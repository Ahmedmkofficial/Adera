from fastapi import FastAPI

from backend.api.admin import router as admin_router
from backend.api.alerts import router as alerts_router
from backend.api.auth import router as auth_router
from backend.api.cases import router as cases_router
from backend.api.recipients import router as recipients_router
from backend.api.reports import router as reports_router
from backend.api.risk import router as risk_router
from backend.api.transactions import router as transactions_router

app = FastAPI(title="Adera API")

app.include_router(auth_router)
app.include_router(risk_router)
app.include_router(reports_router)
app.include_router(transactions_router)
app.include_router(recipients_router)
app.include_router(alerts_router)
app.include_router(cases_router)
app.include_router(admin_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}