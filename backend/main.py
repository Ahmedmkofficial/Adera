from fastapi import FastAPI

from backend.api.risk import router as risk_router

app = FastAPI(title="Adera API")

app.include_router(risk_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}