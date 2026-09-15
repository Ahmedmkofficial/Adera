from fastapi import FastAPI

app = FastAPI(title="Adera API")


@app.get("/health")
def health_check():
    return {"status": "ok"}