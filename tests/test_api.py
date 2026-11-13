import pytest
from fastapi.testclient import TestClient

from src.HealthService import HealthService
from src.JobRepository import InMemoryJobRepository, SqliteJobRepository
from src.TrackerService import TrackerService
from src.app import create_app


@pytest.fixture
def client():
    health_repo = SqliteJobRepository(":memory:")
    app = create_app(
        tracker=TrackerService(job_repository=InMemoryJobRepository()),
        health=HealthService(job_repository=health_repo),
    )
    try:
        yield TestClient(app)
    finally:
        health_repo.close()


def test_post_job_then_get_list_and_job(client):
    payload = {
        "title": "Software Engineer",
        "url": "https://example.com/jobs/1",
        "org_id": "org-1",
        "seniority": "entry",
        "workmode": "remote",
        "id": "job-1",
    }
    created = client.post("/jobs", json=payload)
    assert created.status_code == 200
    assert created.json() == "job-1"

    listed = client.get("/jobs")
    assert listed.status_code == 200
    jobs = listed.json()
    assert len(jobs) == 1
    job = jobs[0]
    assert job["id"] == "job-1"
    assert job["title"] == "Software Engineer"
    assert job["url"] == "https://example.com/jobs/1"
    assert job["org_id"] == "org-1"
    assert job["seniority"] == "entry"
    assert job["workmode"] == "remote"

    fetched = client.get("/jobs/job-1")
    assert fetched.status_code == 200
    assert fetched.json() == job


def test_get_missing_job_returns_null(client):
    response = client.get("/jobs/missing")
    assert response.status_code == 200
    assert response.json() is None


def test_health_returns_healthy_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "Service is healthy",
    }
