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


def _consistency_score(state: dict) -> float:
    scores = [float(score) for score in state.get("score_history", [])[-3:]]
    if len(scores) < 2:
        return 0.5
    spread = max(scores) - min(scores)
    return _clamp(1.0 - spread)


def _improvement_score(state: dict, current_signal: float) -> float:
    scores = [float(score) for score in state.get("score_history", [])]
    if not scores:
        return 0.5
    delta = current_signal - scores[-1]
    if delta >= 0.15:
        return 1.0
    if delta >= 0.03:
        return 0.75
    if delta >= -0.05:
        return 0.5
    return 0.2


def _confidence_alignment(action: dict, feedback: dict[str, object]) -> float:
    confidence_level = float(action.get("confidence_level", 3))
    claimed = confidence_level / 5.0
    observed = float(feedback["confidence_score"])
    return _clamp(1.0 - abs(claimed - observed))


def _strategy_score(answer: str, action: dict, task_id: str) -> float:
    strategy = action.get("answer_strategy", "detailed")
    if strategy == "skip":
        return 0.0 if answer else 0.1
    if strategy == "clarify":
        return 0.75 if "?" in answer or len(answer.split()) >= 18 else 0.45
    if strategy == "direct":
        return 0.8 if 12 <= len(answer.split()) <= 80 else 0.55
    if strategy == "detailed":
        target = {"easy": 30, "medium": 55, "hard": 80}[task_id]
        return _length_credit(answer, target)
    return 0.5


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


def reward_breakdown(answer: str, state: dict, task_id: str | None = None) -> dict[str, float]:
    task = task_id or str(state.get("task_id", "easy"))
    action = state.get("last_action", {}) or {}
    feedback = analyze_behavior(answer, state)
    correctness = relevance_score(answer, {**state, "task_id": task})
    clarity = float(feedback["clarity_score"])
    confidence = float(feedback["confidence_score"])
    current_signal = _clamp((correctness + clarity + confidence) / 3.0)
    return {
        "correctness": correctness,
        "clarity": _clamp(clarity),
        "confidence": _clamp(confidence),
        "consistency": _consistency_score(state),
        "improvement": _improvement_score(state, current_signal),
        "confidence_alignment": _confidence_alignment(action, feedback),
        "strategy": _strategy_score(answer, action, task),
    }


def _weighted_reward(breakdown: dict[str, float], weights: dict[str, float]) -> float:
    return _clamp(sum(breakdown[key] * weight for key, weight in weights.items()))


def classify_quality(answer: str) -> str:
    score = grade_medium(answer, {"task_id": "medium"})
    if score >= 0.7:
        return "good"
    if score >= 0.35:
        return "avg"
    return "poor"


def grade_easy(answer: str, state: dict) -> float:
    """Easy: basic HR interview score with strong correctness/relevance weight."""
    breakdown = reward_breakdown(answer, state, "easy")
    return _weighted_reward(
        breakdown,
        {
            "correctness": 0.38,
            "clarity": 0.22,
            "confidence": 0.14,
            "consistency": 0.08,
            "improvement": 0.08,
            "confidence_alignment": 0.04,
            "strategy": 0.06,
        },
    )


def grade_medium(answer: str, state: dict) -> float:
    """Medium: technical reasoning score emphasizing clarity and tradeoff relevance."""
    breakdown = reward_breakdown(answer, state, "medium")
    return _weighted_reward(
        breakdown,
        {
            "correctness": 0.30,
            "clarity": 0.24,
            "confidence": 0.12,
            "consistency": 0.10,
            "improvement": 0.10,
            "confidence_alignment": 0.06,
            "strategy": 0.08,
        },
    )


def grade_hard(answer: str, state: dict) -> float:
    """Hard: adaptive/stress interview score emphasizing STAR evidence and trend."""
    breakdown = reward_breakdown(answer, state, "hard")
    return _weighted_reward(
        breakdown,
        {
            "correctness": 0.28,
            "clarity": 0.22,
            "confidence": 0.10,
            "consistency": 0.12,
            "improvement": 0.14,
            "confidence_alignment": 0.06,
            "strategy": 0.08,
        },
    )


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}


def get_grader(task_id: str):
    return GRADERS[task_id]
