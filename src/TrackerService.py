# methods
# add_job
# find_jobs
# apply
# advance
# pipeline?
from fastapi import APIRouter

from src.JobRepository import InMemoryJobRepository, JobRepository
from src.Models import Job


class TrackerService:
    def __init__(self, job_repository: JobRepository | None = None):
        self.jobs = []
        self.applications = []
        self.job_repository = job_repository or InMemoryJobRepository()
        self.router = APIRouter()
        self.router.add_api_route("/jobs", self.add_job, methods=["POST"])
        self.router.add_api_route("/jobs", self.get_jobs_list, methods=["GET"])
        self.router.add_api_route("/jobs/{job_id}", self.get_job, methods=["GET"])

    def add_job(self, job: Job):
        return self.job_repository.add(job)

    def get_jobs_list(self):
        return self.job_repository.list()

    def get_job(self, job_id: str):
        return self.job_repository.get(job_id)
