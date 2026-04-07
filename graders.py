from __future__ import annotations


def _contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)


def _word_score(text: str, target_words: int) -> float:
    return min(len(text.split()) / target_words, 1.0)


def _keyword_score(text: str, groups: list[list[str]]) -> float:
    if not groups:
        return 0.0
    return sum(1 for group in groups if _contains_any(text, group)) / len(groups)


def _clamp(score: float) -> float:
    return round(min(max(score, 0.0), 1.0), 4)


def grade_easy(answer: str, state: dict) -> float:
    groups = [
        ["experience", "project", "worked", "built", "learned", "created"],
        ["role", "company", "team", "mission", "interest", "excited"],
        ["strength", "skill", "communication", "collaboration", "ownership", "problem"],
    ]
    score = 0.55 * _keyword_score(answer, groups) + 0.35 * _word_score(answer, 45)
    if _contains_any(answer, ["for example", "specifically", "because"]):
        score += 0.10
    return _clamp(score)


def grade_medium(answer: str, state: dict) -> float:
    groups = [
        ["first", "then", "finally", "step", "approach", "structured"],
        ["because", "tradeoff", "decision", "chose", "reason", "constraint"],
        ["measure", "metric", "result", "impact", "tested", "validated"],
        ["improve", "learned", "different", "next time", "iterate", "feedback"],
    ]
    score = 0.60 * _keyword_score(answer, groups) + 0.25 * _word_score(answer, 65)
    if len(state.get("history", [])) >= 3 and _contains_any(answer, ["as i mentioned", "building on", "to improve", "follow-up"]):
        score += 0.10
    if _contains_any(answer, ["i don't know", "still learning", "would ask", "would research"]):
        score += 0.05
    return _clamp(score)


def grade_hard(answer: str, state: dict) -> float:
    groups = [
        ["situation", "context", "when", "challenge", "conflict"],
        ["task", "responsibility", "goal", "needed", "expected"],
        ["action", "i did", "i worked", "i communicated", "i decided"],
        ["result", "outcome", "impact", "learned", "improved", "resolved"],
        ["specific", "for example", "measured", "feedback", "metric"],
    ]
    score = 0.65 * _keyword_score(answer, groups) + 0.25 * _word_score(answer, 80)
    if _contains_any(answer, ["star", "situation", "task", "action", "result"]):
        score += 0.10
    return _clamp(score)


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}


def get_grader(task_id: str):
    return GRADERS[task_id]
