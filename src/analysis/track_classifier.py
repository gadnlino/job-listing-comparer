from src.config import TRACK_KEYWORDS, TRACK_PRIORITY


def classify_tracks(title: str, description: str) -> tuple[dict[str, int], str]:
    text = f"{title} {description}".lower()
    scores: dict[str, int] = {}
    for track, keywords in TRACK_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            scores[track] = count

    if not scores:
        return {}, "unknown"

    max_score = max(scores.values())
    candidates = [track for track, score in scores.items() if score == max_score]
    for track in TRACK_PRIORITY:
        if track in candidates:
            return scores, track
    return scores, candidates[0]
