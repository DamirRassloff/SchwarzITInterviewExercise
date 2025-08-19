import pandas as pd
from fastapi import FastAPI

DATA_FILE = "./data/sales_data.csv"

# Dataset laden
df = pd.read_csv(DATA_FILE)

app = FastAPI(title="Schwarz IT – API (Step 2)")

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
def get_data():
    return {
        "count": len(df),
        "preview": df.head(50).to_dict(orient="records"),
    }