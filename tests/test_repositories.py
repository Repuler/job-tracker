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

mock_job2 = Job(
    "Full-Stack Engineer",
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

@pytest.fixture(params=["memory", "sqlite"])
def repo(request):
    if request.param == "memory":
        return InMemoryJobRepository()
    return SqliteJobRepository(":memory:")

# add / get
def test_add_then_get_returns_equal_job(repo):
    job_id = repo.add(mock_job)
    assert job_id is not None
    get_job = repo.get(job_id)
    assert get_job is not None
    job1 = mock_job.get_details()
    job2 = get_job.get_details()
    for i in range(len(job1)):
        assert job2[i] == job1[i]
def test_get_missing_returns_none(repo):
    job_id = 'job-2'
    job = repo.get(job_id)
    assert job is None
def test_add_duplicate_raises(repo):
    assert repo.add(mock_job) is not None
    with pytest.raises(JobAlreadyExists):
        repo.add(mock_job)

# list
def test_list_empty(repo):
    list = repo.list()
    assert len(list) == 0
def test_list_respects_limit_and_offset(repo):
    repo.add(mock_job)
    list = repo.list()
    assert len(list) == 1

# update
def test_update_changes_fields(repo):
    repo.add(mock_job)
    repo.update(mock_job2)
    job = repo.get(mock_job.id)
    assert job.title == 'Full-Stack Engineer'
    assert job.title != mock_job.title
def test_update_missing_raises(repo): 
    with pytest.raises(JobNotFoundError):
        repo.update(mock_job2)

# delete
def test_delete_removes_job(repo):
    repo.add(mock_job)
    job = repo.get(mock_job.id)
    assert job is not None
    repo.delete(job.id)
    job = repo.get(mock_job.id)
    assert job is None
def test_delete_missing_raises(repo):
    with pytest.raises(JobNotFoundError):
        repo.delete(mock_job2.id)
