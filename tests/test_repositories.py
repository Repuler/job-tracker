from datetime import datetime
import pytest
from src.Models import Application, Job, Resume, Seniority, Status, WorkMode
from src.JobRepository import (InMemoryJobRepository, SqliteJobRepository,
                               JobAlreadyExistsError, JobNotFoundError)
from src.ApplicationRepository import (InMemoryApplicationRepository,
                                       SqliteApplicationRepository,
                                       AppAlreadyExistsError, AppNotFoundError)

def make_job(**overrides) -> Job:
    fields = dict(
        title="Software Engineer",
        url="temp_url.com/job",
        org_id="org-1",
        seniority=Seniority.ENTRY,
        workmode=WorkMode.REMOTE,
        id="job-1",
        salary_min=90000,
        salary_max=120000,
        posted_at=datetime(2009, 10, 5, 18, 0),
        source="LinkedIn",
        location="Golden, CO",
        description="Coding with Python",
    )
    fields.update(overrides)
    return Job(**fields)

@pytest.fixture(params=["memory", "sqlite"])
def repo(request):
    if request.param == "memory":
        yield InMemoryJobRepository()
        return
    sqlite_repo = SqliteJobRepository(":memory:")
    try:
        yield sqlite_repo
    finally:
        sqlite_repo.close()

# add / get
def test_add_then_get_returns_equal_job(repo):
    job = make_job()
    job_id = repo.add(job)
    assert job_id is not None
    get_job = repo.get(job_id)
    assert get_job is not None
    job1 = job.get_details()
    job2 = get_job.get_details()
    for i in range(len(job1)):
        assert job2[i] == job1[i]
def test_get_missing_returns_none(repo):
    job_id = 'job-2'
    job = repo.get(job_id)
    assert job is None
def test_add_duplicate_raises(repo):
    job = make_job()
    assert repo.add(job) is not None
    with pytest.raises(JobAlreadyExistsError):
        repo.add(job)

# list
def test_list_empty(repo):
    jobs = repo.list()
    assert len(jobs) == 0
def test_list_respects_limit_and_offset(repo):
    # Create three mock jobs with unique IDs
    job1 = make_job()
    job2 = make_job(id="job-xyz-2", title="Backend Developer")
    job3 = make_job(id="job-xyz-3", title="Frontend Developer")

    repo.add(job1)
    repo.add(job2)
    repo.add(job3)

    # List with limit=2, offset=1: last two jobs
    jobs = repo.list(limit=2, offset=1)
    assert len(jobs) == 2
    # Confirm which jobs are returned
    listed_ids = {job.id for job in jobs}
    expected_ids = {job2.id, job3.id}
    assert listed_ids.issubset(expected_ids)
    assert len(listed_ids) == 2

# update
def test_update_changes_fields(repo):
    job = make_job()
    repo.add(job)
    job_update = make_job(title="Full-Stack Engineer")
    repo.update(job_update)
    get_job = repo.get(job.id)
    assert get_job.title == 'Full-Stack Engineer'
    assert get_job.title != job.title
def test_update_missing_raises(repo): 
    with pytest.raises(JobNotFoundError):
        repo.update(make_job())

# delete
def test_delete_removes_job(repo):
    job = make_job()
    repo.add(job)
    job = repo.get(job.id)
    assert job is not None
    repo.delete(job.id)
    job = repo.get(job.id)
    assert job is None
def test_delete_missing_raises(repo):
    with pytest.raises(JobNotFoundError):
        repo.delete(make_job().id)


def make_resume(**overrides) -> Resume:
    fields = dict(
        title="acme",
        file_path="resumes/acme.pdf",
        file_link="https://files.example/acme.pdf",
        created_at=datetime(2026, 1, 2, 3, 4, 5),
        updated_at=datetime(2026, 1, 2, 3, 4, 6),
    )
    fields.update(overrides)
    return Resume(**fields)


def make_app(**overrides) -> Application:
    fields = dict(
        job_id="job-1",
        resume=make_resume(),
        id="app-1",
        applied_at=datetime(2026, 2, 1, 12, 0),
        updated_at=datetime(2026, 2, 2, 12, 0),
        created_at=datetime(2026, 1, 15, 9, 0),
        status=Status.APPLIED,
    )
    fields.update(overrides)
    return Application(**fields)


@pytest.fixture(params=["memory", "sqlite"])
def app_repo(request):
    if request.param == "memory":
        yield InMemoryApplicationRepository()
        return
    sqlite_repo = SqliteApplicationRepository(":memory:")
    try:
        yield sqlite_repo
    finally:
        sqlite_repo.close()


def test_add_then_get_returns_equal_app(app_repo):
    app = make_app()
    app_id = app_repo.add(app)
    assert app_id is not None
    assert app_id == app.id
    stored = app_repo.get(app_id)
    assert stored == app


def test_get_missing_app_returns_none(app_repo):
    assert app_repo.get("app-missing") is None


def test_add_duplicate_app_raises(app_repo):
    app = make_app()
    assert app_repo.add(app) is not None
    with pytest.raises(AppAlreadyExistsError):
        app_repo.add(app)


def test_list_apps_empty(app_repo):
    assert app_repo.list() == []


def test_list_apps_respects_limit_and_offset(app_repo):
    app1 = make_app(id="app-1", created_at=datetime(2026, 1, 1))
    app2 = make_app(id="app-2", job_id="job-2", created_at=datetime(2026, 1, 2))
    app3 = make_app(id="app-3", job_id="job-3", created_at=datetime(2026, 1, 3))

    app_repo.add(app1)
    app_repo.add(app2)
    app_repo.add(app3)

    apps = app_repo.list(limit=2, offset=1)
    assert [app.id for app in apps] == [app2.id, app3.id]


def test_update_app_changes_fields(app_repo):
    app = make_app()
    app_repo.add(app)
    updated = make_app(
        id=app.id,
        job_id="job-2",
        status=Status.INTERVIEWING,
        resume=make_resume(title="tailored"),
    )
    app_repo.update(updated)
    stored = app_repo.get(app.id)
    assert stored == updated


def test_update_missing_app_raises(app_repo):
    with pytest.raises(AppNotFoundError):
        app_repo.update(make_app())


def test_delete_removes_app(app_repo):
    app = make_app()
    app_repo.add(app)
    assert app_repo.get(app.id) is not None
    app_repo.delete(app.id)
    assert app_repo.get(app.id) is None


def test_delete_missing_app_raises(app_repo):
    with pytest.raises(AppNotFoundError):
        app_repo.delete(make_app().id)
