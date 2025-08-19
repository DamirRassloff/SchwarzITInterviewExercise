import pandas as pd
from fastapi import FastAPI, Query
from typing import Optional

DATA_FILE = "./data/sales_data.csv"

# CSV einlesen
df = pd.read_csv(DATA_FILE)

# Datum als datetime
df["Verkaufsdatum"] = pd.to_datetime(df["Verkaufsdatum"], errors="coerce")

app = FastAPI(title="Schwarz IT – API (Step 3)")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/meta")
def meta():
    return {
        "columns": list(df.columns),
        "row_count": len(df),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
    }


@app.get("/data")
def get_data(
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    data = df.copy()

    # Filter nach Start/End falls angegeben
    if start:
        data = data[data["Verkaufsdatum"] >= pd.to_datetime(start, errors="coerce")]
    if end:
        data = data[data["Verkaufsdatum"] <= pd.to_datetime(end, errors="coerce")]

    return {
        "count": len(data),
        "preview": data.head(50).to_dict(orient="records"),
    }
