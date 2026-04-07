from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(default="easy", description="Task id to start: easy, medium, or hard.")


class InterviewAction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str = Field(default="", description="Candidate answer for the current interview prompt.")
    answer: Optional[str] = Field(default=None, description="Alias accepted by some validators for candidate answer.")

    def text(self) -> str:
        return (self.answer if self.answer is not None else self.message).strip()


class InterviewState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    difficulty: str
    turn: int
    max_turns: int
    prompt: str
    history: list[dict[str, str]]
    done: bool
