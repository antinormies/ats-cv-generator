from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    description: str = ""
    salary: str = ""
    tags: list[str] = field(default_factory=list)
    posted_at: datetime | None = None
    remote: bool = False


NORMALIZED_FIELDS = ["title", "company", "location", "url", "source", "description", "salary", "tags", "posted_at", "remote"]
