from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.risk import router as risk_router
from backend.api.reports import router as reports_router
from backend.api.transactions import router as transactions_router
from backend.api.admin import router as admin_router
from backend.api.alerts import router as alerts_router
from backend.api.cases import router as cases_router

app = FastAPI(
    title="Adera API",
    description="Explainable Fraud Intelligence & Investigation Platform API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(risk_router)
app.include_router(reports_router)
app.include_router(transactions_router)
app.include_router(admin_router)
app.include_router(alerts_router)
app.include_router(cases_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
