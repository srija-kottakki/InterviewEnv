from __future__ import annotations

from graders import analyze_behavior, classify_quality, get_grader, relevance_score, reward_breakdown
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
        self._resume_text = ""
        self._parsed_resume_data: dict[str, object] = {}
        self._last_follow_up_question: str | None = None
        self._performance_history: list[dict[str, object]] = []
        self._score_history: list[float] = []
        self._score_trend = "flat"
        self._stress_level = 0.0
        self._adaptivity_factor = 0.0
        self._reward_breakdown: dict[str, float] = {}
        self._last_action: dict[str, object] = {}

    def update_resume(self, resume_text: str, parsed_resume_data: dict[str, object]) -> StateModel:
        self._resume_text = resume_text
        self._parsed_resume_data = parsed_resume_data
        if self._turn == 0 and not self._done:
            self._current_question = self._select_question()
            self._history = [{"role": "interviewer", "content": self._current_question}]
            self._question_history = [self._current_question]
            self._adaptive_reason = "Resume uploaded; next question personalized to resume context."
        return self.state()

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
        self._last_follow_up_question = None
        self._performance_history = []
        self._score_history = []
        self._score_trend = "flat"
        self._stress_level = self._initial_stress_level()
        self._adaptivity_factor = 0.0
        self._reward_breakdown = {}
        self._last_action = {}
        return self.state()

    def step(self, action: ActionModel) -> tuple[ObservationModel, float, bool, dict]:
        if self._done:
            return self.observation(), 0.0, True, self._info(extra={"error": "episode_done"})

        previous_question = self._current_question
        answer = action.text()
        self._last_action = action.model_dump()
        self._last_answer = answer
        self._history.append({"role": "agent", "content": answer})
        self._qa_history.append({"question": previous_question, "answer": answer})

        state_dict = self.state().model_dump()
        state_dict["last_action"] = dict(self._last_action)
        self._behavioral_feedback = analyze_behavior(answer, state_dict)
        reward = get_grader(self._task_id)(answer, state_dict)
        self._reward_breakdown = reward_breakdown(answer, state_dict, self._task_id)
        relevance = relevance_score(answer, state_dict)
        self._score = reward
        self._success = reward >= self._task["pass_threshold"]
        self._quality_label = classify_quality(answer) if self._task_id == "medium" else None
        self._score_history.append(reward)
        self._score_trend = self._compute_score_trend()

        old_difficulty = self._current_difficulty
        self._current_difficulty = self._adapt_difficulty(relevance)
        self._stress_level = self._adapt_stress(reward)
        self._adaptivity_factor = round((self._current_difficulty / 3.0 + self._stress_level + reward) / 3.0, 4)
        self._adaptive_reason = self._explain_adaptation(old_difficulty, self._current_difficulty, relevance)
        self._last_follow_up_question = self._generate_follow_up(answer, relevance)
        self._performance_history.append(
            {
                "turn": self._turn + 1,
                "question": previous_question,
                "action": dict(self._last_action),
                "reward": reward,
                "relevance_score": relevance,
                "score_trend": self._score_trend,
                "stress_level": self._stress_level,
                "behavioral_feedback": dict(self._behavioral_feedback),
                "reward_breakdown": dict(self._reward_breakdown),
            }
        )

        self._turn += 1
        self._done = self._success or self._turn >= self._task["max_turns"]
        next_question = self._last_follow_up_question
        if next_question in self._question_history:
            next_question = None
        self._last_follow_up_question = next_question
        self._current_question = "Interview complete." if self._done else next_question or self._select_question()
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
            question=self._current_question,
            done=self._done,
            history=list(self._history),
            qa_history=list(self._qa_history),
            question_history=list(self._question_history),
            resume_text=self._resume_text,
            parsed_resume_data=dict(self._parsed_resume_data),
            last_feedback=dict(self._behavioral_feedback),
            performance_history=list(self._performance_history),
            score_history=list(self._score_history),
            score_trend=self._score_trend,
            stress_level=self._stress_level,
            adaptivity_factor=self._adaptivity_factor,
            reward_breakdown=dict(self._reward_breakdown),
            last_action=dict(self._last_action),
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
            question=self._current_question,
            done=self._done,
            last_answer=self._last_answer,
            quality_label=self._quality_label,
            behavioral_feedback=dict(self._behavioral_feedback),
            follow_up_question=self._last_follow_up_question,
            adaptive_reason=self._adaptive_reason,
            stress_level=self._stress_level,
            adaptivity_factor=self._adaptivity_factor,
            score_trend=self._score_trend,
            reward_breakdown=dict(self._reward_breakdown),
            performance_history=list(self._performance_history),
            last_action=dict(self._last_action),
        )

    def _adapt_difficulty(self, relevance: float) -> int:
        clarity = float(self._behavioral_feedback["clarity_score"])
        confidence = float(self._behavioral_feedback["confidence_score"])
        filler = float(self._behavioral_feedback["filler_score"])
        strategy = self._last_action.get("answer_strategy", "detailed")
        if strategy == "skip":
            return max(self._current_difficulty - 1, 1)
        if strategy == "clarify" and relevance >= 0.55:
            return self._current_difficulty
        if clarity >= 0.70 and confidence >= 0.65 and filler >= 0.75 and relevance >= 0.65:
            return min(self._current_difficulty + 1, 3)
        if clarity < 0.35 or confidence < 0.35 or filler < 0.45 or relevance < 0.35:
            return max(self._current_difficulty - 1, 1)
        return self._current_difficulty

    def _initial_stress_level(self) -> float:
        return {"easy": 0.15, "medium": 0.35, "hard": 0.60}[self._task_id]

    def _adapt_stress(self, reward: float) -> float:
        delta = -0.08 if reward >= 0.70 else 0.10 if reward < 0.45 else 0.02
        if self._task_id == "hard" and self._current_difficulty == 3:
            delta += 0.05
        if self._last_action.get("tone") == "defensive":
            delta += 0.06
        if self._last_action.get("answer_strategy") == "clarify":
            delta -= 0.03
        return round(min(max(self._stress_level + delta, 0.0), 1.0), 4)

    def _compute_score_trend(self) -> str:
        if len(self._score_history) < 2:
            return "flat"
        delta = self._score_history[-1] - self._score_history[-2]
        if delta > 0.04:
            return "improving"
        if delta < -0.04:
            return "declining"
        return "flat"

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
        bucket = self._resume_question_bucket(self._current_difficulty) + QUESTION_BUCKETS[self._current_difficulty]
        asked = set(self._question_history)
        for question in bucket:
            if question not in asked:
                return question
        return bucket[self._turn % len(bucket)]

    def _has_resume_context(self) -> bool:
        if self._resume_text.strip():
            return True
        return any(
            self._parsed_resume_data.get(key)
            for key in ("skills", "projects", "experience", "education", "tools_technologies")
        )

    def _resume_question_bucket(self, level: int) -> list[str]:
        if not self._has_resume_context():
            return []

        data = self._parsed_resume_data
        skills = [str(skill) for skill in data.get("skills", [])]
        projects = [str(project) for project in data.get("projects", [])]
        experience = [str(item) for item in data.get("experience", [])]
        questions = []

        for project in projects[:3]:
            name = project.split(".")[0][:80]
            questions.extend([
                f"Explain the goal of this resume project: {name}.",
                f"What challenge did you face in this project: {name}?",
                f"How would you improve this project now: {name}?",
            ])
        for skill in skills[:5]:
            if skill.lower() == "python":
                questions.extend(["In Python, when would you use a list instead of a tuple?", "Explain decorators in Python with a resume-based example."])
            elif skill.lower() == "sql":
                questions.extend(["Explain SQL JOINs using one of your projects.", "How would you find duplicates in SQL?"])
            elif skill.lower() in {"ml", "machine learning", "tensorflow", "pytorch", "scikit-learn"}:
                questions.extend(["Explain overfitting and how you would detect it.", "Which evaluation metrics would fit your ML project?"])
            elif skill:
                questions.append(f"How did you use {skill} in your resume projects?")
        for item in experience[:3]:
            snippet = item[:90]
            questions.extend([
                f"What were your responsibilities in this experience: {snippet}?",
                f"Describe a challenge you solved during this experience: {snippet}.",
                "How did you collaborate with your team in that role?",
            ])

        behavioral = [
            "Tell me about a difficult problem from your resume experience.",
            "Tell me about a failure connected to your resume and what you learned.",
            "Give a teamwork example connected to your resume.",
        ]
        questions.extend(behavioral)

        if level == 1:
            return questions[::3] or []
        if level == 2:
            return questions[1::2] or questions
        return questions or []

    def _generate_follow_up(self, answer: str, relevance: float) -> str | None:
        lowered = answer.lower()
        if "react" in lowered:
            return "Why React instead of Angular, and how did you optimize performance?"
        if "python" in lowered:
            return "What Python design choice mattered most in that work, and why?"
        if "sql" in lowered:
            return "How did you design the SQL queries or joins for correctness and performance?"
        if "machine learning" in lowered or "model" in lowered or "ml" in lowered:
            return "How did you evaluate the model and handle overfitting or bias?"
        if "team" in lowered or "collaborat" in lowered:
            return "What was your specific contribution to the team outcome?"
        if relevance < 0.45:
            if self._has_resume_context():
                return "Can you connect your answer more directly to the question and your resume?"
            return "Can you connect your answer more directly to the question?"
        return None

    def _info(self, extra: dict | None = None) -> dict:
        info = {
            "task_id": self._task_id,
            "task_name": self._task["name"],
            "difficulty": self._task["difficulty"],
            "current_difficulty": self._current_difficulty,
            "pass_threshold": self._task["pass_threshold"],
            "grader": self._task["grader"],
            "score": self._score,
            "score_trend": self._score_trend,
            "stress_level": self._stress_level,
            "adaptivity_factor": self._adaptivity_factor,
            "reward_breakdown": dict(self._reward_breakdown),
            "success": self._success,
            "behavioral_feedback": dict(self._behavioral_feedback),
            "adaptive_reason": self._adaptive_reason,
            "follow_up_question": self._last_follow_up_question,
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
