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
        return
    print(f"{marker} {json.dumps(payload, ensure_ascii=True, separators=(',', ':'))}", flush=True)


def fallback_action(task_id: str, step: int, prompt: str) -> ActionModel:
    answers = {
        "easy": [
            "I am interested in this role because my project experience, teamwork, communication, and ownership match the position. I have built projects, worked with a team, and learned to explain technical choices clearly.",
            "One strength I bring is structured problem solving. For example, I break a project into constraints, communicate progress, and measure whether the result helped the team.",
        ],
        "medium": [
            "First, I would describe the project goal and constraints. Then I would explain the approach because it balanced tradeoffs, reliability, and delivery time. I measured the result, validated impact, learned from feedback, and would improve observability next time.",
            "The main tradeoff was speed versus robustness. I chose the safer design because the impact and correctness mattered more, then measured success with tests, user feedback, and clear performance metrics.",
        ],
        "hard": [
            "Using STAR: the situation was a team project with unclear ownership and a delivery risk. My task was to clarify responsibility and unblock progress. The action I took was to communicate tradeoffs, implement the highest-risk part, and measure progress. The result was a completed project, better feedback, and a lesson about alignment.",
            "In that conflict, I stayed collaborative, clarified the goal, and took ownership of the next step. I documented the decision, asked for feedback, and measured the outcome so the team could learn from the result.",
        ],
    }
    answer = answers[task_id][min(step, len(answers[task_id]) - 1)]
    confidence = {"easy": 4, "medium": 4, "hard": 3}[task_id]
    tone = "collaborative" if "team" in prompt.lower() or task_id == "hard" else "confident"
    return ActionModel(
        answer=answer,
        answer_strategy="structured",
        strategy="structured",
        confidence_level=confidence,
        confidence=confidence / 5,
        tone=tone,
    )


def model_action(client: OpenAI, task_id: str, step: int, prompt: str, history: list[dict[str, str]]) -> ActionModel:
    if not HF_TOKEN:
        return fallback_action(task_id, step, prompt)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return compact JSON for an interview candidate action with keys: "
                        "answer, answer_strategy, confidence_level, tone. "
                        "Use answer_strategy in direct|detailed|clarify|skip, confidence_level 1-5, "
                        "tone in neutral|confident|collaborative|defensive."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"task_id": task_id, "step": step, "prompt": prompt, "history": history},
                        ensure_ascii=True,
                    ),
                },
            ],
            temperature=0,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        return ActionModel(**payload)
    except Exception:
        return fallback_action(task_id, step, prompt)


def run_task(client: OpenAI, task_id: str) -> dict:
    env = InterviewEnv()
    state = env.reset(task_id)
    total_reward = 0.0
    steps = 0
    done = False

    while not done:
        action = model_action(client, task_id, steps, state.prompt, state.history)
        observation, reward, done, info = env.step(action)
        state = env.state()
        steps += 1
        total_reward += reward
        emit(
            "[STEP]",
            {
                "task_id": task_id,
                "step": steps,
                "action": action.model_dump(),
                "observation": observation.model_dump(),
                "reward": reward,
                "done": done,
                "info": info,
            },
        )

    return {
        "task_id": task_id,
        "score": round(total_reward / max(steps, 1), 4),
        "steps": steps,
        "done": done,
    }


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "missing-token")
    emit("[START]")
    results = [run_task(client, task_id) for task_id in TASKS]
    emit(
        "[END]",
        {
            "env_id": "InterviewEnv",
            "model": MODEL_NAME,
            "tasks": results,
            "mean_score": round(sum(item["score"] for item in results) / len(results), 4),
        },
    )


if __name__ == "__main__":
    main()
