from __future__ import annotations


TASKS: dict[str, dict] = {
    "easy": {
        "id": "easy",
        "name": "Keyword detection in an interview answer",
        "difficulty": "easy",
        "description": "Detect whether the answer includes role-relevant interview keywords.",
        "max_turns": 2,
        "pass_threshold": 0.55,
        "grader": "graders.grade_easy",
        "opening_prompt": "Answer this interview question: why are you interested in this role?",
        "followup_prompts": [
            "Add one specific experience, project, or skill that supports your interest.",
        ],
    },
    "medium": {
        "id": "medium",
        "name": "Classify answer quality",
        "difficulty": "medium",
        "description": "Classify interview answer quality as poor, average, or good using structure and specificity.",
        "max_turns": 3,
        "pass_threshold": 0.65,
        "grader": "graders.grade_medium",
        "opening_prompt": "Describe a technical or academic project and explain why your approach was effective.",
        "followup_prompts": [
            "Explain one tradeoff or constraint you considered.",
            "What would improve the answer from average to good?",
        ],
    },
    "hard": {
        "id": "hard",
        "name": "Open-ended behavioral rubric evaluation",
        "difficulty": "hard",
        "description": "Evaluate a behavioral interview answer on STAR structure, evidence, impact, and reflection.",
        "max_turns": 4,
        "pass_threshold": 0.72,
        "grader": "graders.grade_hard",
        "opening_prompt": "Tell me about a time you handled a difficult challenge or conflict using STAR format.",
        "followup_prompts": [
            "Clarify the situation and your responsibility.",
            "What action did you personally take?",
            "What was the measurable result and what did you learn?",
        ],
    },
}


def get_task(task_id: str) -> dict:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task_id '{task_id}'. Expected one of {list(TASKS)}.")
    return TASKS[task_id]
