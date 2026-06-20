from collections import Counter

from src.models import JobMatch, SkillFrequency


def count_jobs_by_track(matches: list[JobMatch]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for match in matches:
        track = match.primary_track if match.primary_track != "unknown" else "unclassified"
        counts[track] += 1
    return dict(counts)


def count_jobs_by_source(matches: list[JobMatch]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for match in matches:
        counts[match.job.source] += 1
    return dict(counts)


def top_requested_skills(matches: list[JobMatch], limit: int = 20) -> list[SkillFrequency]:
    counter: Counter[str] = Counter()
    for match in matches:
        counter.update(set(match.matched_skills + match.missing_skills))
    return [
        SkillFrequency(skill=skill, count=count)
        for skill, count in counter.most_common(limit)
    ]


def top_missing_skills(matches: list[JobMatch], limit: int = 20) -> list[SkillFrequency]:
    counter: Counter[str] = Counter()
    for match in matches:
        counter.update(match.missing_skills)
    return [
        SkillFrequency(skill=skill, count=count)
        for skill, count in counter.most_common(limit)
    ]


def avg_fit_by_track(matches: list[JobMatch]) -> dict[str, float]:
    totals: dict[str, list[float]] = {}
    for match in matches:
        track = match.primary_track
        totals.setdefault(track, []).append(match.fit_score)
    return {track: round(sum(vals) / len(vals), 1) for track, vals in totals.items()}
