# abstract class for managing job related requests

from abc import ABC, abstractmethod
import sqlite3
from datetime import datetime

from typing import Optional
from .Models import Job, Seniority, WorkMode

class JobAlreadyExists(Exception):
    pass

class JobNotFoundError(Exception):
    pass

class JobRepository(ABC):
    @abstractmethod
    def add(self, job: Job) -> None:
        ...

    @abstractmethod
    def get(self, job_id: str) -> Optional[Job]:
        ...

    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> list[Job]:
        ...

    @abstractmethod
    def update(self, job: Job) -> None:
        ...

    @abstractmethod
    def delete(self, job_id: str) -> None:
        ...

class SqliteJobRepository(JobRepository):
    def __init__(self, db_path: str = "jobs.db") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row   # rows act like dicts
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                org_id TEXT NOT NULL,
                seniority TEXT,
                work_mode TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                posted_at TEXT,
                source TEXT,
                location TEXT,
                description TEXT
            )
        """)
        self._conn.commit()

    # --- conversion helpers: the only place that knows the row format ---
    def _to_row(self, job: Job) -> tuple:
        # enums -> .value, datetimes -> .isoformat(), None stays None
        return (
            job.id,
            job.title,
            job.url,
            job.org_id,
            job.seniority.value,
            job.workmode.value,
            job.salary_min,
            job.salary_max,
            job.posted_at.isoformat() if job.posted_at is not None else None,
            job.source,
            job.location,
            job.description,
        )

    def _from_row(self, row: sqlite3.Row) -> Job:
        # reverse it: Seniority(row["seniority"]), datetime.fromisoformat(...)
        posted_at = row["posted_at"]
        return Job(
            id=row["id"],
            title=row["title"],
            url=row["url"],
            org_id=row["org_id"],
            seniority=Seniority(row["seniority"]),
            workmode=WorkMode(row["work_mode"]),
            salary_min=row["salary_min"],
            salary_max=row["salary_max"],
            posted_at=datetime.fromisoformat(posted_at) if posted_at is not None else None,
            source=row["source"],
            location=row["location"],
            description=row["description"],
        )

    def add(self, job: Job) -> str:
        # INSERT INTO jobs VALUES (?, ?, ...) with self._to_row(job), then commit
        try:
            self._conn.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                self._to_row(job),
            )
        except sqlite3.IntegrityError as exc:
            raise JobAlreadyExists from exc
        self._conn.commit()
        return job.id

    def get(self, job_id: str) -> Optional[Job]:
        # SELECT * FROM jobs WHERE id = ?  -> _from_row or None
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list(self, limit: int = 100, offset: int = 0) -> list[Job]:
        # SELECT * FROM jobs  -> [_from_row(r) for r in rows]
        rows = self._conn.execute(
            "SELECT * FROM jobs LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def update(self, job: Job) -> None:
        # UPDATE ... WHERE id = ?; if cursor.rowcount == 0 raise JobNotFoundError
        values = self._to_row(job)
        cursor = self._conn.execute(
            """
            UPDATE jobs
            SET title = ?, url = ?, org_id = ?, seniority = ?, work_mode = ?,
                salary_min = ?, salary_max = ?, posted_at = ?, source = ?,
                location = ?, description = ?
            WHERE id = ?
            """,
            (*values[1:], values[0]),
        )
        if cursor.rowcount == 0:
            raise JobNotFoundError
        self._conn.commit()

    def delete(self, job_id: str) -> None:
        # DELETE ... WHERE id = ?; same rowcount check
        cursor = self._conn.execute(
            "DELETE FROM jobs WHERE id = ?",
            (job_id,),
        )
        if cursor.rowcount == 0:
            raise JobNotFoundError
        self._conn.commit()

class InMemoryJobRepository(JobRepository):
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
    def add(self, job: Job) -> str:
        # store under job.id; raise ValueError if the id already exists
        if job.id in self._jobs:
            raise JobAlreadyExists
        self._jobs[job.id] = job
        return job.id

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def list(self, limit: int = 100, offset: int = 0) -> list[Job]:
        return list[Job](self._jobs.values())[offset:offset + limit]

    def update(self, job: Job) -> None:
        # raise JobNotFoundError if missing, else replace
        if not job.id in self._jobs:
            raise JobNotFoundError
        self._jobs[job.id] = job
        
    def delete(self, job_id: str) -> None:
        # raise JobNotFoundError if missing, else remove
        if not job_id in self._jobs:
            raise JobNotFoundError
        self._jobs.pop(job_id)
        