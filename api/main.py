import pandas as pd
from fastapi import FastAPI, Query
from typing import Optional

DATA_FILE = "./data/sales_data.csv"

# CSV einlesen (robust bei Umlauten)
try:
    df = pd.read_csv(DATA_FILE)
except UnicodeDecodeError:
    # Falls Datei Latin-1 ist
    df = pd.read_csv(DATA_FILE, encoding="latin-1")

# Spaltennamen, die wir erwarten
DATE_COL = "Verkaufsdatum"
CATEGORY_COL = "Kategorie"
SALES_COL = "Verkauf in Stück"  # falls CSV falsch decodiert ist: "Verkauf in StÃ¼ck"

# Minimaler Fix, falls das "ü" zerschossen ist
if SALES_COL not in df.columns and "Verkauf in StÃ¼ck" in df.columns:
    SALES_COL = "Verkauf in StÃ¼ck"

# Datum als datetime
df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")

app = FastAPI(title="Schwarz IT – API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/meta")
def meta():
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
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
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
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    top: int = Query(10, ge=1, le=100, description="Top N Kategorien"),
):
    data = df.copy()
    if start:
        data = data[data[DATE_COL] >= pd.to_datetime(start, errors="coerce")]
    if end:
        data = data[data[DATE_COL] <= pd.to_datetime(end, errors="coerce")]

    # Verkäufe casten
    sales_series = pd.to_numeric(data[SALES_COL], errors="coerce").fillna(0)
    data = data.assign(_sales=sales_series)

    # Verkäufe pro Kategorie
    by_cat = (
        data.groupby(CATEGORY_COL)["_sales"]
        .sum()
        .reset_index()
        .sort_values("_sales", ascending=False)
        .head(top)
    )

    # Verkäufe über Zeit (pro Tag)
    by_date = (
        data.groupby(DATE_COL)["_sales"]
        .sum()
        .reset_index()
        .sort_values(DATE_COL)
    )

    return {
        "total_rows": int(len(data)),
        "total_sales": float(sales_series.sum()),
        "sales_by_category": [
            {CATEGORY_COL: str(row[CATEGORY_COL]), "sales": float(row["_sales"])}
            for _, row in by_cat.iterrows()
        ],
        "sales_over_time": [
            {DATE_COL: str(row[DATE_COL].date()), "sales": float(row["_sales"])}
            for _, row in by_date.iterrows()
        ],
    }
