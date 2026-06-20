from dataclasses import dataclass, field

from src.analysis.progress import ProgressReporter, null_reporter
from src.collectors.adzuna import AdzunaCollector
from src.collectors.arbeitnow import ArbeitnowCollector
from src.collectors.base import BaseCollector
from src.collectors.remotive import RemotiveCollector
from src.config import DEFAULT_ADZUNA_COUNTRIES, DEFAULT_QUERIES
from src.models import JobPosting


@dataclass
class CollectionResult:
    jobs: list[JobPosting] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)


def deduplicate_jobs(jobs: list[JobPosting]) -> list[JobPosting]:
    seen_urls: set[str] = set()
    seen_keys: set[tuple[str, str]] = set()
    unique: list[JobPosting] = []
    for job in jobs:
        url_key = job.url.strip().lower()
        if url_key and url_key in seen_urls:
            continue
        title_company = (job.title.strip().lower(), job.company.strip().lower())
        if title_company in seen_keys:
            continue
        if url_key:
            seen_urls.add(url_key)
        seen_keys.add(title_company)
        unique.append(job)
    return unique


class JobOrchestrator:
    def __init__(self) -> None:
        self.collectors: dict[str, BaseCollector] = {
            "remotive": RemotiveCollector(),
            "adzuna": AdzunaCollector(),
            "arbeitnow": ArbeitnowCollector(),
        }

    def collect(
        self,
        sources: list[str],
        max_results: int,
        adzuna_countries: list[str] | None = None,
        reporter: ProgressReporter | None = None,
    ) -> CollectionResult:
        reporter = reporter or null_reporter()
        result = CollectionResult()
        per_source_budget = max(1, max_results // max(len(sources), 1))
        countries = adzuna_countries or DEFAULT_ADZUNA_COUNTRIES

        for source in sources:
            collector = self.collectors.get(source)
            if collector is None:
                result.warnings.append(f"Unknown source: {source}")
                continue

            if source == "adzuna":
                adzuna = collector
                if not adzuna.has_credentials():
                    result.warnings.append(
                        "Adzuna skipped: set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env "
                        "(register at developer.adzuna.com)."
                    )
                    continue
                try:
                    source_jobs = self._collect_adzuna(
                        adzuna, per_source_budget, countries, reporter=reporter
                    )
                    result.jobs.extend(source_jobs)
                    if source_jobs:
                        result.sources_used.append(source)
                except Exception as exc:
                    result.warnings.append(f"Adzuna failed: {exc}")
                continue

            label = source.replace("_", " ").title()
            reporter.emit(
                f"Collecting jobs from {label}…",
                stage="collect",
                source=source,
            )
            try:
                if source == "remotive":
                    source_jobs = self._collect_batch(collector, per_source_budget)
                elif source == "arbeitnow":
                    source_jobs = self._collect_batch(collector, per_source_budget)
                else:
                    source_jobs = self._collect_queries(collector, per_source_budget)
                result.jobs.extend(source_jobs)
                if source_jobs:
                    result.sources_used.append(source)
            except Exception as exc:
                result.warnings.append(f"{source.title()} failed: {exc}")

        result.jobs = deduplicate_jobs(result.jobs)[:max_results]
        return result

    def _collect_batch(self, collector: BaseCollector, budget: int) -> list[JobPosting]:
        matched: list[JobPosting] = []
        seen_ids: set[str] = set()
        if isinstance(collector, RemotiveCollector):
            collector.fetch_batch()
        elif isinstance(collector, ArbeitnowCollector):
            collector.fetch_all()

        per_query = max(1, budget // len(DEFAULT_QUERIES))
        for query in DEFAULT_QUERIES:
            for job in collector.search_jobs(query, per_query):
                if job.id not in seen_ids:
                    seen_ids.add(job.id)
                    matched.append(job)
        return matched[:budget]

    def _collect_adzuna(
        self,
        collector: AdzunaCollector,
        budget: int,
        countries: list[str],
        reporter: ProgressReporter | None = None,
    ) -> list[JobPosting]:
        reporter = reporter or null_reporter()
        matched: list[JobPosting] = []
        seen_ids: set[str] = set()
        per_country = max(1, budget // max(len(countries), 1))
        per_query = max(1, per_country // len(DEFAULT_QUERIES))
        for country in countries:
            reporter.emit(
                f"Collecting jobs from Adzuna ({country})…",
                stage="collect",
                source="adzuna",
            )
            for query in DEFAULT_QUERIES:
                try:
                    jobs = collector.search_jobs(query, per_query, country=country)
                except Exception:
                    continue
                for job in jobs:
                    if job.id not in seen_ids:
                        seen_ids.add(job.id)
                        matched.append(job)
        return matched[:budget]

    def _collect_queries(self, collector: BaseCollector, budget: int) -> list[JobPosting]:
        matched: list[JobPosting] = []
        seen_ids: set[str] = set()
        per_query = max(1, budget // len(DEFAULT_QUERIES))
        for query in DEFAULT_QUERIES:
            for job in collector.search_jobs(query, per_query):
                if job.id not in seen_ids:
                    seen_ids.add(job.id)
                    matched.append(job)
        return matched[:budget]
