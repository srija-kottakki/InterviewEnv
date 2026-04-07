from __future__ import annotations


TASKS: dict[str, dict] = {
    "easy": {
        "id": "easy",
        "name": "Basic interview question answering",
        "difficulty": "easy",
        "description": "Answer a single introductory interview question with relevant details.",
        "max_turns": 2,
        "pass_threshold": 0.55,
        "grader": "grade_easy",
        "opening_prompt": "Tell me about yourself and why you are interested in this role.",
        "followup_prompts": [
            "What is one strength you would bring to this team?",
        ],
    },
    "medium": {
        "id": "medium",
        "name": "Multi-turn follow-up reasoning",
        "difficulty": "medium",
        "description": "Answer follow-up interview questions with structured reasoning and adaptation.",
        "max_turns": 3,
        "pass_threshold": 0.62,
        "grader": "grade_medium",
        "opening_prompt": "Walk me through a technical or academic project you are proud of.",
        "followup_prompts": [
            "Why did you choose that approach, and what tradeoffs did you consider?",
            "What would you improve if you had to do the project again?",
        ],
    },
    "hard": {
        "id": "hard",
        "name": "Behavioral STAR-format interview simulation",
        "difficulty": "hard",
        "description": "Use situation, task, action, and result structure for behavioral interview answers.",
        "max_turns": 4,
        "pass_threshold": 0.70,
        "grader": "grade_hard",
        "opening_prompt": "Tell me about a time you handled a difficult challenge or conflict.",
        "followup_prompts": [
            "What exactly was your responsibility in that situation?",
            "What action did you personally take?",
            "What was the result, and what did you learn?",
        ],
    },
}


def get_task(task_id: str) -> dict:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task_id '{task_id}'. Expected one of {list(TASKS)}.")
    return TASKS[task_id]
