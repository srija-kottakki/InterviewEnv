from __future__ import annotations

from graders import analyze_behavior, classify_quality, get_grader, relevance_score
from models import ActionModel, ObservationModel, StateModel

from env.tasks import get_task


QUESTION_BUCKETS = {
    1: [
        "Why are you interested in this role?",
        "What is one strength you would bring to this team?",
        "Tell me about a project you enjoyed.",
        "What skill are you currently improving?",
    ],
    2: [
        "Describe a project decision and the tradeoffs you considered.",
        "How did you measure whether your work was successful?",
        "Tell me about feedback you received and how you applied it.",
        "How would you explain your project to a non-technical teammate?",
        "What would you improve if you rebuilt that project?",
    ],
    3: [
        "Tell me about a difficult conflict using STAR format.",
        "Give an example of a high-pressure failure and what you learned.",
        "Defend a technical decision with evidence and measurable impact.",
        "Describe a time you influenced a team without formal authority.",
        "Tell me about a mistake that was your responsibility and how you recovered.",
    ],
}


class InterviewEnv:
    """Adaptive OpenEnv interview environment with deterministic grading."""

    def __init__(self) -> None:
        self._task_id = "easy"
        self._task = get_task(self._task_id)
        self._turn = 0
        self._done = False
        self._score = 0.0
        self._success = False
        self._current_difficulty = 1
        self._current_question = QUESTION_BUCKETS[1][0]
        self._history: list[dict[str, str]] = []
        self._qa_history: list[dict[str, str]] = []
        self._question_history: list[str] = []
        self._behavioral_feedback = self._empty_feedback()
        self._adaptive_reason = "Initial question selected."
        self._quality_label: str | None = None
        self._last_answer: str | None = None

    def reset(self, task_id: str = "easy") -> StateModel:
        self._task_id = task_id
        self._task = get_task(task_id)
        self._turn = 0
        self._done = False
        self._score = 0.0
        self._success = False
        self._current_difficulty = {"easy": 1, "medium": 2, "hard": 3}[task_id]
        self._current_question = self._select_question()
        self._history = [{"role": "interviewer", "content": self._current_question}]
        self._qa_history = []
        self._question_history = [self._current_question]
        self._behavioral_feedback = self._empty_feedback()
        self._adaptive_reason = f"Started at difficulty level {self._current_difficulty} for task '{task_id}'."
        self._quality_label = None
        self._last_answer = None
        return self.state()

    def step(self, action: ActionModel) -> tuple[ObservationModel, float, bool, dict]:
        if self._done:
            return self.observation(), 0.0, True, self._info(extra={"error": "episode_done"})

        previous_question = self._current_question
        answer = action.message.strip()
        self._last_answer = answer
        self._history.append({"role": "agent", "content": answer})
        self._qa_history.append({"question": previous_question, "answer": answer})

        state_dict = self.state().model_dump()
        self._behavioral_feedback = analyze_behavior(answer, state_dict)
        reward = get_grader(self._task_id)(answer, state_dict)
        relevance = relevance_score(answer, state_dict)
        self._score = reward
        self._success = reward >= self._task["pass_threshold"]
        self._quality_label = classify_quality(answer) if self._task_id == "medium" else None

        old_difficulty = self._current_difficulty
        self._current_difficulty = self._adapt_difficulty(relevance)
        self._adaptive_reason = self._explain_adaptation(old_difficulty, self._current_difficulty, relevance)

        self._turn += 1
        self._done = self._success or self._turn >= self._task["max_turns"]
        self._current_question = "Interview complete." if self._done else self._select_question()
        self._history.append({"role": "interviewer", "content": self._current_question})
        self._question_history.append(self._current_question)

        return self.observation(), reward, self._done, self._info(extra={"relevance_score": relevance})

    def state(self) -> StateModel:
        return StateModel(
            task_id=self._task_id,
            difficulty=self._task["difficulty"],
            current_difficulty=self._current_difficulty,
            turn=self._turn,
            max_turns=self._task["max_turns"],
            prompt=self._current_question,
            current_question=self._current_question,
            done=self._done,
            history=list(self._history),
            qa_history=list(self._qa_history),
            question_history=list(self._question_history),
            score=self._score,
            success=self._success,
            quality_label=self._quality_label,
            behavioral_feedback=dict(self._behavioral_feedback),
            adaptive_reason=self._adaptive_reason,
        )

    def observation(self) -> ObservationModel:
        return ObservationModel(
            task_id=self._task_id,
            difficulty=self._task["difficulty"],
            current_difficulty=self._current_difficulty,
            turn=self._turn,
            max_turns=self._task["max_turns"],
            prompt=self._current_question,
            current_question=self._current_question,
            done=self._done,
            last_answer=self._last_answer,
            quality_label=self._quality_label,
            behavioral_feedback=dict(self._behavioral_feedback),
            adaptive_reason=self._adaptive_reason,
        )

    def _adapt_difficulty(self, relevance: float) -> int:
        clarity = float(self._behavioral_feedback["clarity_score"])
        confidence = float(self._behavioral_feedback["confidence_score"])
        filler = float(self._behavioral_feedback["filler_score"])
        if clarity >= 0.70 and confidence >= 0.65 and filler >= 0.75 and relevance >= 0.65:
            return min(self._current_difficulty + 1, 3)
        if clarity < 0.35 or confidence < 0.35 or filler < 0.45 or relevance < 0.35:
            return max(self._current_difficulty - 1, 1)
        return self._current_difficulty

    def _explain_adaptation(self, old_level: int, new_level: int, relevance: float) -> str:
        feedback = self._behavioral_feedback
        summary = (
            f"clarity={feedback['clarity_score']}, confidence={feedback['confidence_score']}, "
            f"filler={feedback['filler_score']}, relevance={relevance}"
        )
        if new_level > old_level:
            return f"Increased difficulty from {old_level} to {new_level} because performance was strong ({summary})."
        if new_level < old_level:
            return f"Decreased difficulty from {old_level} to {new_level} to recover after a weaker answer ({summary})."
        return f"Kept difficulty at {new_level} based on balanced performance ({summary})."

    def _select_question(self) -> str:
        bucket = QUESTION_BUCKETS[self._current_difficulty]
        asked = set(self._question_history)
        for question in bucket:
            if question not in asked:
                return question
        return bucket[self._turn % len(bucket)]

    def _info(self, extra: dict | None = None) -> dict:
        info = {
            "task_id": self._task_id,
            "task_name": self._task["name"],
            "difficulty": self._task["difficulty"],
            "current_difficulty": self._current_difficulty,
            "pass_threshold": self._task["pass_threshold"],
            "grader": self._task["grader"],
            "score": self._score,
            "success": self._success,
            "behavioral_feedback": dict(self._behavioral_feedback),
            "adaptive_reason": self._adaptive_reason,
        }
        if self._quality_label is not None:
            info["quality_label"] = self._quality_label
        if extra:
            info.update(extra)
        return info

    @staticmethod
    def _empty_feedback() -> dict[str, object]:
        return {
            "filler_score": 1.0,
            "confidence_score": 0.0,
            "clarity_score": 0.0,
            "comments": "No answer evaluated yet.",
        }
