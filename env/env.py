from __future__ import annotations

from env.graders import get_grader
from env.models import InterviewAction, InterviewState
from env.tasks import get_task


class InterviewEnv:
    def __init__(self) -> None:
        self._task_id = "easy"
        self._task = get_task(self._task_id)
        self._turn = 0
        self._done = False
        self._prompt = self._task["opening_prompt"]
        self._history: list[dict[str, str]] = []

    def reset(self, task_id: str = "easy") -> tuple[InterviewState, dict]:
        self._task_id = task_id
        self._task = get_task(task_id)
        self._turn = 0
        self._done = False
        self._prompt = self._task["opening_prompt"]
        self._history = [{"role": "interviewer", "content": self._prompt}]
        return self.state(), self._info()

    def step(self, action: InterviewAction) -> tuple[InterviewState, float, bool, dict]:
        if self._done:
            return self.state(), 0.0, True, {"error": "episode_done"}

        answer = action.text()
        self._history.append({"role": "agent", "content": answer})
        reward = get_grader(self._task_id)(answer, self.state().model_dump())

        self._turn += 1
        self._done = self._turn >= self._task["max_turns"]

        if self._done:
            self._prompt = "Interview complete."
        else:
            followups = self._task["followup_prompts"]
            next_index = min(self._turn - 1, len(followups) - 1)
            self._prompt = followups[next_index]

        self._history.append({"role": "interviewer", "content": self._prompt})
        info = self._info()
        info["last_score"] = reward
        return self.state(), reward, self._done, info

    def state(self) -> InterviewState:
        return InterviewState(
            task_id=self._task_id,
            difficulty=self._task["difficulty"],
            turn=self._turn,
            max_turns=self._task["max_turns"],
            prompt=self._prompt,
            history=list(self._history),
            done=self._done,
        )

    def _info(self) -> dict:
        return {
            "task_id": self._task_id,
            "task_name": self._task["name"],
            "difficulty": self._task["difficulty"],
            "pass_threshold": self._task["pass_threshold"],
            "grader": self._task["grader"],
        }
