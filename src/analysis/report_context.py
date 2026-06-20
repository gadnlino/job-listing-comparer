from src.analysis.aggregator import (
    avg_fit_by_track,
    count_jobs_by_source,
    count_jobs_by_track,
    top_missing_skills,
    top_requested_skills,
)
from src.models import DetectedSkill, JobMatch, ReportSummaryContext, SourceSummary, TopJobSummary


def build_study_recommendation(
    matches: list[JobMatch],
    jobs_by_track: dict[str, int],
    top_missing: list,
) -> str:
    if not matches:
        return "No jobs were found. Try different sources or increase max results."

    avg_by_track = avg_fit_by_track(matches)
    lines: list[str] = []

    for track, count in sorted(jobs_by_track.items(), key=lambda x: -x[1]):
        avg_fit = avg_by_track.get(track, 0)
        if count >= 3 and avg_fit >= 60:
            lines.append(f"- **{track}**: Strong near-term opportunity (high demand, high fit).")
        elif count >= 3 and avg_fit >= 40:
            lines.append(f"- **{track}**: Good specialization candidate (high demand, moderate fit).")
        elif count < 2:
            lines.append(f"- **{track}**: Lower priority (limited demand in current sample).")

    if top_missing:
        skills = ", ".join(item.skill for item in top_missing[:5])
        lines.append(f"- Priority study targets based on high-fit job gaps: {skills}.")

    return "\n".join(lines) if lines else "Review top matching jobs and missing skills to choose your next specialization."


def build_report_context(
    resume_skills: list[DetectedSkill],
    matches: list[JobMatch],
    display_matches: list[JobMatch] | None = None,
    link_exclusions_by_source: dict[str, int] | None = None,
) -> ReportSummaryContext:
    display_matches = display_matches if display_matches is not None else matches
    jobs_by_track = count_jobs_by_track(matches)
    jobs_by_source = count_jobs_by_source(matches)
    requested = top_requested_skills(matches)
    missing = top_missing_skills(matches)
    recommendation = build_study_recommendation(matches, jobs_by_track, missing)

    top_jobs = sorted(display_matches, key=lambda m: -m.fit_score)[:20]
    top_summaries = [
        TopJobSummary(
            title=m.job.title,
            company=m.job.company,
            source=m.job.source,
            fit_score=m.fit_score,
            primary_track=m.primary_track,
            matched_skills=m.matched_skills,
            missing_skills=m.missing_skills,
            seniority_estimate=m.seniority_estimate,
            url=m.job.url,
            link_status=m.link_status,
            link_status_code=m.link_status_code,
        )
        for m in top_jobs
    ]

    per_source: list[SourceSummary] = []
    for source, count in jobs_by_source.items():
        source_matches = [m for m in matches if m.job.source == source]
        avg_fit = (
            round(sum(m.fit_score for m in source_matches) / len(source_matches), 1)
            if source_matches
            else 0.0
        )
        track_counts = count_jobs_by_track(source_matches)
        top_track = max(track_counts, key=track_counts.get) if track_counts else None
        per_source.append(
            SourceSummary(source=source, job_count=count, avg_fit=avg_fit, top_track=top_track)
        )

    return ReportSummaryContext(
        resume_skills=[s.canonical_name for s in resume_skills],
        total_jobs_analyzed=len(matches),
        jobs_by_source=jobs_by_source,
        jobs_by_track=jobs_by_track,
        avg_fit_by_track=avg_fit_by_track(matches),
        top_requested_skills=requested,
        top_missing_skills=missing,
        top_matching_jobs=top_summaries,
        per_source_summary=per_source,
        study_recommendation=recommendation,
        link_exclusions_by_source=link_exclusions_by_source or {},
    )
