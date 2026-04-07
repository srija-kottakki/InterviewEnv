from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


TaskId = Literal["easy", "medium", "hard"]


class ActionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., description="Candidate answer submitted by the agent.")


class ObservationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: TaskId
    difficulty: TaskId
    current_difficulty: int
    turn: int
    max_turns: int
    prompt: str
    current_question: str
    done: bool
    last_answer: Optional[str] = None
    quality_label: Optional[Literal["poor", "avg", "good"]] = None
    behavioral_feedback: dict[str, object] = Field(default_factory=dict)
    adaptive_reason: str = ""


class StateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: TaskId
    difficulty: TaskId
    current_difficulty: int
    turn: int
    max_turns: int
    prompt: str
    current_question: str
    done: bool
    history: list[dict[str, str]]
    qa_history: list[dict[str, str]]
    question_history: list[str]
    score: float = 0.0
    success: bool = False
    quality_label: Optional[Literal["poor", "avg", "good"]] = None
    behavioral_feedback: dict[str, object] = Field(default_factory=dict)
    adaptive_reason: str = ""


class MetadataModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env_id: str
    version: str
    authors: list[str]
    description: str
    action_schema: dict
    observation_schema: dict
    state_schema: dict
    tasks: list[dict]
    graders: dict[str, str]
    api: dict[str, str]


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: TaskId = "easy"


class StepResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation: ObservationModel
    reward: float
    done: bool
    info: dict


# Backward-compatible aliases for earlier local imports.
Action = ActionModel
Observation = ObservationModel
InterviewAction = ActionModel
InterviewState = StateModel
Metadata = MetadataModel
