import pandas as pd
from fastapi import FastAPI, Query
from typing import Optional

DATA_FILE = "./data/sales_data.csv"

# Try to read CSV file (handle encoding issues like German umlauts)
try:
    df = pd.read_csv(DATA_FILE)
except UnicodeDecodeError:
    # Fallback if the file is encoded in Latin-1
    df = pd.read_csv(DATA_FILE, encoding="latin-1")

# Define column names we expect in the dataset
DATE_COL = "Verkaufsdatum"
CATEGORY_COL = "Kategorie"
SALES_COL = "Verkauf in Stück"  # sometimes mis-decoded as "Verkauf in StÃ¼ck"
STORE_COL = "Filialnummer"
ARTICLE_COL = "Artikelname"     # used for distinct_articles metric
PRED_COL = "Vorhergesagter Verkaufswert"

# Fix column name if special character (ü) got corrupted
if SALES_COL not in df.columns and "Verkauf in StÃ¼ck" in df.columns:
    SALES_COL = "Verkauf in StÃ¼ck"

# Parse the date column to datetime
df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")

# Initialize FastAPI application
app = FastAPI(title="Schwarz IT – API")


@app.get("/health")
def health():
    """Simple health endpoint for monitoring"""
    return {"status": "ok"}


@app.get("/meta")
def meta():
    """Return metadata about the dataset (columns, datatypes, row count)"""
    return {
        "columns": list(df.columns),
        "row_count": len(df),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
        "date_column": DATE_COL,
        "category_column": CATEGORY_COL,
        "sales_column": SALES_COL,
    }


@app.get("/data")
def get_data(
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str]   = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Return raw sales data (optionally filtered by date).
    Limited to first 50 rows for preview purposes.
    """
    data = df.copy()
    if start:
        data = data[data[DATE_COL] >= pd.to_datetime(start, errors="coerce")]
    if end:
        data = data[data[DATE_COL] <= pd.to_datetime(end, errors="coerce")]

    return {
        "count": len(data),
        "preview": data.head(50).to_dict(orient="records"),
    }


@app.get("/metrics")
def metrics(
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str]   = Query(None, description="End date (YYYY-MM-DD)"),
    top: int             = Query(10, ge=0, le=100, description="Top N categories/articles/stores"),
):
    """
    Calculate aggregated sales metrics for the dashboard:
    - Sales by category
    - Sales over time
    - Sales by store
    - Sales by article
    - KPIs (total rows, total sales, avg per day, distinct articles)
    - Predicted sales value over time
    """

    # Apply date filters
    data = df.copy()
    if start:
        data = data[data[DATE_COL] >= pd.to_datetime(start, errors="coerce")]
    if end:
        data = data[data[DATE_COL] <= pd.to_datetime(end, errors="coerce")]

    # Cast sales to numeric
    sales_series = pd.to_numeric(data[SALES_COL], errors="coerce").fillna(0)
    data = data.assign(_sales=sales_series)

    # --- Sales by category ---
    by_cat = (
        data.groupby(CATEGORY_COL)["_sales"]
        .sum()
        .reset_index()
        .sort_values("_sales", ascending=False)
    )
    if top > 0:
        by_cat = by_cat.head(top)

    # --- Sales over time (daily) ---
    by_date = (
        data.groupby(DATE_COL)["_sales"]
        .sum()
        .reset_index()
        .sort_values(DATE_COL)
    )

    # --- Sales by store ---
    by_store = (
        data.groupby(STORE_COL)["_sales"]
        .sum()
        .reset_index()
        .sort_values("_sales", ascending=False)
    )
    if top > 0:
        by_store = by_store.head(top)

    # --- Sales by article ---
    by_article = (
        data.groupby(ARTICLE_COL)["_sales"]
        .sum()
        .reset_index()
        .sort_values("_sales", ascending=False)
    )
    if top > 0:
        by_article = by_article.head(top)

    # --- KPIs ---
    total_sales = float(sales_series.sum())
    days = int(len(by_date))
    avg_sales_per_day = float(total_sales / days) if days > 0 else 0.0
    distinct_articles = (
        data[ARTICLE_COL].nunique()
        if ARTICLE_COL in data.columns
        else None
    )

    # --- Predicted sales over time (daily) ---
    pred_series = pd.to_numeric(data.get(PRED_COL, 0), errors="coerce").fillna(0)
    by_date_pred = (
        data.assign(_pred=pred_series)
            .groupby(DATE_COL)["_pred"]
            .sum()
            .reset_index()
            .sort_values(DATE_COL)
    )

    # Build and return JSON response
    return {
        "total_rows": int(len(data)),
        "total_sales": total_sales,
        "avg_sales_per_day": avg_sales_per_day,
        "distinct_articles": distinct_articles,
        "sales_by_category": [
            {CATEGORY_COL: str(row[CATEGORY_COL]), "sales": float(row["_sales"])}
            for _, row in by_cat.iterrows()
        ],
        "sales_over_time": [
            {DATE_COL: str(row[DATE_COL].date()), "sales": float(row["_sales"])}
            for _, row in by_date.iterrows()
        ],
        "sales_by_store": [
            {STORE_COL: str(row[STORE_COL]), "sales": float(row["_sales"])}
            for _, row in by_store.iterrows()
        ],
        "sales_by_article": [
            {ARTICLE_COL: str(row[ARTICLE_COL]), "sales": float(row["_sales"])}
            for _, row in by_article.iterrows()
        ],
        "predicted_over_time": [
            {DATE_COL: str(row[DATE_COL].date()), "predicted": float(row["_pred"])}
            for _, row in by_date_pred.iterrows()
        ],
    }
