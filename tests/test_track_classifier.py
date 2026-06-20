from src.analysis.track_classifier import classify_tracks


def test_multi_track_assignment():
    scores, _ = classify_tracks(
        "Senior Python AWS Backend Engineer",
        "Build serverless microservices with Lambda and DynamoDB",
    )
    assert "backend_cloud" in scores
    assert scores["backend_cloud"] >= 1


def test_primary_track_selection():
    _, primary = classify_tracks(
        "Platform Engineer",
        "Kubernetes, Terraform, CI/CD, observability with Grafana",
    )
    assert primary == "platform_engineering"
