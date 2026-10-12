"""CDC observability API; read-only and localhost-only until auth is added."""
import os
import requests
from fastapi import FastAPI, HTTPException
from cdc.processing import metrics
from cdc.ai import explain

app = FastAPI(title="CDC Real-Time Data Platform", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/metrics")
def get_metrics():
    return metrics(os.getenv("CDC_STORE", "artifacts/cdc.db"))


@app.post("/api/ai/investigate")
def investigate():
    try:
        return explain(get_metrics())
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise HTTPException(502, "AI model unavailable") from exc
