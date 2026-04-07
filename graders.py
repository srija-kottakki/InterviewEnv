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


def _resume_match_score(answer: str, state: dict) -> float:
    parsed_resume = state.get("parsed_resume_data", {}) or {}
    resume_terms = []
    for key in ("skills", "programming_languages", "libraries_frameworks", "tools", "tools_technologies"):
        resume_terms.extend(parsed_resume.get(key, []) or [])
    if not resume_terms:
        return 0.0
    matches = sum(1 for term in resume_terms if term and _contains_any(answer, [str(term)]))
    return min(matches / 2.0, 1.0)


def _star_bonus(answer: str) -> float:
    groups = [
        ["situation", "context", "challenge", "conflict"],
        ["task", "responsibility", "goal"],
        ["action", "i did", "i built", "i led", "i communicated"],
        ["result", "outcome", "impact", "measured", "improved"],
        ["learned", "feedback", "next time", "reflection"],
    ]
    return _keyword_fraction(answer, groups)


def relevance_score(answer: str, state: dict) -> float:
    task_id = state.get("task_id", "easy")
    resume_match = _resume_match_score(answer, state)
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
    base = _keyword_fraction(answer, groups_by_task[task_id])
    length = _length_credit(answer, {"easy": 35, "medium": 60, "hard": 85}[task_id])
    if task_id == "easy":
        score = 0.50 * base + 0.30 * length + 0.20 * resume_match
    elif task_id == "medium":
        score = 0.50 * base + 0.25 * length + 0.25 * resume_match
    else:
        score = 0.45 * base + 0.20 * length + 0.20 * _star_bonus(answer) + 0.15 * resume_match
    return _clamp(score)


def classify_quality(answer: str) -> str:
    score = grade_medium(answer, {"task_id": "medium"})
    if score >= 0.7:
        return "good"
    if score >= 0.35:
        return "avg"
    return "poor"


def grade_easy(answer: str, state: dict) -> float:
    """Easy: detect whether the answer contains role/interview-relevant keywords."""
    feedback = analyze_behavior(answer, state)
    relevance = relevance_score(answer, {**state, "task_id": "easy"})
    return _clamp(0.30 * float(feedback["clarity_score"]) + 0.25 * float(feedback["confidence_score"]) + 0.45 * relevance)


def grade_medium(answer: str, state: dict) -> float:
    """Medium: classify answer quality using structure, specificity, and reflection."""
    feedback = analyze_behavior(answer, state)
    relevance = relevance_score(answer, {**state, "task_id": "medium"})
    return _clamp(0.35 * float(feedback["clarity_score"]) + 0.25 * float(feedback["confidence_score"]) + 0.40 * relevance)


def grade_hard(answer: str, state: dict) -> float:
    """Hard: open-ended STAR/rubric evaluation scored from 0.0 to 1.0."""
    feedback = analyze_behavior(answer, state)
    relevance = relevance_score(answer, {**state, "task_id": "hard"})
    return _clamp(0.40 * float(feedback["clarity_score"]) + 0.20 * float(feedback["confidence_score"]) + 0.40 * relevance)


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}


def get_grader(task_id: str):
    return GRADERS[task_id]
