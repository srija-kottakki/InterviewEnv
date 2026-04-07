from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


TaskId = Literal["easy", "medium", "hard"]
AnswerStrategy = Literal["direct", "detailed", "structured", "concise", "default", "clarify", "skip"]
Tone = Literal["neutral", "confident", "collaborative", "defensive"]


class ActionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(default="", description="Candidate answer submitted by the agent.")
    message: str = Field(default="", description="Backward-compatible alias for answer.")
    answer_strategy: AnswerStrategy = Field(
        default="detailed",
        description="RL action choice controlling how the candidate approaches the answer.",
    )
    confidence_level: int = Field(default=3, ge=1, le=5, description="Self-reported confidence from 1 to 5.")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Backward-compatible continuous confidence value from 0.0 to 1.0.",
    )
    strategy: AnswerStrategy = Field(
        default="default",
        description="Backward-compatible strategy alias; mapped to answer_strategy when provided.",
    )
    tone: Tone = Field(default="neutral", description="Candidate delivery tone.")

    def text(self) -> str:
        return (self.answer or self.message).strip()

    def normalized_strategy(self) -> AnswerStrategy:
        if self.strategy != "default":
            return self.strategy
        return self.answer_strategy

    def normalized_confidence(self) -> float:
        return max(self.confidence, self.confidence_level / 5.0)


class ObservationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: TaskId
    difficulty: TaskId
    current_difficulty: int
    turn: int
    max_turns: int
    prompt: str
    current_question: str
    question: str
    done: bool
    last_answer: Optional[str] = None
    quality_label: Optional[Literal["poor", "avg", "good"]] = None
    behavioral_feedback: dict[str, object] = Field(default_factory=dict)
    follow_up_question: Optional[str] = None
    adaptive_reason: str = ""
    stress_level: float = 0.0
    adaptivity_factor: float = 0.0
    score_trend: Literal["flat", "improving", "declining"] = "flat"
    reward_breakdown: dict[str, float] = Field(default_factory=dict)
    performance_history: list[dict[str, object]] = Field(default_factory=list)
    last_action: dict[str, object] = Field(default_factory=dict)
    learning_metrics: dict[str, object] = Field(default_factory=dict)


class StateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: TaskId
    difficulty: TaskId
    current_difficulty: int
    turn: int
    max_turns: int
    prompt: str
    current_question: str
    question: str
    done: bool
    history: list[dict[str, str]]
    qa_history: list[dict[str, object]]
    question_history: list[str]
    resume_text: str = ""
    parsed_resume_data: dict[str, object] = Field(default_factory=dict)
    last_feedback: dict[str, object] = Field(default_factory=dict)
    performance_history: list[dict[str, object]] = Field(default_factory=list)
    score_history: list[float] = Field(default_factory=list)
    score_trend: Literal["flat", "improving", "declining"] = "flat"
    stress_level: float = 0.0
    adaptivity_factor: float = 0.0
    reward_breakdown: dict[str, float] = Field(default_factory=dict)
    last_action: dict[str, object] = Field(default_factory=dict)
    learning_metrics: dict[str, object] = Field(default_factory=dict)
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
