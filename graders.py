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


def relevance_score(answer: str, state: dict) -> float:
    task_id = state.get("task_id", "easy")
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
    return _clamp(0.75 * _keyword_fraction(answer, groups_by_task[task_id]) + 0.25 * _length_credit(answer, 55))


def analyze_behavior(answer: str, state: dict) -> dict[str, object]:
    words = [word.strip(".,!?;:").lower() for word in answer.split()]
    filler_words = {"um", "uh", "like", "basically"}
    filler_count = sum(1 for word in words if word in filler_words)
    lowered = answer.lower()
    if "you know" in lowered:
        filler_count += lowered.count("you know")

    filler_score = _clamp(1.0 - min(filler_count / 4.0, 1.0))
    confident_markers = ["i led", "i decided", "i built", "i measured", "i improved", "i learned", "i recommend"]
    uncertain_markers = ["maybe", "sort of", "kind of", "i guess", "probably", "not sure"]
    confidence_score = _clamp(
        0.45
        + 0.12 * sum(1 for marker in confident_markers if marker in lowered)
        - 0.12 * sum(1 for marker in uncertain_markers if marker in lowered)
        + 0.20 * _length_credit(answer, 45)
    )
    structure_markers = ["first", "then", "because", "for example", "result", "learned", "situation", "task", "action"]
    clarity_score = _clamp(0.35 * _length_credit(answer, 55) + 0.65 * min(sum(1 for marker in structure_markers if marker in lowered) / 3.0, 1.0))

    comments = []
    comments.append("Low filler usage." if filler_score >= 0.8 else "Reduce filler words such as um, uh, like, basically, or you know.")
    comments.append("Confident delivery." if confidence_score >= 0.7 else "Use more decisive phrasing and own your actions.")
    comments.append("Clear structure." if clarity_score >= 0.7 else "Add structure, examples, and a measurable result.")

    return {
        "filler_score": filler_score,
        "confidence_score": confidence_score,
        "clarity_score": clarity_score,
        "comments": " ".join(comments),
    }


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
