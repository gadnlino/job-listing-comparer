from src.resume.skill_extractor import extract_skills


def test_known_skills_detected():
    text = "Skills: Python, AWS, Kubernetes, Terraform, Docker"
    skills = extract_skills(text)
    names = {s.canonical_name for s in skills}
    assert "Python" in names
    assert "AWS" in names
    assert "Kubernetes" in names


def test_alias_k8s_maps_to_kubernetes():
    text = "Experience with k8s orchestration"
    skills = extract_skills(text)
    names = [s.canonical_name for s in skills]
    assert "Kubernetes" in names


def test_javascript_not_java():
    text = "Built systems with JavaScript and TypeScript"
    skills = extract_skills(text)
    names = {s.canonical_name for s in skills}
    assert "JavaScript" in names
    assert "Java" not in names


def test_deduplication_keeps_highest_confidence():
    text = "kubernetes and k8s expert"
    skills = extract_skills(text)
    k8s_skills = [s for s in skills if s.canonical_name == "Kubernetes"]
    assert len(k8s_skills) == 1


def test_detected_skill_shape():
    text = "Python developer"
    skills = extract_skills(text)
    assert skills
    skill = skills[0]
    assert skill.canonical_name
    assert 0 <= skill.confidence <= 1
    assert skill.weight in {"high", "medium", "low"}
