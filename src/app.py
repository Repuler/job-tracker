from fastapi import FastAPI

from src.HealthService import HealthService
from src.JobRepository import InMemoryJobRepository, JobRepository
from src.TrackerService import TrackerService


def create_app(
    tracker: TrackerService | None = None,
    health: HealthService | None = None,
    job_repository: JobRepository | None = None,
) -> FastAPI:
    """Build the API without constructing an app at import time.

    The tracker and the health check share one repository, built here
    unless the caller supplies the services or the repository.
    """
    if tracker is None or health is None:
        if job_repository is None:
            if tracker is not None:
                job_repository = tracker.job_repository
            elif health is not None:
                job_repository = health.job_repository
            else:
                job_repository = InMemoryJobRepository()
        if tracker is None:
            tracker = TrackerService(job_repository=job_repository)
        if health is None:
            health = HealthService(job_repository=job_repository)
    app = FastAPI()
    app.include_router(tracker.router)
    app.include_router(health.router)
    return app
