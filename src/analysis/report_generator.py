from datetime import datetime
from pathlib import Path

import httpx

from src.analysis.pdf_renderer import render_pdf_from_markdown
from src.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    PDF_RENDERER,
    REPORTS_DIR,
)
from src.models import JobMatch, ReportSummaryContext


def generate_template_summary(context: ReportSummaryContext) -> str:
    top_tracks = sorted(context.jobs_by_track.items(), key=lambda x: -x[1])[:3]
    track_text = ", ".join(f"{t} ({c})" for t, c in top_tracks) if top_tracks else "N/A"
    missing = ", ".join(s.skill for s in context.top_missing_skills[:5]) or "None identified"
    return (
        f"This analysis reviewed {context.total_jobs_analyzed} job postings across "
        f"{', '.join(context.jobs_by_source.keys()) or 'selected sources'}. "
        f"Your resume highlights skills including {', '.join(context.resume_skills[:8]) or 'limited detected skills'}. "
        f"The strongest career tracks by volume are {track_text}. "
        f"The most frequently missing skills across matching roles are {missing}. "
        f"{context.study_recommendation.replace(chr(10), ' ')}"
    )


def generate_llm_summary(context: ReportSummaryContext) -> tuple[str, bool]:
    prompt = (
        "You are a career advisor. Write a 2-3 paragraph executive summary based ONLY "
        "on the structured JSON below. Do not invent skills, counts, or recommendations "
        "not present in the data.\n\n"
        f"{context.model_dump_json(indent=2)}"
    )
    try:
        headers: dict[str, str] = {}
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"

        # Prefer OpenAI-compatible API (llama.cpp / Groq at /v1/chat/completions).
        response = httpx.post(
            f"{LLM_BASE_URL}/v1/chat/completions",
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful career advisor."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            headers=headers,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if choices:
            message = (choices[0].get("message") or {}).get("content") or ""
            text = str(message).strip()
            if text:
                return text, True
    except Exception:
        pass

    # Backwards-compatible fallback to Ollama's /api/generate.
    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "").strip()
        if text:
            return text, True
    except Exception:
        pass
    return generate_template_summary(context), False


def write_job_matches_csv(matches: list[JobMatch], path: Path) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source", "title", "company", "location", "country", "remote_type", "url",
        "primary_track", "fit_score", "matched_skills", "missing_skills",
        "salary_min", "salary_max", "currency", "seniority_estimate",
        "link_status", "link_status_code",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for match in sorted(matches, key=lambda m: -m.fit_score):
            job = match.job
            writer.writerow(
                {
                    "source": job.source,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location or "",
                    "country": job.country or "",
                    "remote_type": job.remote_type or "",
                    "url": job.url,
                    "primary_track": match.primary_track,
                    "fit_score": match.fit_score,
                    "matched_skills": "; ".join(match.matched_skills),
                    "missing_skills": "; ".join(match.missing_skills),
                    "salary_min": job.salary_min or "",
                    "salary_max": job.salary_max or "",
                    "currency": job.currency or "",
                    "seniority_estimate": match.seniority_estimate,
                    "link_status": match.link_status,
                    "link_status_code": match.link_status_code or "",
                }
            )


def _md_cell(value: str | float | int | None) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_cell(cell) for cell in row) + " |")
    return lines


