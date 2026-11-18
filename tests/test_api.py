import pytest
from fastapi.testclient import TestClient

from src.JobRepository import InMemoryJobRepository
from src.app import create_app
from src.Models import Status


@pytest.fixture
def client():
    return TestClient(create_app())


def _iter_routes(routes):
    for route in routes:
        included = getattr(route, "original_router", None)
        if included is not None:
            yield from _iter_routes(included.routes)
            continue
        yield route


def _repository_owners(app):
    owners = []
    seen = set()
    for route in _iter_routes(app.routes):
        endpoint = getattr(route, "endpoint", None)
        owner = getattr(endpoint, "__self__", None)
        if owner is None or not hasattr(owner, "job_repository"):
            continue
        if id(owner) in seen:
            continue
        seen.add(id(owner))
        owners.append(owner)
    return owners


def test_post_empty_job_returns_422(client):
    response = client.post("/jobs", json={})
    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "title: Field required; url: Field required; org_id: Field required; "
            "seniority: Field required; workmode: Field required"
        )
    }


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
    created_body = created.json()
    assert created_body["job_id"]
    assert isinstance(created_body["app_id"], str)
    assert created_body["app_id"]

    listed = client.get("/jobs")
    assert listed.status_code == 200
    jobs = listed.json()
    assert len(jobs) == 1
    job = jobs[0]
    assert job["id"] == created_body["job_id"]
    assert job["title"] == "Software Engineer"
    assert job["url"] == "https://example.com/jobs/1"
    assert job["org_id"] == "org-1"
    assert job["seniority"] == "entry"
    assert job["workmode"] == "remote"

    fetched = client.get(f"/jobs/{created_body['job_id']}")
    assert fetched.status_code == 200
    assert fetched.json() == job


def test_get_missing_job_returns_null(client):
    missing_job_id = "missing"
    response = client.get(f"/jobs/{missing_job_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": f"Job {missing_job_id} not found"}


def test_health_returns_healthy_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "Service is healthy",
    }


def test_create_app_shares_the_repository_and_does_not_create_a_database_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    default_app = create_app()
    default_owners = _repository_owners(default_app)
    assert len(default_owners) == 2
    assert default_owners[0].job_repository is default_owners[1].job_repository
    assert not (tmp_path / "jobs.db").exists()

    repo = InMemoryJobRepository()
    app = create_app(job_repository=repo)
    owners = _repository_owners(app)
    assert len(owners) == 2
    assert all(owner.job_repository is repo for owner in owners)

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={
            "id": "job-1",
            "title": "Software Engineer",
            "url": "https://example.com/jobs/1",
            "org_id": "org-1",
            "seniority": "entry",
            "workmode": "remote",
        },
    )
    assert created.status_code == 200
    created_body = created.json()
    assert created_body["job_id"]
    assert repo.get(created_body["job_id"]).title == "Software Engineer"

    health = next(owner for owner in owners if hasattr(owner, "databaseHealth"))
    assert health.databaseHealth() == {
        "status": "healthy",
        "message": "Database is healthy",
    }
    assert not (tmp_path / "jobs.db").exists()


def test_post_job_creates_saved_application(client):
    payload = {
        "title": "Software Engineer",
        "url": "https://example.com/jobs/1",
        "org_id": "org-1",
        "seniority": "entry",
        "workmode": "remote",
    }
    created = client.post("/jobs", json=payload)
    assert created.status_code == 200

    created_body = created.json()
    job_id = created_body["job_id"]
    app_id = created_body["app_id"]
    assert isinstance(job_id, str) and job_id
    assert isinstance(app_id, str) and app_id

    application = client.get(f"/applications/{app_id}")
    assert application.status_code == 200
    body = application.json()
    assert body["id"] == app_id
    assert body["job_id"] == job_id
    assert body["resume_path"] is None
    assert body["status"] == Status.SAVED.value
