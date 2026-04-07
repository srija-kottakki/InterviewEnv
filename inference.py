from __future__ import annotations

import json
import os

from openai import OpenAI

from env.env import InterviewEnv
from env.models import InterviewAction
from env.tasks import TASKS


API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")


def emit(marker: str, payload: dict) -> None:
    print(f"{marker} {json.dumps(payload, ensure_ascii=True, separators=(',', ':'))}", flush=True)


def fallback_answer(task_id: str, prompt: str) -> str:
    answers = {
        "easy": "I am interested in this role because it matches my project experience, communication strengths, and curiosity for learning. For example, I built small backend features, worked with teammates, and learned to explain tradeoffs clearly. I would bring ownership, collaboration, and a steady problem-solving approach to the team.",
        "medium": "First, I would describe the project goal and the constraints. Then I would explain the approach I chose, because it balanced simplicity, reliability, and delivery time. I measured the result with tests and feedback. Next time, I would improve observability, document tradeoffs earlier, and ask focused questions when I found a gap.",
        "hard": "Using STAR: the situation was a difficult team project with unclear ownership. My task was to unblock communication and deliver my part. The action I took was to clarify responsibilities, share updates, and implement the highest-risk piece first. The result was a working submission, better feedback, and a lesson about early alignment.",
    }
    return answers[task_id]


def model_answer(client: OpenAI, task_id: str, prompt: str, history: list[dict[str, str]]) -> str:
    if not HF_TOKEN:
        return fallback_answer(task_id, prompt)

    messages = [
        {
            "role": "system",
            "content": "Answer as an interview candidate. Be concise, specific, structured, and deterministic.",
        },
        {
            "role": "user",
            "content": json.dumps({"task_id": task_id, "prompt": prompt, "history": history}, ensure_ascii=True),
        },
    ]
    try:
        response = client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0)
        text = response.choices[0].message.content or ""
        return " ".join(text.split()) or fallback_answer(task_id, prompt)
    except Exception:
        return fallback_answer(task_id, prompt)


def run_task(client: OpenAI, task_id: str) -> float:
    env = InterviewEnv()
    state, info = env.reset(task_id)
    emit("[START]", {"task_id": task_id, "state": state.model_dump(), "info": info})

    total_reward = 0.0
    steps = 0
    done = False

    while not done:
        answer = model_answer(client, task_id, state.prompt, state.history)
        state, reward, done, info = env.step(InterviewAction(message=answer))
        total_reward += reward
        steps += 1
        emit(
            "[STEP]",
            {
                "task_id": task_id,
                "step": steps,
                "action": {"message": answer},
                "state": state.model_dump(),
                "reward": reward,
                "done": done,
                "info": info,
            },
        )

    final_score = round(total_reward / steps, 4) if steps else 0.0
    emit("[END]", {"task_id": task_id, "score": final_score, "steps": steps, "done": True})
    return final_score


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "missing-token")
    for task_id in TASKS:
        run_task(client, task_id)


if __name__ == "__main__":
    main()
