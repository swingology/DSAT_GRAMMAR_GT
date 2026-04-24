"""Job state machine and pipeline orchestration for DSAT question processing."""
from typing import Optional


# State transition table: {from_status: set(allowed_to_statuses)}
TRANSITIONS = {
    "pending": {"parsing", "extracting", "failed"},
    "parsing": {"extracting", "failed"},
    "extracting": {"generating", "annotating", "failed"},
    "generating": {"annotating", "failed"},
    "annotating": {"overlap_checking", "validating", "failed"},
    "overlap_checking": {"validating", "failed"},
    "validating": {"approved", "needs_review", "failed"},
    "approved": set(),       # terminal
    "needs_review": set(),    # terminal (wait for admin)
    "failed": set(),          # terminal
}

ALL_STATUSES = set(TRANSITIONS.keys())


def can_transition(from_status: str, to_status: str) -> bool:
    """Check if a transition from from_status to to_status is valid."""
    if to_status == "failed":
        return from_status not in ("approved", "needs_review", "failed")
    return to_status in TRANSITIONS.get(from_status, set())


def next_status(current: str, content_origin: str = "official", job_type: str = "ingest") -> Optional[str]:
    """Determine the next status in the pipeline based on current status and job type."""
    needs_overlap = content_origin in ("unofficial", "generated")

    if current == "pending":
        if job_type == "generate":
            return "extracting"  # generation skips parsing
        return "parsing"
    elif current == "parsing":
        return "extracting"
    elif current == "extracting":
        if job_type == "generate":
            return "generating"
        return "annotating"
    elif current == "generating":
        return "annotating"
    elif current == "annotating":
        if needs_overlap:
            return "overlap_checking"
        return "validating"
    elif current == "overlap_checking":
        return "validating"
    elif current == "validating":
        return "approved"  # default; validator may set needs_review instead
    return None


class JobOrchestrator:
    """Orchestrates the processing pipeline for a question job."""

    def __init__(self, job_id: str, content_origin: str, job_type: str):
        self.job_id = job_id
        self.content_origin = content_origin
        self.job_type = job_type
        self.current_status = "pending"
        self.errors: list[dict] = []

    def advance(self) -> str:
        """Advance to the next pipeline status. Returns the new status."""
        next_s = next_status(self.current_status, self.content_origin, self.job_type)
        if next_s and can_transition(self.current_status, next_s):
            self.current_status = next_s
            return self.current_status
        raise ValueError(f"Cannot advance from {self.current_status}")

    def fail(self, step: str, error_code: str, message: str, retries: int = 0) -> str:
        """Mark the job as failed with structured error info."""
        self.errors.append({
            "step": step,
            "error_code": error_code,
            "message": message,
            "retries": retries,
            "max_retries": 3,
        })
        self.current_status = "failed"
        return self.current_status