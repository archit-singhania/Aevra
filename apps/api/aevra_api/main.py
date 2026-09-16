from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from aevra_api.api.routes.auth import router as auth_router
from aevra_api.api.routes.brands import router as brands_router
from aevra_api.api.routes.campaigns import router as campaigns_router
from aevra_api.api.routes.knowledge import router as knowledge_router
from aevra_api.api.routes.models import router as models_router
from aevra_api.api.routes.workspaces import router as workspaces_router
from aevra_api.domain.errors import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    GenerationError,
    NotFoundError,
    ProviderUnavailableError,
    UnsupportedContentError,
)


class HealthResponse(BaseModel):
    status: str
    service: str
    phase: int


app = FastAPI(
    title="Aevra API",
    version="0.1.0",
    description="Deterministic application boundary for Aevra.",
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")
app.include_router(brands_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.include_router(campaigns_router, prefix="/api/v1")


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


@app.exception_handler(AuthenticationError)
def handle_authentication_error(_request: Request, exc: AuthenticationError) -> JSONResponse:
    response = error_response("authentication_failed", str(exc), status.HTTP_401_UNAUTHORIZED)
    response.headers["WWW-Authenticate"] = "Bearer"
    return response


@app.exception_handler(ForbiddenError)
def handle_forbidden_error(_request: Request, exc: ForbiddenError) -> JSONResponse:
    return error_response("forbidden", str(exc), status.HTTP_403_FORBIDDEN)


@app.exception_handler(NotFoundError)
def handle_not_found_error(_request: Request, exc: NotFoundError) -> JSONResponse:
    return error_response("not_found", str(exc), status.HTTP_404_NOT_FOUND)


@app.exception_handler(ConflictError)
def handle_conflict_error(_request: Request, exc: ConflictError) -> JSONResponse:
    return error_response("conflict", str(exc), status.HTTP_409_CONFLICT)


@app.exception_handler(UnsupportedContentError)
def handle_unsupported_content_error(
    _request: Request, exc: UnsupportedContentError
) -> JSONResponse:
    return error_response("unsupported_content", str(exc), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


@app.exception_handler(ProviderUnavailableError)
def handle_provider_unavailable_error(
    _request: Request, exc: ProviderUnavailableError
) -> JSONResponse:
    return error_response("provider_unavailable", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)


@app.exception_handler(GenerationError)
def handle_generation_error(_request: Request, exc: GenerationError) -> JSONResponse:
    return error_response("generation_failed", str(exc), status.HTTP_502_BAD_GATEWAY)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="aevra-api", phase=6)
