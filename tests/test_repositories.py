from copy import deepcopy
from datetime import datetime
import pytest
from src.Models import Job, Seniority, WorkMode
from src.JobRepository import (InMemoryJobRepository, SqliteJobRepository,
                               JobAlreadyExists, JobNotFoundError)

# mock job
mock_job = Job(
    "Software Engineer",
    "temp_url.com/job",
    'org-1',
    Seniority.ENTRY,
    WorkMode.REMOTE,
    "job-1",
    90000,
    120000,
    datetime(2009, 10, 5, 18, 00),
    "LinkedIn",
    "Golden, CO",
    "Coding with Python"
)

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
        return InMemoryJobRepository()
    return SqliteJobRepository(":memory:")

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
    with pytest.raises(JobAlreadyExists):
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

    # List with limit=2, offset=0: first two jobs
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
        repo.update(mock_job)

# delete
def test_delete_removes_job(repo):
    job = make_job()
    repo.add(mock_job)
    job = repo.get(job.id)
    assert job is not None
    repo.delete(job.id)
    job = repo.get(job.id)
    assert job is None
def test_delete_missing_raises(repo):
    with pytest.raises(JobNotFoundError):
        repo.delete(make_job().id)
