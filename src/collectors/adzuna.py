import httpx

from src.collectors.base import BaseCollector
from src.config import ADZUNA_APP_ID, ADZUNA_APP_KEY
from src.models import JobPosting

ADZUNA_API = "https://api.adzuna.com/v1/api/jobs"


class AdzunaCollector(BaseCollector):
    name = "adzuna"

    def has_credentials(self) -> bool:
        return bool(ADZUNA_APP_ID and ADZUNA_APP_KEY)

    def search_jobs(self, query: str, max_results: int, **kwargs) -> list[JobPosting]:
        if not self.has_credentials():
            return []

        country = kwargs.get("country", "gb")
        page = kwargs.get("page", 1)
        results_per_page = min(max_results, kwargs.get("results_per_page", 20))

        url = f"{ADZUNA_API}/{country}/search/{page}"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": query,
            "results_per_page": results_per_page,
            "content-type": "application/json",
        }
        response = httpx.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
        return [self._normalize(item, country) for item in payload.get("results", [])]

    def _normalize(self, item: dict, country: str) -> JobPosting:
        company = item.get("company", {}) or {}
        location = item.get("location", {}) or {}
        return JobPosting(
            id=str(item.get("id", item.get("redirect_url", ""))),
            source=self.name,
            title=item.get("title", "Unknown"),
            company=company.get("display_name", "Unknown"),
            location=location.get("display_name"),
            country=country,
            remote_type=None,
            url=item.get("redirect_url", ""),
            description=item.get("description") or "",
            salary_min=item.get("salary_min"),
            salary_max=item.get("salary_max"),
            currency=item.get("salary_currency"),
            created_at=None,
            raw_payload=item,
        )
