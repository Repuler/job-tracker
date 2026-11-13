from fastapi import FastAPI

from src.HealthService import HealthService
from src.TrackerService import TrackerService


def create_app(tracker=None, health=None) -> FastAPI:
    """Build the API without constructing an app at import time."""
    app = FastAPI()
    if tracker is None:
        tracker = TrackerService()
    if health is None:
        health = HealthService()
    app.include_router(tracker.router)
    app.include_router(health.router)
    return app
