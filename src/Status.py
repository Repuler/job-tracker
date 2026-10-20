# enum for status of a task
from enum import enum


class InvalidTransitionError(Exception):
    pass
@dataclass
class Application:
    job_title: str
    company: str
    status: Status = Status.SAVED
    updated_at: datetime = field(default_factory=datetime.now)
    def advance_to(self, new_status: Status) -> None:
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidTransitionError(
                f"Can't move from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.now()