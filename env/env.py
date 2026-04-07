from __future__ import annotations

from graders import classify_quality, get_grader
from models import ActionModel, ObservationModel, StateModel

from env.tasks import get_task


class InterviewEnv:
    """Deterministic OpenEnv interview environment."""

    def __init__(self) -> None:
        self._task_id = "easy"
        self._task = get_task(self._task_id)
        self._turn = 0
        self._done = False
        self._score = 0.0
        self._success = False
        self._prompt = self._task["opening_prompt"]
        self._history: list[dict[str, str]] = []
        self._quality_label: str | None = None
        self._last_answer: str | None = None

    def reset(self, task_id: str = "easy") -> StateModel:
        self._task_id = task_id
        self._task = get_task(task_id)
        self._turn = 0
        self._done = False
        self._score = 0.0
        self._success = False
        self._prompt = self._task["opening_prompt"]
        self._history = [{"role": "interviewer", "content": self._prompt}]
        self._quality_label = None
        self._last_answer = None
        return self.state()

    def step(self, action: ActionModel) -> tuple[ObservationModel, float, bool, dict]:
        if self._done:
            return self.observation(), 0.0, True, self._info(extra={"error": "episode_done"})

        answer = action.message.strip()
        self._last_answer = answer
        self._history.append({"role": "agent", "content": answer})

        reward = get_grader(self._task_id)(answer, self.state().model_dump())
        self._score = reward
        self._success = reward >= self._task["pass_threshold"]
        self._quality_label = classify_quality(answer) if self._task_id == "medium" else None

        self._turn += 1
        self._done = self._success or self._turn >= self._task["max_turns"]
        self._prompt = "Interview complete." if self._done else self._next_prompt()
        self._history.append({"role": "interviewer", "content": self._prompt})

        return self.observation(), reward, self._done, self._info()

    def state(self) -> StateModel:
        return StateModel(
            task_id=self._task_id,
            difficulty=self._task["difficulty"],
            turn=self._turn,
            max_turns=self._task["max_turns"],
            prompt=self._prompt,
            done=self._done,
            history=list(self._history),
            score=self._score,
            success=self._success,
            quality_label=self._quality_label,
        )

    def observation(self) -> ObservationModel:
        return ObservationModel(
            task_id=self._task_id,
            difficulty=self._task["difficulty"],
            turn=self._turn,
            max_turns=self._task["max_turns"],
            prompt=self._prompt,
            done=self._done,
            last_answer=self._last_answer,
            quality_label=self._quality_label,
        )

    def _next_prompt(self) -> str:
        followups = self._task["followup_prompts"]
        index = min(max(self._turn - 1, 0), len(followups) - 1)
        return followups[index]

    def _info(self, extra: dict | None = None) -> dict:
        info = {
            "task_id": self._task_id,
            "task_name": self._task["name"],
            "difficulty": self._task["difficulty"],
            "pass_threshold": self._task["pass_threshold"],
            "grader": self._task["grader"],
            "score": self._score,
            "success": self._success,
        }
        if self._quality_label is not None:
            info["quality_label"] = self._quality_label
        if extra:
            info.update(extra)
        return info
