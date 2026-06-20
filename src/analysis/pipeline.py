from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.analysis.aggregator import (
    count_jobs_by_track,
    top_missing_skills,
    top_requested_skills,
)
from src.analysis.link_validator import (
    build_link_validation_warnings,
    filter_displayable_matches,
    link_validation_summary,
    validate_job_links,
)
from src.analysis.matcher import match_jobs
from src.analysis.progress import ProgressReporter, null_reporter
from src.analysis.report_context import build_report_context, build_study_recommendation
from src.analysis.report_generator import generate_reports
from src.collectors.orchestrator import JobOrchestrator
from src.config import PROCESSED_DIR, REPORTS_DIR, UPLOADS_DIR
from src.models import AnalysisResult, ReportSummaryContext
from src.resume.parser import (
    EmptyResumeTextError,
    ResumeParseError,
    extract_text_from_pdf,
    save_resume_text,
)
from src.resume.skill_extractor import extract_skills


class AnalysisInputError(Exception):
    """User-facing validation error before pipeline starts."""


@dataclass
class AnalysisView:
    result: AnalysisResult
    pdf_generated: bool
    llm_fallback: bool
    has_remotive: bool


def run_analysis(
    content: bytes,
    filename: str,
    max_results: int,
    sources: list[str],
    adzuna_countries: list[str],
    reporter: ProgressReporter | None = None,
) -> AnalysisView:
    reporter = reporter or null_reporter()

    if not filename or not filename.lower().endswith(".pdf"):
        raise AnalysisInputError("Please upload a PDF resume file.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    upload_path = UPLOADS_DIR / f"{timestamp}_{filename}"
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    upload_path.write_bytes(content)

    reporter.emit("Parsing resume…", stage="parse")
    try:
        resume_text = extract_text_from_pdf(upload_path)
        save_resume_text(resume_text, PROCESSED_DIR / "resume_text.txt")
    except EmptyResumeTextError as exc:
        raise AnalysisInputError(str(exc)) from exc
    except ResumeParseError as exc:
        raise AnalysisInputError(str(exc)) from exc

    reporter.emit("Detecting skills…", stage="skills")
    resume_skills = extract_skills(resume_text)

    orchestrator = JobOrchestrator()
    collection = orchestrator.collect(
        sources=sources,
        max_results=max_results,
        adzuna_countries=adzuna_countries,
        reporter=reporter,
    )

    matches = match_jobs(collection.jobs, resume_skills)
    reporter.emit(
        f"Matching {len(matches)} jobs to your skills…",
        stage="match",
    )

    matches = validate_job_links(matches, reporter=reporter)
    display_matches = filter_displayable_matches(matches)
    link_summary = link_validation_summary(matches)
    link_exclusions = {
        source: counts["excluded"]
        for source, counts in link_summary.items()
        if counts["excluded"] > 0
    }
    collection.warnings.extend(build_link_validation_warnings(link_summary))

    jobs_by_track = count_jobs_by_track(matches)
    top_missing = top_missing_skills(matches)
    top_requested = top_requested_skills(matches)
    recommendation = build_study_recommendation(matches, jobs_by_track, top_missing)

    pdf_generated = False
    llm_used = False
    llm_fallback = False

    if matches:
        context = build_report_context(
            resume_skills,
            matches,
            display_matches=display_matches,
            link_exclusions_by_source=link_exclusions,
        )
        reporter.emit("Generating Markdown report…", stage="report")
        _, _, pdf_path, _, llm_used, pdf_warning = generate_reports(
            display_matches, context, REPORTS_DIR
        )
        reporter.emit("Rendering PDF report…", stage="report")
        pdf_generated = pdf_path is not None
        llm_fallback = pdf_generated and not llm_used
        if pdf_warning:
            collection.warnings.append(pdf_warning)
    else:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        from src.analysis.report_generator import write_job_matches_csv, write_report_markdown

        reporter.emit("Generating reports…", stage="report")
        empty_context = ReportSummaryContext(
            resume_skills=[s.canonical_name for s in resume_skills],
            total_jobs_analyzed=0,
            jobs_by_source={},
            jobs_by_track={},
            avg_fit_by_track={},
            top_requested_skills=[],
            top_missing_skills=[],
            top_matching_jobs=[],
            per_source_summary=[],
            study_recommendation=recommendation,
        )
        write_job_matches_csv([], REPORTS_DIR / "job_matches.csv")
        write_report_markdown(empty_context, "No jobs found.", REPORTS_DIR / "market_fit_report.md")

    result = AnalysisResult(
        resume_skills=resume_skills,
        matches=display_matches,
        total_jobs_analyzed=len(matches),
        warnings=collection.warnings,
        sources_used=collection.sources_used,
        jobs_by_track=jobs_by_track,
        top_requested_skills=top_requested,
        top_missing_skills=top_missing,
        study_recommendation=recommendation,
        llm_used=llm_used,
        pdf_generated=pdf_generated,
    )

    return AnalysisView(
        result=result,
        pdf_generated=pdf_generated,
        llm_fallback=llm_fallback,
        has_remotive=any(m.job.source == "remotive" for m in matches),
    )
