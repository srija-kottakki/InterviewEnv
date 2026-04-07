from __future__ import annotations


def _clamp(value: float) -> float:
    return round(min(max(value, 0.0), 1.0), 4)


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _keyword_fraction(text: str, groups: list[list[str]]) -> float:
    if not groups:
        return 0.0
    return sum(1 for group in groups if _contains_any(text, group)) / len(groups)


def _length_credit(text: str, target_words: int) -> float:
    return min(len(text.split()) / target_words, 1.0)


def classify_quality(answer: str) -> str:
    score = grade_medium(answer, {})
    if score >= 0.7:
        return "good"
    if score >= 0.35:
        return "avg"
    return "poor"


def grade_easy(answer: str, state: dict) -> float:
    """Easy: detect whether the answer contains role/interview-relevant keywords."""
    keyword_groups = [
        ["interview", "role", "company", "position", "team"],
        ["experience", "project", "built", "worked", "created"],
        ["skill", "strength", "communication", "collaboration", "ownership"],
    ]
    score = 0.75 * _keyword_fraction(answer, keyword_groups) + 0.25 * _length_credit(answer, 35)
    return _clamp(score)


def grade_medium(answer: str, state: dict) -> float:
    """Medium: classify answer quality using structure, specificity, and reflection."""
    keyword_groups = [
        ["first", "then", "finally", "because", "approach"],
        ["specific", "for example", "project", "measured", "result"],
        ["tradeoff", "constraint", "decision", "impact", "validated"],
        ["learned", "improve", "feedback", "next time", "would"],
    ]
    score = 0.65 * _keyword_fraction(answer, keyword_groups) + 0.35 * _length_credit(answer, 65)
    return _clamp(score)


def grade_hard(answer: str, state: dict) -> float:
    """Hard: open-ended STAR/rubric evaluation scored from 0.0 to 1.0."""
    rubric_groups = [
        ["situation", "context", "challenge", "conflict", "when"],
        ["task", "responsibility", "goal", "needed", "expected"],
        ["action", "i did", "i worked", "i decided", "i communicated"],
        ["result", "outcome", "impact", "resolved", "improved"],
        ["learned", "reflection", "feedback", "metric", "measured"],
    ]
    score = 0.75 * _keyword_fraction(answer, rubric_groups) + 0.25 * _length_credit(answer, 90)
    if _contains_any(answer, ["star", "situation", "task", "action", "result"]):
        score += 0.05
    return _clamp(score)


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}


def get_grader(task_id: str):
    return GRADERS[task_id]
