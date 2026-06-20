from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from src.analysis.progress import ProgressReporter, null_reporter
from src.config import (
    LINK_VALIDATION_ENABLED,
    LINK_VALIDATION_MAX_JOBS,
    LINK_VALIDATION_MIN_BODY_BYTES,
    LINK_VALIDATION_TIMEOUT_SECONDS,
)
from src.models import JobMatch, LinkStatus

MAX_READ_BYTES = 16 * 1024
MAX_REDIRECTS = 5
MAX_CONCURRENCY = 10
USER_AGENT = "CareerMarketFitScanner/1.0"


def _classify_response(status_code: int, body_size: int, min_body: int) -> LinkStatus:
    if status_code in (403, 429):
        return "unknown"
    if status_code in (404, 410):
        return "inaccessible"
    if status_code >= 500:
        return "inaccessible"
    if 200 <= status_code < 300:
        return "accessible" if body_size > min_body else "inaccessible"
    if 400 <= status_code < 500:
        return "unknown"
    return "unknown"


def _validate_single_url(url: str, timeout: float, min_body: int) -> tuple[LinkStatus, int | None]:
    url = url.strip()
    if not url:
        return "inaccessible", None

    try:
        with httpx.Client(
            follow_redirects=True,
            max_redirects=MAX_REDIRECTS,
            timeout=httpx.Timeout(5.0, read=timeout),
            headers={"User-Agent": USER_AGENT},
        ) as client:
            with client.stream("GET", url) as response:
                body_size = 0
                for chunk in response.iter_bytes(4096):
                    body_size += len(chunk)
                    if body_size >= MAX_READ_BYTES:
                        break
                return _classify_response(response.status_code, body_size, min_body), response.status_code
    except (httpx.TimeoutException, httpx.ConnectError, httpx.TooManyRedirects):
        return "inaccessible", None
    except Exception:
        return "unknown", None


def validate_job_links(
    matches: list[JobMatch],
    reporter: ProgressReporter | None = None,
) -> list[JobMatch]:
    reporter = reporter or null_reporter()

    if not matches:
        return []

    if not LINK_VALIDATION_ENABLED:
        return [
            m.model_copy(update={"link_status": "unknown", "link_status_code": None})
            for m in matches
        ]

    to_validate = matches[:LINK_VALIDATION_MAX_JOBS]
    remainder = matches[LINK_VALIDATION_MAX_JOBS:]
    statuses: list[tuple[LinkStatus, int | None]] = [("unknown", None)] * len(to_validate)
    total = len(to_validate)
    completed = 0

    reporter.emit(
        f"Validating {total} job links…",
        stage="validate",
        total=total,
    )

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
        future_to_idx = {
            executor.submit(
                _validate_single_url,
                m.job.url,
                LINK_VALIDATION_TIMEOUT_SECONDS,
                LINK_VALIDATION_MIN_BODY_BYTES,
            ): idx
            for idx, m in enumerate(to_validate)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                statuses[idx] = future.result()
            except Exception:
                statuses[idx] = ("unknown", None)
            completed += 1
            match = to_validate[idx]
            reporter.emit(
                f"Validating link {completed}/{total}: {match.job.title} ({match.job.source})",
                stage="validate",
                source=match.job.source,
                title=match.job.title,
                current=completed,
                total=total,
            )

    validated: list[JobMatch] = []
    for idx, match in enumerate(to_validate):
        status, code = statuses[idx]
        validated.append(match.model_copy(update={"link_status": status, "link_status_code": code}))

    for match in remainder:
        validated.append(match.model_copy(update={"link_status": "unknown", "link_status_code": None}))

    return validated


def filter_displayable_matches(matches: list[JobMatch]) -> list[JobMatch]:
    if not LINK_VALIDATION_ENABLED:
        return list(matches)
    return [m for m in matches if m.link_status in ("accessible", "unknown")]


def link_validation_summary(matches: list[JobMatch]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for match in matches:
        source = match.job.source
        if source not in summary:
            summary[source] = {
                "accessible": 0,
                "inaccessible": 0,
                "unknown": 0,
                "excluded": 0,
                "validated": 0,
            }
        counts = summary[source]
        counts[match.link_status] = counts.get(match.link_status, 0) + 1
        if match.link_status in ("accessible", "inaccessible"):
            counts["validated"] += 1
        if match.link_status == "inaccessible":
            counts["excluded"] += 1
    return summary


def build_link_validation_warnings(summary: dict[str, dict[str, int]]) -> list[str]:
    warnings: list[str] = []
    for source, counts in sorted(summary.items()):
        validated = counts["accessible"] + counts["inaccessible"]
        if validated == 0:
            continue
        if counts["inaccessible"] / validated > 0.2:
            warnings.append(
                f"{source}: {counts['inaccessible']} of {validated} links excluded — could not be verified"
            )
    return warnings
