from fastapi import FastAPI, APIRouter

from src.HealthService import HealthService
from src.JobRepository import InMemoryJobRepository, JobRepository
from src.ApplicationRepository import InMemoryApplicationRepository, ApplicationRepository
from src.TrackerService import TrackerService


def create_app(
    tracker: TrackerService | None = None,
    health: HealthService | None = None,
    job_repository: JobRepository | None = None,
    application_repository: ApplicationRepository | None = None,
) -> FastAPI:
    """Build the API without constructing an app at import time.

    The tracker and the health check share one repository, built here
    unless the caller supplies the services or the repository.
    """
    router = APIRouter()
    if tracker is None or health is None:
        if job_repository is None:
            job_repository = InMemoryJobRepository()
        if application_repository is None:
            application_repository = InMemoryApplicationRepository()
        if tracker is None:
            tracker = TrackerService(router=router, job_repository=job_repository, application_repository=application_repository)
        if health is None:
            health = HealthService(router=router, job_repository=job_repository, application_repository=application_repository)
    app = FastAPI()
    app.include_router(tracker.router)
    app.include_router(health.router)
    return app
