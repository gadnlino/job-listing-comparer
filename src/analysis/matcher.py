from src.analysis.track_classifier import classify_tracks
from src.config import SENIORITY_KEYWORDS, WEIGHT_VALUES
from src.models import DetectedSkill, JobMatch, JobPosting
from src.resume.skill_extractor import SkillExtractor, get_skill_extractor


def estimate_seniority(title: str, description: str = "") -> str:
    title_lower = title.lower()
    for level, keywords in SENIORITY_KEYWORDS:
        if any(kw in title_lower for kw in keywords):
            return level
    desc_lower = description.lower()
    for level, keywords in SENIORITY_KEYWORDS:
        if any(kw in desc_lower for kw in keywords):
            return level
    return "unknown"


def _specific_skills(resume_skills: list[DetectedSkill], extractor: SkillExtractor) -> set[str]:
    names = {s.canonical_name for s in resume_skills}
    children = set()
    for name in list(names):
        children.update(extractor.get_child_skills(name))
    return names | children


def _job_skill_names(job: JobPosting, extractor: SkillExtractor) -> list[str]:
    text = f"{job.title} {job.description}"
    return [s.canonical_name for s in extractor.extract_skills(text)]


def _effective_job_skills(job_skills: list[str], extractor: SkillExtractor) -> dict[str, float]:
    skill_set = set(job_skills)
    weights: dict[str, float] = {}
    for name in skill_set:
        child_skills = extractor.get_child_skills(name)
        present_children = [c for c in child_skills if c in skill_set]
        if present_children:
            for child in present_children:
                weights[child] = extractor.skill_weight_value(child)
            if name not in present_children:
                continue
        weights[name] = extractor.skill_weight_value(name)

    for parent_name in list(weights):
        for child in extractor.get_child_skills(parent_name):
            if child in weights and parent_name in weights:
                del weights[parent_name]
                break
    return weights


def match_job(
    job: JobPosting,
    resume_skills: list[DetectedSkill],
    extractor: SkillExtractor | None = None,
) -> JobMatch:
    extractor = extractor or get_skill_extractor()
    resume_names = _specific_skills(resume_skills, extractor)
    job_skill_list = _job_skill_names(job, extractor)
    job_weights = _effective_job_skills(job_skill_list, extractor)

    matched: list[str] = []
    missing: list[str] = []
    matched_weight = 0.0
    total_weight = sum(job_weights.values())

    for skill, weight in sorted(job_weights.items(), key=lambda x: -x[1]):
        if skill in resume_names:
            matched.append(skill)
            matched_weight += weight
        else:
            missing.append(skill)

    fit_score = round((matched_weight / total_weight) * 100, 1) if total_weight else 0.0
    fit_score = min(100.0, fit_score)

    track_scores, primary_track = classify_tracks(job.title, job.description)
    if not track_scores:
        primary_track = "unknown"

    return JobMatch(
        job=job,
        primary_track=primary_track,
        track_scores=track_scores,
        fit_score=fit_score,
        matched_skills=matched,
        missing_skills=missing,
        seniority_estimate=estimate_seniority(job.title, job.description),
    )


def match_jobs(
    jobs: list[JobPosting],
    resume_skills: list[DetectedSkill],
) -> list[JobMatch]:
    extractor = get_skill_extractor()
    matches = [match_job(job, resume_skills, extractor) for job in jobs]
    return sorted(matches, key=lambda m: -m.fit_score)
