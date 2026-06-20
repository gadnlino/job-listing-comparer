from datetime import datetime
from typing import Any

import httpx

from src.collectors.base import BaseCollector
from src.models import JobPosting

REMOTIVE_API = "https://remotive.com/api/remote-jobs"


class RemotiveCollector(BaseCollector):
    name = "remotive"
    _cached_jobs: list[JobPosting] | None = None

    def fetch_batch(self, category: str = "software-dev") -> list[JobPosting]:
        if self._cached_jobs is not None:
            return self._cached_jobs
        response = httpx.get(REMOTIVE_API, params={"category": category}, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
        jobs = [self._normalize(item) for item in payload.get("jobs", [])]
        self._cached_jobs = jobs
        return jobs

    def search_jobs(self, query: str, max_results: int, **kwargs) -> list[JobPosting]:
        jobs = self.fetch_batch(kwargs.get("category", "software-dev"))
        query_lower = query.lower()
        terms = query_lower.split()
        filtered = [
            job
            for job in jobs
            if all(term in f"{job.title} {job.description}".lower() for term in terms)
        ]
        return filtered[:max_results]

    def _normalize(self, item: dict[str, Any]) -> JobPosting:
        salary = item.get("salary") or ""
        salary_min = salary_max = None
        currency = None
        if isinstance(salary, str) and salary.strip():
            currency = "USD"
        return JobPosting(
            id=str(item.get("id", item.get("url", ""))),
            source=self.name,
            title=item.get("title", "Unknown"),
            company=item.get("company_name", "Unknown"),
            location=item.get("candidate_required_location"),
            country=item.get("job_region"),
            remote_type="remote",
            url=item.get("url", ""),
            description=item.get("description") or "",
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            created_at=_parse_date(item.get("publication_date")),
            raw_payload=item,
        )


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
