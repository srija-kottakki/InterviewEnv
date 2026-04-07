from __future__ import annotations

from utils.feedback_analyzer import analyze_behavior


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


def relevance_score(answer: str, state: dict) -> float:
    task_id = state.get("task_id", "easy")
    parsed_resume = state.get("parsed_resume_data", {}) or {}
    resume_terms = []
    for key in ("skills", "programming_languages", "libraries_frameworks", "tools", "tools_technologies"):
        resume_terms.extend(parsed_resume.get(key, []) or [])
    resume_bonus = 0.15 if _contains_any(answer, [str(term) for term in resume_terms]) else 0.0
    groups_by_task = {
        "easy": [
            ["interview", "role", "company", "position", "team"],
            ["experience", "project", "built", "worked", "created"],
            ["skill", "strength", "communication", "collaboration", "ownership"],
        ],
        "medium": [
            ["first", "then", "finally", "because", "approach"],
            ["specific", "for example", "project", "measured", "result"],
            ["tradeoff", "constraint", "decision", "impact", "validated"],
            ["learned", "improve", "feedback", "next time", "would"],
        ],
        "hard": [
            ["situation", "context", "challenge", "conflict", "when"],
            ["task", "responsibility", "goal", "needed", "expected"],
            ["action", "i did", "i worked", "i decided", "i communicated"],
            ["result", "outcome", "impact", "resolved", "improved"],
            ["learned", "reflection", "feedback", "metric", "measured"],
        ],
    }
    return _clamp(0.65 * _keyword_fraction(answer, groups_by_task[task_id]) + 0.20 * _length_credit(answer, 55) + resume_bonus)


def classify_quality(answer: str) -> str:
    score = grade_medium(answer, {})
    if score >= 0.7:
        return "good"
    if score >= 0.35:
        return "avg"
    return "poor"


def grade_easy(answer: str, state: dict) -> float:
    """Easy: detect whether the answer contains role/interview-relevant keywords."""
    feedback = analyze_behavior(answer, state)
    relevance = relevance_score(answer, {**state, "task_id": "easy"})
    return _clamp((float(feedback["clarity_score"]) + float(feedback["confidence_score"]) + relevance) / 3.0)


def grade_medium(answer: str, state: dict) -> float:
    """Medium: classify answer quality using structure, specificity, and reflection."""
    feedback = analyze_behavior(answer, state)
    relevance = relevance_score(answer, {**state, "task_id": "medium"})
    return _clamp((float(feedback["clarity_score"]) + float(feedback["confidence_score"]) + relevance) / 3.0)


def grade_hard(answer: str, state: dict) -> float:
    """Hard: open-ended STAR/rubric evaluation scored from 0.0 to 1.0."""
    feedback = analyze_behavior(answer, state)
    relevance = relevance_score(answer, {**state, "task_id": "hard"})
    return _clamp((float(feedback["clarity_score"]) + float(feedback["confidence_score"]) + relevance) / 3.0)


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}


def get_grader(task_id: str):
    return GRADERS[task_id]
