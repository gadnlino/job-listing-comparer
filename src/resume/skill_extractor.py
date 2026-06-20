import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.config import SKILLS_PATH, WEIGHT_VALUES
from src.models import DetectedSkill, WeightTier


@dataclass
class SkillDefinition:
    canonical_name: str
    aliases: list[str]
    weight: WeightTier
    patterns: list[re.Pattern[str]]
    parent_of: list[str]


SECTION_HEADERS = ("skills:", "technologies:", "stack:", "technical skills:")


class SkillExtractor:
    def __init__(self, catalog_path: Path | None = None) -> None:
        path = catalog_path or SKILLS_PATH
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.skills = self._load_definitions(raw)
        self._children = {
            child.lower()
            for skill in self.skills
            for child in skill.parent_of
        }

    def _load_definitions(self, raw: list[dict]) -> list[SkillDefinition]:
        definitions: list[SkillDefinition] = []
        for entry in raw:
            patterns = [re.compile(p, re.IGNORECASE) for p in entry.get("patterns", [])]
            definitions.append(
                SkillDefinition(
                    canonical_name=entry["canonical_name"],
                    aliases=entry.get("aliases", []),
                    weight=entry["weight"],
                    patterns=patterns,
                    parent_of=entry.get("parent_of", []),
                )
            )
        definitions.sort(key=lambda s: -len(s.canonical_name))
        return definitions

    @staticmethod
    def normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()

    def extract_skills(self, text: str) -> list[DetectedSkill]:
        normalized = self.normalize_text(text)
        lines = text.splitlines()
        found: dict[str, DetectedSkill] = {}

        for skill in self.skills:
            if skill.canonical_name.lower() in self._children:
                continue
            if skill.canonical_name == "JavaScript":
                if re.search(r"\bjava\b", normalized) and not re.search(
                    r"\bjavascript\b|\bjs\b", normalized, re.IGNORECASE
                ):
                    pass

            best_confidence = 0.0
            best_snippet: str | None = None

            for pattern in skill.patterns:
                match = pattern.search(normalized)
                if not match:
                    continue
                if skill.canonical_name == "JavaScript" and re.search(
                    r"\bjava\b", normalized[max(0, match.start() - 1): match.end() + 1]
                ):
                    if "javascript" not in normalized[match.start(): match.end()].lower():
                        continue

                confidence = 1.0
                matched_text = match.group(0)
                if matched_text.lower() != skill.canonical_name.lower():
                    if any(alias.lower() == matched_text.lower() for alias in skill.aliases):
                        confidence = 0.9
                    else:
                        confidence = 0.85

                for line in lines:
                    if pattern.search(line.lower()):
                        if any(header in line.lower() for header in SECTION_HEADERS):
                            confidence = min(1.0, confidence + 0.05)
                        break

                if confidence > best_confidence:
                    best_confidence = confidence
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    best_snippet = text[start:end].strip()

            if best_confidence > 0:
                found[skill.canonical_name] = DetectedSkill(
                    canonical_name=skill.canonical_name,
                    confidence=round(best_confidence, 2),
                    weight=skill.weight,
                    snippet=best_snippet,
                )

        for skill in self.skills:
            if skill.canonical_name in found:
                continue
            if skill.canonical_name not in {p for s in self.skills for p in s.parent_of}:
                continue
            for parent in self.skills:
                if skill.canonical_name not in parent.parent_of:
                    continue
                if parent.canonical_name in found:
                    found[skill.canonical_name] = DetectedSkill(
                        canonical_name=skill.canonical_name,
                        confidence=0.85,
                        weight=skill.weight,
                        snippet=found[parent.canonical_name].snippet,
                    )
                    break

        return sorted(found.values(), key=lambda s: (-s.confidence, s.canonical_name))

    def skill_weight_value(self, skill_name: str) -> float:
        for skill in self.skills:
            if skill.canonical_name == skill_name:
                return WEIGHT_VALUES[skill.weight]
        return WEIGHT_VALUES["low"]

    def get_child_skills(self, parent_name: str) -> list[str]:
        for skill in self.skills:
            if skill.canonical_name == parent_name:
                return skill.parent_of
        return []


_default_extractor: SkillExtractor | None = None


def get_skill_extractor() -> SkillExtractor:
    global _default_extractor
    if _default_extractor is None:
        _default_extractor = SkillExtractor()
    return _default_extractor


def extract_skills(text: str) -> list[DetectedSkill]:
    return get_skill_extractor().extract_skills(text)