def build_report_markdown(
    context: ReportSummaryContext,
    executive_summary: str,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now()
    date_str = generated_at.strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Career Market Fit Report",
        f"*Generated: {date_str}*",
        "",
        "## Executive Summary",
        executive_summary,
        "",
        f"## Total Jobs Analyzed: {context.total_jobs_analyzed}",
        "",
        "## Resume Skills Detected",
    ]

    if context.resume_skills:
        lines.extend(f"- {skill}" for skill in context.resume_skills)
    else:
        lines.append("- None detected")

    lines.extend(["", "## Market Overview", "", "### Jobs by Source"])
    if context.jobs_by_source:
        source_rows = [[source, str(count)] for source, count in context.jobs_by_source.items()]
        lines.extend(_markdown_table(["Source", "Jobs"], source_rows))
    else:
        lines.append("_No jobs analyzed._")

    lines.extend(["", "### Jobs by Career Track"])
    if context.jobs_by_track:
        track_rows = [
            [track, str(count), str(context.avg_fit_by_track.get(track, 0))]
            for track, count in context.jobs_by_track.items()
        ]
        lines.extend(_markdown_table(["Track", "Jobs", "Avg Fit"], track_rows))
    else:
        lines.append("_No jobs analyzed._")

    lines.extend(["", "## Top 20 Most Requested Skills"])
    if context.top_requested_skills:
        lines.extend(f"- {item.skill} ({item.count})" for item in context.top_requested_skills)
    else:
        lines.append("- None identified")

    lines.extend(["", "## Top 20 Missing Skills"])
    if context.top_missing_skills:
        lines.extend(f"- {item.skill} ({item.count})" for item in context.top_missing_skills)
    else:
        lines.append("- None identified")

    lines.extend(["", "## Per-Source Snapshot"])
    if context.per_source_summary:
        snapshot_rows = [
            [
                summary.source,
                str(summary.job_count),
                str(summary.avg_fit),
                summary.top_track or "N/A",
            ]
            for summary in context.per_source_summary
        ]
        lines.extend(_markdown_table(["Source", "Jobs", "Avg Fit", "Top Track"], snapshot_rows))
    else:
        lines.append("_No source data._")

    lines.extend(["", "## Top 20 Matching Jobs"])
    if context.top_matching_jobs:
        job_rows = [
            [
                job.title,
                job.company,
                job.source,
                str(job.fit_score),
                job.primary_track,
                job.seniority_estimate,
                job.link_status if job.link_status == "unknown" else "",
                job.url,
            ]
            for job in context.top_matching_jobs[:20]
        ]
        lines.extend(
            _markdown_table(
                ["Title", "Company", "Source", "Fit", "Track", "Seniority", "Link Status", "URL"],
                job_rows,
            )
        )
    else:
        lines.append("_No matching jobs._")

    if context.link_exclusions_by_source:
        lines.extend(["", "## Link Validation"])
        for source, count in sorted(context.link_exclusions_by_source.items()):
            if count > 0:
                lines.append(f"- **{source}**: {count} link(s) excluded (inaccessible)")

    lines.extend(["", "## Study Recommendation", context.study_recommendation, ""])
    lines.extend(
        [
            "---",
            "",
            "*Job data from Remotive, Adzuna, and Arbeitnow where applicable. "
            "Remotive job listings courtesy of [Remotive](https://remotive.com).*",
        ]
    )
    return "\n".join(lines)


def write_report_markdown(
    context: ReportSummaryContext,
    executive_summary: str,
    path: Path,
    generated_at: datetime | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        build_report_markdown(context, executive_summary, generated_at),
        encoding="utf-8",
    )


def generate_reports(
    matches: list[JobMatch],
    context: ReportSummaryContext,
    reports_dir: Path | None = None,
) -> tuple[Path, Path, Path | None, str, bool, str | None]:
    reports_dir = reports_dir or REPORTS_DIR
    csv_path = reports_dir / "job_matches.csv"
    md_path = reports_dir / "market_fit_report.md"
    pdf_path = reports_dir / "market_fit_report.pdf"

    executive_summary, llm_used = generate_llm_summary(context)
    write_job_matches_csv(matches, csv_path)

    generated_at = datetime.now()
    write_report_markdown(context, executive_summary, md_path, generated_at)

    pdf_result: Path | None = None
    pdf_warning: str | None = None
    if PDF_RENDERER == "weasyprint":
        pdf_result, pdf_warning = render_pdf_from_markdown(md_path, pdf_path)

    return csv_path, md_path, pdf_result, executive_summary, llm_used, pdf_warning
