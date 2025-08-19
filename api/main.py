from fastapi import FastAPI

app = FastAPI(title="Schwarz IT – API")

@app.get("/health")
def health():
    return {"status": "ok"}