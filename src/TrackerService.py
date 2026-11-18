# methods
# add_job
# find_jobs
# apply
# advance
# pipeline?
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from src.JobRepository import InMemoryJobRepository, JobRepository, JobAlreadyExistsError, JobNotFoundError
from src.Models import Job, Application, Resume, Status
from src.ApplicationRepository import InMemoryApplicationRepository, ApplicationRepository, AppAlreadyExistsError, AppNotFoundError


class TrackerService:
    def __init__(self, router: APIRouter, job_repository: JobRepository | None = None, application_repository: ApplicationRepository | None = None):
        self.job_repository = job_repository or InMemoryJobRepository()
        self.application_repository = application_repository or InMemoryApplicationRepository()
        self.router = router
        # Jobs Routes
        self.router.add_api_route("/jobs", self.add_job, methods=["POST"])
        self.router.add_api_route("/jobs", self.get_jobs_list, methods=["GET"])
        self.router.add_api_route("/jobs/{job_id}", self.get_job, methods=["GET"])
        # Applications Routes
        self.router.add_api_route("/applications", self.get_applications_list, methods=["GET"])
        self.router.add_api_route("/applications/{app_id}", self.get_application, methods=["GET"])
        self.router.add_api_route("/applications/{app_id}/apply", self.apply_to_job, methods=["POST"])
        self.router.add_api_route("/applications/{app_id}/advance", self.advance_application, methods=["POST"])

    def add_job(self, job: Job):
        try: 
            job_id = self.job_repository.add(job)
            app_id = self.application_repository.add(Application(job_id=job_id))
            return {"job_id": job_id, "app_id": app_id}
        except Exception as e:
            if isinstance(e, JobAlreadyExistsError):
                raise HTTPException(status_code=409, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    def get_jobs_list(self):
        return self.job_repository.list()

    def get_job(self, job_id: str):
        try:
            return self.job_repository.get(job_id)
        except Exception as e:
            if isinstance(e, JobNotFoundError):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    def get_applications_list(self):
        return self.application_repository.list()

    def get_application(self, app_id: str):
        try:
            return self.application_repository.get(app_id)
        except Exception as e:
            if isinstance(e, AppNotFoundError):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    def apply_to_job(self, app_id, resume: Resume):
        try:
            application = self.application_repository.get(app_id)
            if application is None:
                raise AppNotFoundError(app_id)
            application.resume = resume
            application.status = Status.APPLIED
            return self.application_repository.update(application)
        except Exception as e:
            if isinstance(e, AppNotFoundError):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    def advance_application(self, app_id: str, status: Status):
        try:
            application = self.application_repository.get(app_id)
            if application is None:
                raise AppNotFoundError(app_id)
            application.status = status
            return self.application_repository.update(application)
        except Exception as e:
            if isinstance(e, AppNotFoundError):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))
