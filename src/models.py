from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

WeightTier = Literal["high", "medium", "low"]
LinkStatus = Literal["accessible", "inaccessible", "unknown"]


class DetectedSkill(BaseModel):
    canonical_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    weight: WeightTier
    snippet: Optional[str] = None


class JobPosting(BaseModel):
    id: str
    source: str
    title: str
    company: str
    location: Optional[str] = None
    country: Optional[str] = None
    remote_type: Optional[str] = None
    url: str
    description: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    created_at: Optional[datetime] = None
    raw_payload: Optional[dict[str, Any]] = None


class JobMatch(BaseModel):
    job: JobPosting
    primary_track: str
    track_scores: dict[str, int]
    fit_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    seniority_estimate: str
    link_status: LinkStatus = "unknown"
    link_status_code: Optional[int] = None


class TopJobSummary(BaseModel):
    title: str
    company: str
    source: str
    fit_score: float
    primary_track: str
    matched_skills: list[str]
    missing_skills: list[str]
    seniority_estimate: str
    url: str
    link_status: LinkStatus = "unknown"
    link_status_code: Optional[int] = None


class SourceSummary(BaseModel):
    source: str
    job_count: int
    avg_fit: float
    top_track: Optional[str] = None


class SkillFrequency(BaseModel):
    skill: str
    count: int


class ReportSummaryContext(BaseModel):
    resume_skills: list[str]
    total_jobs_analyzed: int
    jobs_by_source: dict[str, int]
    jobs_by_track: dict[str, int]
    avg_fit_by_track: dict[str, float]
    top_requested_skills: list[SkillFrequency]
    top_missing_skills: list[SkillFrequency]
    top_matching_jobs: list[TopJobSummary]
    per_source_summary: list[SourceSummary]
    study_recommendation: str
    link_exclusions_by_source: dict[str, int] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    resume_skills: list[DetectedSkill]
    matches: list[JobMatch]
    total_jobs_analyzed: int
    warnings: list[str]
    sources_used: list[str]
    jobs_by_track: dict[str, int]
    top_requested_skills: list[SkillFrequency]
    top_missing_skills: list[SkillFrequency]
    study_recommendation: str
    llm_used: bool = False
    pdf_generated: bool = False
