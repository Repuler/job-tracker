# methods
# serviceHealth
# databaseHealth
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from src.JobRepository import JobRepository
from src.ApplicationRepository import ApplicationRepository


class HealthService:
    def __init__(self, router: APIRouter, job_repository: JobRepository, application_repository: ApplicationRepository):
        self.job_repository = job_repository
        # TODO: add application repository health check
        self.application_repository = application_repository
        self.router = router
        self.router.add_api_route("/health", self.serviceHealth, methods=["GET"])
        self.router.add_api_route("/health/database", self.databaseHealth, methods=["GET"])

    def serviceHealth(self):
        return {"status": "healthy", "message": "Service is healthy"}

    def databaseHealth(self):
        try:
            self.job_repository.check_connection()
            return {"status": "healthy", "message": "Database is healthy"}
        except Exception as e:
            raise HTTPException(status_code=500, detail={"status": "unhealthy", "message": "Database is not healthy", "error": str(e)})
