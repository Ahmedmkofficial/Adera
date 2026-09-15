from fastapi import FastAPI

from backend.api.risk import router as risk_router
from backend.api.reports import router as reports_router
from backend.api.transactions import router as transactions_router

app = FastAPI(title="Adera API")

app.include_router(risk_router)
app.include_router(reports_router)
app.include_router(transactions_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}