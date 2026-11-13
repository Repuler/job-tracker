# methods
# serviceHealth
# databaseHealth
from fastapi import APIRouter

from src.JobRepository import JobRepository


class HealthService:
    def __init__(self, job_repository: JobRepository):
        self.job_repository = job_repository
        self.router = APIRouter()
        self.router.add_api_route("/health", self.serviceHealth, methods=["GET"])

    def serviceHealth(self):
        return {"status": "healthy", "message": "Service is healthy"}

    def databaseHealth(self):
        try:
            self.job_repository.check_connection()
            return {"status": "healthy", "message": "Database is healthy"}
        except Exception as e:
            return {"status": "unhealthy", "message": "Database is not healthy", "error": str(e)}
