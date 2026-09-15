from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    phase: int


app = FastAPI(
    title="Aevra API",
    version="0.1.0",
    description="Deterministic application boundary for Aevra.",
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="aevra-api", phase=0)

