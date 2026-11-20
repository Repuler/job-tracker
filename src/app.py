from fastapi import FastAPI, APIRouter, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.HealthService import HealthService
from src.JobRepository import InMemoryJobRepository, JobRepository
from src.ApplicationRepository import InMemoryApplicationRepository, ApplicationRepository
from src.TrackerService import TrackerService


def _field(loc: tuple) -> str:
    parts = [str(part) for part in loc if part not in {"body", "query", "path"}]
    return ".".join(parts) or "request"


def create_app(
    job_repository: JobRepository | None = None,
    application_repository: ApplicationRepository | None = None,
) -> FastAPI:
    """Build the API without constructing an app at import time.

    The tracker and the health check share one repository, built here
    unless the caller supplies the services or the repository.
    """
    router = APIRouter()
    if job_repository is None:
        job_repository = InMemoryJobRepository()
    if application_repository is None:
        application_repository = InMemoryApplicationRepository()
    tracker = TrackerService(router=router, job_repository=job_repository, application_repository=application_repository)
    health = HealthService(router=router, job_repository=job_repository, application_repository=application_repository)
    app = FastAPI()

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        detail = "; ".join(
            f"{_field(err['loc'])}: {err['msg']}" for err in exc.errors()
        )
        return JSONResponse(status_code=422, content={"detail": detail})

    @app.exception_handler(500)
    async def server_error_exception_handler(request: Request, exc: Exception):
        detail = "Internal server error"
        return JSONResponse(status_code=500, content={"detail": detail})

    app.include_router(tracker.router)
    app.include_router(health.router)
    return app
