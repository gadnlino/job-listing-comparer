from typing import Any

import httpx

from src.collectors.base import BaseCollector
from src.models import JobPosting

ARBEITNOW_API = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowCollector(BaseCollector):
    name = "arbeitnow"
    _cached_jobs: list[JobPosting] | None = None

    def fetch_all(self, max_pages: int = 5) -> list[JobPosting]:
        if self._cached_jobs is not None:
            return self._cached_jobs

        jobs: list[JobPosting] = []
        url: str | None = ARBEITNOW_API
        pages = 0
        while url and pages < max_pages:
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", payload.get("jobs", []))
            if isinstance(data, list):
                jobs.extend(self._normalize(item) for item in data)
            url = payload.get("links", {}).get("next") if isinstance(payload.get("links"), dict) else None
            pages += 1

        self._cached_jobs = jobs
        return jobs

    def search_jobs(self, query: str, max_results: int, **kwargs) -> list[JobPosting]:
        jobs = self.fetch_all()
        query_lower = query.lower()
        terms = query_lower.split()
        filtered = [
            job
            for job in jobs
            if all(term in f"{job.title} {job.description}".lower() for term in terms)
        ]
        return filtered[:max_results]

    def _normalize(self, item: dict[str, Any]) -> JobPosting:
        tags = item.get("tags") or []
        remote_type = "remote" if item.get("remote") else None
        location = item.get("location") or (", ".join(tags) if tags else None)
        return JobPosting(
            id=str(item.get("slug", item.get("url", item.get("title", "")))),
            source=self.name,
            title=item.get("title", "Unknown"),
            company=item.get("company_name") or item.get("company") or "Unknown",
            location=location,
            country=item.get("country"),
            remote_type=remote_type,
            url=item.get("url") or "",
            description=item.get("description") or "",
            salary_min=None,
            salary_max=None,
            currency=None,
            created_at=None,
            raw_payload=item,
        )
