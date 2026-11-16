# abstract class for managing application related requests

from abc import ABC, abstractmethod
import sqlite3
from datetime import datetime

from typing import Optional
from .Models import Application, Resume, Status

class AppAlreadyExistsError(Exception):
    def __init__(self, app_id):
        self.app_id = app_id
        super().__init__(f"Application {app_id} already exists")

class AppNotFoundError(Exception):
    def __init__(self, app_id):
        self.app_id = app_id
        super().__init__(f"Application {app_id} not found")

class ApplicationRepository(ABC):
    @abstractmethod
    def add(self, app: Application) -> str:
        ...

    @abstractmethod
    def get(self, app_id: str) -> Optional[Application]:
        ...

    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> list[Application]:
        ...

    @abstractmethod
    def update(self, app: Application) -> None:
        ...

    @abstractmethod
    def delete(self, app_id: str) -> None:
        ...

class SqliteApplicationRepository(ApplicationRepository):
    def __init__(self, db_path: str = "applications.db") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row   # rows act like dicts
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                resume_title TEXT NOT NULL,
                resume_file_path TEXT NOT NULL,
                resume_file_link TEXT,
                resume_created_at TEXT NOT NULL,
                resume_updated_at TEXT NOT NULL,
                applied_at TEXT,
                updated_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # --- conversion helpers: the only place that knows the row format ---
    def _to_row(self, app: Application) -> tuple:
        # enums -> .value, datetimes -> .isoformat(), None stays None
        return (
            app.id,
            app.job_id,
            app.resume.title,
            app.resume.file_path,
            app.resume.file_link,
            app.resume.created_at.isoformat(),
            app.resume.updated_at.isoformat(),
            app.applied_at.isoformat() if app.applied_at is not None else None,
            app.updated_at.isoformat(),
            app.created_at.isoformat(),
            app.status.value,
        )

    def _from_row(self, row: sqlite3.Row) -> Application:
        # reverse it: Status(row["status"]), datetime.fromisoformat(...)
        applied_at = row["applied_at"]
        return Application(
            id=row["id"],
            job_id=row["job_id"],
            resume=Resume(
                title=row["resume_title"],
                file_path=row["resume_file_path"],
                file_link=row["resume_file_link"],
                created_at=datetime.fromisoformat(row["resume_created_at"]),
                updated_at=datetime.fromisoformat(row["resume_updated_at"]),
            ),
            applied_at=datetime.fromisoformat(applied_at) if applied_at is not None else None,
            updated_at=datetime.fromisoformat(row["updated_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            status=Status(row["status"]),
        )

    def add(self, app: Application) -> str:
        # INSERT INTO applications VALUES (?, ?, ...) with self._to_row(app), then commit
        try:
            self._conn.execute(
                "INSERT INTO applications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                self._to_row(app),
            )
        except sqlite3.IntegrityError as exc:
            raise AppAlreadyExistsError(app.id) from exc
        self._conn.commit()
        return app.id

    def get(self, app_id: str) -> Optional[Application]:
        # SELECT * FROM applications WHERE id = ?  -> _from_row or None
        row = self._conn.execute(
            "SELECT * FROM applications WHERE id = ?",
            (app_id,),
        ).fetchone()
        if row is None:
            raise AppNotFoundError(app_id)
        return self._from_row(row)

    def list(self, limit: int = 100, offset: int = 0) -> list[Application]:
        # SELECT * FROM applications  -> [_from_row(r) for r in rows]
        rows = self._conn.execute(
            "SELECT * FROM applications ORDER BY created_at, id LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def update(self, app: Application) -> None:
        # UPDATE ... WHERE id = ?; if cursor.rowcount == 0 raise AppNotFoundError
        values = self._to_row(app)
        cursor = self._conn.execute(
            """
            UPDATE applications
            SET job_id = ?, resume_title = ?, resume_file_path = ?, resume_file_link = ?,
                resume_created_at = ?, resume_updated_at = ?, applied_at = ?,
                updated_at = ?, created_at = ?, status = ?
            WHERE id = ?
            """,
            (*values[1:], values[0]),
        )
        if cursor.rowcount == 0:
            raise AppNotFoundError(app.id)
        self._conn.commit()

    def delete(self, app_id: str) -> None:
        # DELETE ... WHERE id = ?; same rowcount check
        cursor = self._conn.execute(
            "DELETE FROM applications WHERE id = ?",
            (app_id,),
        )
        if cursor.rowcount == 0:
            raise AppNotFoundError(app_id)
        self._conn.commit()

class InMemoryApplicationRepository(ApplicationRepository):
    def __init__(self) -> None:
        self._apps: dict[str, Application] = {}

    def add(self, app: Application) -> str:
        # store under app.id; raise AppAlreadyExistsError if the id already exists
        if app.id in self._apps:
            raise AppAlreadyExistsError(app.id)
        self._apps[app.id] = app
        return app.id

    def get(self, app_id: str) -> Optional[Application]:
        try:
            return self._apps[app_id]
        except KeyError:
            raise AppNotFoundError(app_id)

    def list(self, limit: int = 100, offset: int = 0) -> list[Application]:
        apps = sorted(self._apps.values(), key=lambda app: (app.created_at, app.id))
        return apps[offset:offset + limit]

    def update(self, app: Application) -> None:
        # raise AppNotFoundError if missing, else replace
        if app.id not in self._apps:
            raise AppNotFoundError(app.id)
        self._apps[app.id] = app

    def delete(self, app_id: str) -> None:
        # raise AppNotFoundError if missing, else remove
        if app_id not in self._apps:
            raise AppNotFoundError(app_id)
        self._apps.pop(app_id)
