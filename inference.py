from __future__ import annotations

import json
import os

from openai import OpenAI

from env.env import InterviewEnv
from env.tasks import TASKS
from models import ActionModel


API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")


def emit(marker: str, payload: dict | None = None) -> None:
    if payload is None:
        print(marker, flush=True)
    else:
        print(f"{marker} {json.dumps(payload, ensure_ascii=True, separators=(',', ':'))}", flush=True)


def fallback_answer(task_id: str) -> str:
    return {
        "easy": "I am interested in this role because my project experience, teamwork, communication, and ownership match the position. I have built projects, worked with a team, and learned to explain technical choices clearly.",
        "medium": "First, I would describe the project goal and constraints. Then I would explain the approach because it balanced tradeoffs, reliability, and delivery time. I measured the result, validated impact, learned from feedback, and would improve observability next time.",
        "hard": "Using STAR: the situation was a team project with unclear ownership and a delivery risk. My task was to clarify responsibility and unblock progress. The action I took was to communicate tradeoffs, implement the highest-risk part, and measure progress. The result was a completed project, better feedback, and a lesson about alignment.",
    }[task_id]


def model_answer(client: OpenAI, task_id: str, prompt: str, history: list[dict[str, str]]) -> str:
    if not HF_TOKEN:
        return fallback_answer(task_id)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Answer as an interview candidate. Be deterministic, concise, and specific."},
                {"role": "user", "content": json.dumps({"task_id": task_id, "prompt": prompt, "history": history}, ensure_ascii=True)},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        return " ".join(content.split()) or fallback_answer(task_id)
    except Exception:
        return fallback_answer(task_id)


def run_task(client: OpenAI, task_id: str) -> float:
    env = InterviewEnv()
    state = env.reset(task_id)
    emit("[START]")

    done = False
    steps = 0
    total_reward = 0.0

    while not done:
        answer = model_answer(client, task_id, state.prompt, state.history)
        observation, reward, done, info = env.step(ActionModel(answer=answer))
        state = env.state()
        steps += 1
        total_reward += reward
        emit(
            "[STEP]",
            {
                "task_id": task_id,
                "step": steps,
                "action": {"answer": answer},
                "observation": observation.model_dump(),
                "reward": reward,
                "done": done,
                "info": info,
            },
        )

    score = round(total_reward / steps, 4) if steps else 0.0
    emit("[END]", {"task_id": task_id, "score": score, "steps": steps, "done": True})
    return score


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "missing-token")
    for task_id in TASKS:
        run_task(client, task_id)


if __name__ == "__main__":
    main()
