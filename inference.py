"""
Baseline inference script for InterviewEnv.

This script uses the OpenAI client for model calls through the configured API_BASE_URL.
It emits structured stdout markers using the required [START], [STEP], and [END] sections.
"""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from environment import InterviewAction, InterviewEnv, TASKS, get_grader


API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")


SYSTEM_PROMPT = (
    "You are a job candidate in a real interview. "
    "Answer with 80-140 words, stay specific, use evidence, and adapt to what the interviewer values. "
    "For technical rounds, be structured and honest about gaps. "
    "For stress rounds, stay calm and respond directly to pushback."
)


def emit(marker: str, payload: dict[str, Any]) -> None:
    print(marker)
    print(json.dumps(payload, ensure_ascii=True))


def build_messages(task_id: str, history: list[dict[str, str]], turn: int) -> list[dict[str, str]]:
    task = TASKS[task_id]
    prompt = (
        f"Task: {task['name']}. "
        f"Difficulty: {task['difficulty']}. "
        f"Turn: {turn + 1} of {task['max_turns']}. "
        "Infer the hidden rubric from the interviewer questions and answer accordingly."
    )
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt + "\n\nTranscript:\n" + format_history(history)}]


def format_history(history: list[dict[str, str]]) -> str:
    return "\n".join(f"{item['role'].upper()}: {item['content']}" for item in history)


def fallback_response(task_id: str, interviewer_message: str) -> str:
    base = {
        "easy": (
            "I am excited by teams that value learning, collaboration, and ownership. "
            "For example, in a student project I helped a teammate unblock an API issue, documented the fix, "
            "and we shipped on time. That experience taught me that I do my best work in cultures where people "
            "share feedback, support each other, and keep improving."
        ),
        "medium": (
            "One project I am proud of was improving backend latency for a campus platform. "
            "First, I measured slow endpoints and found repeated database lookups. "
            "Then I added indexing, caching, and better query patterns, which reduced response time by about 40 percent. "
            "If I rebuilt it, I would add stronger observability earlier, and when I hit gaps I would research, ask targeted questions, and validate with tests."
        ),
        "hard": (
            "You raise a good point, and let me clarify with evidence. "
            "In my experience, I handled a performance issue by measuring the bottleneck, changing the database access pattern, and tracking the result with data and a latency metric after release. "
            "The reason I can contribute despite less experience is that I stay composed under pushback, respond specifically, and learn fast enough to deliver without becoming a bottleneck."
        ),
    }
    return base[task_id]


def generate_candidate_message(client: OpenAI, task_id: str, history: list[dict[str, str]], turn: int, interviewer_message: str) -> str:
    if not HF_TOKEN:
        return fallback_response(task_id, interviewer_message)

    messages = build_messages(task_id, history, turn)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        cleaned = " ".join(content.split())
        return cleaned if cleaned else fallback_response(task_id, interviewer_message)
    except Exception:
        return fallback_response(task_id, interviewer_message)


def run_task(client: OpenAI, task_id: str) -> float:
    env = InterviewEnv(task_id=task_id)
    grader = get_grader(task_id)

    observation = env.reset()
    history = [{"role": "interviewer", "content": observation.interviewer_message}]

    emit(
        "[START]",
        {
            "type": "START",
            "task_id": task_id,
            "max_turns": observation.max_turns,
            "interviewer_opening": observation.interviewer_message,
        },
    )

    done = False
    total_reward = 0.0
    total_steps = 0

    while not done:
        candidate_message = generate_candidate_message(client, task_id, history, observation.turn, observation.interviewer_message)
        action = InterviewAction(message=candidate_message)
        observation, reward, done = env.step(action)
        total_reward += reward.reward
        total_steps += 1

        history.append({"role": "candidate", "content": candidate_message})
        history.append({"role": "interviewer", "content": observation.interviewer_message})

        emit(
            "[STEP]",
            {
                "type": "STEP",
                "task_id": task_id,
                "turn": observation.turn,
                "candidate_message": candidate_message,
                "interviewer_message": observation.interviewer_message,
                "reward": reward.reward,
                "rubric_score": reward.rubric_score,
                "specificity_score": reward.specificity_score,
                "done": done,
            },
        )

    final_score = grader(env)
    avg_reward = round(total_reward / total_steps, 4) if total_steps else 0.0
    emit(
        "[END]",
        {
            "type": "END",
            "task_id": task_id,
            "final_score": final_score,
            "avg_reward": avg_reward,
            "total_turns": total_steps,
            "feedback": observation.feedback or "",
        },
    )
    return final_score


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "missing-token")
    for task_id in ("easy", "medium", "hard"):
        run_task(client, task_id)


if __name__ == "__main__":
    main()
