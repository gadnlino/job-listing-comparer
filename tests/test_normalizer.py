from src.analysis.normalizer import deduplicate_jobs
from src.collectors.orchestrator import deduplicate_jobs as orch_dedup
from src.models import JobPosting


def test_deduplicate_fallback_title_company():
    jobs = [
        JobPosting(id="1", source="a", title="Engineer", company="Co", url="", description=""),
        JobPosting(id="2", source="b", title="Engineer", company="Co", url="", description=""),
    ]
    assert len(orch_dedup(jobs)) == 1


def test_normalizer_reexport():
    assert deduplicate_jobs is orch_dedup
