from __future__ import annotations


TASKS: dict[str, dict] = {
    "easy": {
        "id": "easy",
        "name": "Basic Interview Simulation",
        "difficulty": "easy",
        "description": "Simulates a low-pressure interview where the agent answers fundamental questions and builds confidence through early-stage feedback.",
        "max_turns": 3,
        "pass_threshold": 0.78,
        "grader": "graders.grade_easy",
        "opening_prompt": "Answer this interview question: why are you interested in this role?",
        "followup_prompts": [
            "Add one specific experience, project, or skill that supports your interest.",
        ],
    },
    "medium": {
        "id": "medium",
        "name": "Technical Interview Simulation",
        "difficulty": "medium",
        "description": "Agent must provide structured, well-reasoned answers including tradeoffs, clarity, and technical depth across multiple turns.",
        "max_turns": 4,
        "pass_threshold": 0.80,
        "grader": "graders.grade_medium",
        "opening_prompt": "Describe a technical or academic project and explain why your approach was effective.",
        "followup_prompts": [
            "Explain one tradeoff or constraint you considered.",
            "What would improve the answer from average to good?",
        ],
    },
    "hard": {
        "id": "hard",
        "name": "Adaptive Stress Interview",
        "difficulty": "hard",
        "description": "Environment dynamically adapts difficulty based on agent performance, testing consistency, improvement, and ability to handle pressure.",
        "max_turns": 5,
        "pass_threshold": 0.82,
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
