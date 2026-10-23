from __future__ import annotations
from ast import Dict, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4
from pathlib import Path


class Status(Enum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


ALLOWED_TRANSITIONS: Dict[Status, Set[Status]] = {
    Status.SAVED: {Status.APPLIED},
    Status.APPLIED: {Status.INTERVIEWING, Status.REJECTED},
    Status.INTERVIEWING: {Status.OFFERED, Status.REJECTED},
    Status.OFFERED: set(),
    Status.REJECTED: set(),
    Status.WITHDRAWN: set(),
}


class InvalidTransitionError(Exception):
    pass


class WorkMode(Enum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"


class Seniority(Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"


def new_id() -> str:
    return str(uuid4())


@dataclass
class Org:
    name: str
    url: str
    logo: str | None = None
    mission: str | None = None
    id: str = field(default_factory=new_id)


@dataclass
class Job:
    title: str
    url: str
    org_id: str
    seniority: Seniority
    workmode: WorkMode
    id: str = field(default_factory=new_id)
    salary_min: int | None = None
    salary_max: int | None = None
    posted_at: datetime | None = None
    source: str | None = None  # "LinkedIn", "Job Scout", etc.
    location: str | None = None
    description: str | None = None

    def get_salary_range(self) -> str:
        if self.salary_min is None and self.salary_max is None:
            return "Not specified"
        if self.salary_min is None:
            return f"Up to {self.salary_max}"
        if self.salary_max is None:
            return f"At least {self.salary_min}"
        return f"{self.salary_min} - {self.salary_max}"

    def get_details(self) -> list[str]:
        results = [
            self.id,
            self.title,
            self.url,
            self.org_id,
            self.seniority,
            self.workmode,
            self.salary_min,
            self.salary_max,
            self.posted_at,
            self.source,
            self.location,
            self.description,
        ]
        return results

    def get_org_data(self) -> Org:
        return self.org


@dataclass
class Resume:
    title: str
    file_path: str
    file_link: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(
        default_factory=datetime.now
    )  # might define via metadata

    @classmethod
    def from_file(cls, file_path: str, title: str | None = None) -> "Resume":
        return cls(title=title or Path(file_path).stem, file_path=file_path)

    def update(
        self,
        title: str | None,
        file_path: str | None,
        file_link: str | None,
    ) -> None:
        is_updated = False
        if title is not None and title != self.title:
            self.title = title
            is_updated = True
        if file_path is not None and file_path != self.file_path:
            self.file_path = file_path
            is_updated = True
        if file_link is not None and file_link != self.file_link:
            self.file_link = file_link
            is_updated = True
        if is_updated:
            self.updated_at = datetime.now()
        else:
            raise ValueError("Nothing to update")


@dataclass
class Application:
    url: str
    resume: Resume
    applied_at: datetime | None = None
    updated_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    status: Status = Status.SAVED

    def advance_to(self, new_status: Status) -> None:
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidTransitionError(
                f"Can't move from {self.status.value} to {new_status.value}"
            )
        if new_status == Status.APPLIED:
            self.applied_at = datetime.now()
        self.status = new_status
        self.updated_at = datetime.now()
