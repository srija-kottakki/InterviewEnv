from __future__ import annotations

from graders import get_grader, relevance_score
from utils.feedback_analyzer import analyze_behavior


QUESTION_BANK = {
    "easy": [
        "Tell me about yourself and why you are interested in this role.",
        "What is one strength you would bring to this team?",
        "Describe a project you enjoyed working on.",
    ],
    "medium": [
        "Walk me through a technical project decision and the tradeoffs you considered.",
        "How did you measure whether your work was successful?",
        "Explain a technical challenge you solved and what you would improve next time.",
    ],
    "hard": [
        "Tell me about a high-pressure failure using STAR format.",
        "Defend a technical decision with evidence and measurable impact.",
        "Describe a time you influenced a team without formal authority.",
    ],
}


def normalize_difficulty(difficulty: str) -> str:
    value = (difficulty or "easy").strip().lower()
    if value not in QUESTION_BANK:
        return "easy"
    return value


def generate_question(difficulty: str, history: list[dict] | None = None) -> str:
    task_id = normalize_difficulty(difficulty)
    used_questions = {item.get("question") for item in history or []}
    for question in QUESTION_BANK[task_id]:
        if question not in used_questions:
            return question
    return QUESTION_BANK[task_id][len(used_questions) % len(QUESTION_BANK[task_id])]


def evaluate_answer(difficulty: str, question: str, answer: str, history: list[dict] | None = None) -> str:
    task_id = normalize_difficulty(difficulty)
    clean_answer = " ".join((answer or "").split())
    if not clean_answer:
        return (
            "Score: 0/10\n"
            "Strengths: You have not submitted an answer yet.\n"
            "Weakness: The interviewer needs a concrete response to evaluate.\n"
            "Improve by: Give a 3-5 sentence answer with one specific example and result."
        )

    state = {
        "task_id": task_id,
        "current_question": question,
        "question": question,
        "history": history or [],
        "qa_history": history or [],
        "score_history": [item.get("score", 0.0) / 10 for item in history or []],
        "last_action": {
            "answer_strategy": "structured" if _looks_structured(clean_answer) else "detailed",
            "confidence": 0.8 if _looks_confident(clean_answer) else 0.5,
            "confidence_level": 4 if _looks_confident(clean_answer) else 3,
        },
    }

    feedback = analyze_behavior(clean_answer, state)
    relevance = relevance_score(clean_answer, state)
    grader_score = get_grader(task_id)(clean_answer, state)
    final_score = round(min(max((0.65 * grader_score + 0.35 * relevance) * 10, 0), 10))

    strengths = _strengths(feedback, relevance, clean_answer)
    weaknesses = _weaknesses(feedback, relevance, clean_answer)
    improvement = _improvement_tip(task_id, feedback, relevance, clean_answer)

    return (
        f"Score: {final_score}/10\n"
        f"Strengths: {strengths}\n"
        f"Weakness: {weaknesses}\n"
        f"Improve by: {improvement}"
    )


def _looks_structured(answer: str) -> bool:
    lowered = answer.lower()
    markers = ["first", "then", "finally", "situation", "task", "action", "result", "because"]
    return sum(marker in lowered for marker in markers) >= 2


def _looks_confident(answer: str) -> bool:
    lowered = answer.lower()
    confident_terms = ["i led", "i built", "i decided", "i measured", "i improved", "i solved"]
    hedges = ["maybe", "i guess", "sort of", "kind of", "probably"]
    return any(term in lowered for term in confident_terms) and not any(term in lowered for term in hedges)


def _strengths(feedback: dict[str, object], relevance: float, answer: str) -> str:
    strengths = []
    if float(feedback["clarity_score"]) >= 0.65:
        strengths.append("clear structure")
    if float(feedback["confidence_score"]) >= 0.60:
        strengths.append("confident tone")
    if relevance >= 0.55:
        strengths.append("good relevance to the question")
    if len(answer.split()) >= 35:
        strengths.append("enough detail for follow-up discussion")
    return ", ".join(strengths) if strengths else "You gave a starting point that can be developed further."


def _weaknesses(feedback: dict[str, object], relevance: float, answer: str) -> str:
    if relevance < 0.35:
        return "The answer does not connect strongly enough to the interviewer question."
    if float(feedback["clarity_score"]) < 0.55:
        return "The answer needs clearer structure and a more concrete example."
    if float(feedback["confidence_score"]) < 0.50:
        return "The answer sounds cautious; use more ownership language."
    if len(answer.split()) < 25:
        return "The answer is short and may not give the interviewer enough evidence."
    return "Minor improvement: add one measurable result or lesson learned."


def _improvement_tip(task_id: str, feedback: dict[str, object], relevance: float, answer: str) -> str:
    if task_id == "hard":
        return "Use STAR: situation, task, action, result, and one reflection."
    if task_id == "medium":
        return "Name the tradeoff, explain your decision, and include a measurable outcome."
    if relevance < 0.45:
        return "Tie the answer directly back to the role and the question."
    return "Add one specific example and quantify the impact where possible."
