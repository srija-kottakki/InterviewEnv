from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(default="easy", description="Task id to start: easy, medium, or hard.")


class Action(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str = Field(default="", description="Candidate answer for the current interview prompt.")
    answer: Optional[str] = Field(default=None, description="Optional alias for message used by some clients.")

    def text(self) -> str:
        return (self.answer if self.answer is not None else self.message).strip()


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    difficulty: str
    turn: int
    max_turns: int
    prompt: str
    history: list[dict[str, str]]
    done: bool


class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    description: str
    tasks: list[dict]
    action_model: str
    observation_model: str
    endpoints: dict[str, str]
    reward: dict[str, object]


class ResetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Observation
    info: dict


class StepResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Observation
    reward: float
    done: bool
    info: dict


class StateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Observation


InterviewAction = Action
InterviewState = Observation
