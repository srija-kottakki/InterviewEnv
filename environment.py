"""
InterviewEnv - A real-world OpenEnv environment for AI interview training.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class InterviewAction(BaseModel):
    message: str = Field(..., description="The candidate's response to the interviewer")


class InterviewObservation(BaseModel):
    interviewer_message: str = Field(..., description="What the interviewer just said")
    turn: int = Field(..., description="Current turn number")
    max_turns: int = Field(..., description="Maximum turns allowed")
    task_id: str = Field(..., description="Which task is active")
    done: bool = Field(default=False, description="Whether the episode is over")
    feedback: Optional[str] = Field(default=None, description="End-of-episode feedback")


class InterviewReward(BaseModel):
    reward: float = Field(..., description="Reward for this step (0.0 to 1.0)")
    rubric_score: float = Field(..., description="How well hidden rubric criteria were met")
    recovery_score: float = Field(..., description="Recovery after weak answers")
    specificity_score: float = Field(..., description="How specific and concrete the answers were")
    info: dict = Field(default_factory=dict, description="Auxiliary debugging information")


TASKS = {
    "easy": {
        "name": "HR Round - Cultural Fit",
        "description": "Detect that the interviewer values cultural fit and answer accordingly.",
        "max_turns": 5,
        "pass_threshold": 0.55,
        "difficulty": "easy",
    },
    "medium": {
        "name": "Technical Round - Depth, Clarity & Honesty",
        "description": "Balance technical depth, clear structure, and honest self-awareness.",
        "max_turns": 8,
        "pass_threshold": 0.60,
        "difficulty": "medium",
    },
    "hard": {
        "name": "Stress Interview - Composure & Evidence",
        "description": "Stay composed under pushback and defend claims with evidence.",
        "max_turns": 12,
        "pass_threshold": 0.65,
        "difficulty": "hard",
    },
}


RUBRICS = {
    "easy": {
        "criteria": ["cultural_fit"],
        "weights": {"cultural_fit": 1.0},
        "keywords": {
            "cultural_fit": ["team", "collaborate", "learn", "grow", "contribute", "values", "mission"]
        },
    },
    "medium": {
        "criteria": ["depth", "clarity", "honesty"],
        "weights": {"depth": 0.40, "clarity": 0.35, "honesty": 0.25},
        "keywords": {
            "depth": ["specifically", "for example", "because", "resulted in", "measured", "impact"],
            "clarity": ["first", "then", "finally", "structured", "steps", "approach"],
            "honesty": ["i don't know", "i am still learning", "i would ask", "i would research", "gap"],
        },
    },
    "hard": {
        "criteria": ["composure", "evidence", "pushback_handling"],
        "weights": {"composure": 0.35, "evidence": 0.40, "pushback_handling": 0.25},
        "keywords": {
            "composure": ["understand", "fair point", "however", "i believe", "let me clarify"],
            "evidence": ["specifically", "in my experience", "the result was", "data", "metric", "project"],
            "pushback_handling": ["you raise a good point", "to add", "actually", "let me explain", "the reason"],
        },
    },
}


INTERVIEW_SCENARIOS = {
    "easy": {
        "opening": "Hi! Thanks for coming in today. Tell me a little about yourself and why you are excited about TechCorp.",
        "followups": [
            "That is interesting. How do you usually work within a team?",
            "Can you tell me about a time you had to adapt to a new environment?",
            "What does growth mean to you professionally?",
            "Why do you think you would be a good fit for our culture here?",
        ],
    },
    "medium": {
        "opening": "Let us dive right in. Can you walk me through a technical project you are most proud of?",
        "followups": [
            "Interesting. Can you go deeper on the technical decisions you made?",
            "How would you explain that architecture to a non-technical stakeholder?",
            "What would you do differently if you built it again?",
            "What is an area in your technical skills you are actively improving?",
            "If you did not know how to solve something, what would your process be?",
        ],
    },
    "hard": {
        "opening": "I will be honest: your resume is impressive but we have seen a lot of candidates. Why should we pick you over someone with more experience?",
        "followups": [
            "That sounds generic. Every candidate says that. Give me something specific.",
            "I am not convinced that project was that impactful. How do you actually measure success?",
            "Our team moves extremely fast. How do I know you will not be a bottleneck?",
            "You have made mistakes before. Tell me about a bad one and why it was your fault.",
            "I still think someone with five years more experience would outperform you. Convince me otherwise.",
        ],
    },
}


GENERIC_PROBES = [
    "Can you expand on that with a specific example?",
    "What was the measurable outcome?",
    "How would you apply that here at our company?",
]


class InterviewEnv:
    """OpenEnv-style interview environment with typed actions and observations."""

    def __init__(self, task_id: str = "easy"):
        if task_id not in TASKS:
            raise ValueError(f"task_id must be one of {list(TASKS)}")

        self.task_id = task_id
        self._config = TASKS[task_id]
        self._rubric = RUBRICS[task_id]
        self._scenario = INTERVIEW_SCENARIOS[task_id]

        self._turn = 0
        self._done = False
        self._history: list[dict] = []
        self._rubric_scores = {criterion: 0.0 for criterion in self._rubric["criteria"]}
        self._weak_answer_last_turn = False
        self._recovery_scores: list[float] = []
        self._followup_index = 0
        self._probe_index = 0

    def reset(self) -> InterviewObservation:
        self._turn = 0
        self._done = False
        self._history = []
        self._rubric_scores = {criterion: 0.0 for criterion in self._rubric["criteria"]}
        self._weak_answer_last_turn = False
        self._recovery_scores = []
        self._followup_index = 0
        self._probe_index = 0

        opening = self._scenario["opening"]
        self._history.append({"role": "interviewer", "content": opening})

        return InterviewObservation(
            interviewer_message=opening,
            turn=0,
            max_turns=self._config["max_turns"],
            task_id=self.task_id,
            done=False,
            feedback=None,
        )

    def step(self, action: InterviewAction) -> tuple[InterviewObservation, InterviewReward, bool]:
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        self._turn += 1
        candidate_message = action.message.strip()
        self._history.append({"role": "candidate", "content": candidate_message})

        turn_rubric_score = self._score_rubric(candidate_message)
        turn_specificity = self._score_specificity(candidate_message)

        confidence = min(len(candidate_message.split()) / 100.0, 1.0)
        perception_gap = abs(confidence - turn_rubric_score)

        recovery = 0.0
        if self._weak_answer_last_turn and turn_rubric_score > 0.5:
            recovery = 0.3
            self._recovery_scores.append(recovery)

        self._weak_answer_last_turn = turn_rubric_score < 0.3

        turn_reward = (
            turn_rubric_score * 0.50
            + turn_specificity * 0.30
            + recovery * 0.20
            - perception_gap * 0.20
        )

        if len(candidate_message.split()) < 15:
            turn_reward *= 0.5

        turn_reward = round(min(max(turn_reward, 0.0), 1.0), 4)

        done = self._turn >= self._config["max_turns"]
        self._done = done
        next_message = self._closing_message(turn_rubric_score) if done else self._get_next_question()
        self._history.append({"role": "interviewer", "content": next_message})

        observation = InterviewObservation(
            interviewer_message=next_message,
            turn=self._turn,
            max_turns=self._config["max_turns"],
            task_id=self.task_id,
            done=done,
            feedback=self._generate_feedback() if done else None,
        )

        reward = InterviewReward(
            reward=turn_reward,
            rubric_score=round(turn_rubric_score, 4),
            recovery_score=round(recovery, 4),
            specificity_score=round(turn_specificity, 4),
            info={
                "turn": self._turn,
                "criteria_hit": dict(self._rubric_scores),
                "weak_answer": self._weak_answer_last_turn,
                "perception_gap": round(perception_gap, 4),
            },
        )

        return observation, reward, done

    def state(self) -> dict:
        return {
            "task_id": self.task_id,
            "turn": self._turn,
            "max_turns": self._config["max_turns"],
            "done": self._done,
            "rubric_name": TASKS[self.task_id]["name"],
            "history_length": len(self._history),
            "current_rubric_scores": dict(self._rubric_scores),
            "pass_threshold": self._config["pass_threshold"],
        }

    def _score_rubric(self, text: str) -> float:
        text_lower = text.lower()
        total_score = 0.0

        for criterion, weight in self._rubric["weights"].items():
            keywords = self._rubric["keywords"][criterion]
            hits = sum(1 for keyword in keywords if keyword in text_lower)
            criterion_score = min(hits / max(len(keywords) * 0.3, 1), 1.0)
            self._rubric_scores[criterion] = max(self._rubric_scores[criterion], criterion_score)
            total_score += criterion_score * weight

        return round(min(total_score, 1.0), 4)

    def _score_specificity(self, text: str) -> float:
        text_lower = text.lower()
        specificity_markers = [
            "for example",
            "specifically",
            "in my project",
            "i built",
            "the result",
            "i measured",
            "we achieved",
            "concretely",
            "in that case",
            "at that time",
            "what i did was",
        ]
        hits = sum(1 for marker in specificity_markers if marker in text_lower)
        length_bonus = min(len(text.split()) / 80.0, 0.3)
        return round(min(hits * 0.25 + length_bonus, 1.0), 4)

    def _get_next_question(self) -> str:
        followups = self._scenario["followups"]
        if self._followup_index < len(followups):
            question = followups[self._followup_index]
            self._followup_index += 1
            return question

        question = GENERIC_PROBES[self._probe_index % len(GENERIC_PROBES)]
        self._probe_index += 1
        return question

    def _closing_message(self, last_score: float) -> str:
        if last_score > 0.6:
            return "Thank you. That was a strong interview. We will be in touch soon."
        if last_score > 0.35:
            return "Thanks for your time. We have a few more candidates to see."
        return "Thanks for coming in. We will let you know our decision."

    def _generate_feedback(self) -> str:
        lines = ["Interview complete. Here is your breakdown:"]
        for criterion, score in self._rubric_scores.items():
            if score > 0.6:
                grade = "Strong"
            elif score > 0.3:
                grade = "Developing"
            else:
                grade = "Needs work"
            lines.append(f"{criterion.replace('_', ' ').title()}: {grade} ({score:.2f})")

        recovery_avg = sum(self._recovery_scores) / len(self._recovery_scores) if self._recovery_scores else 0.0
        lines.append(f"Recovery ability: {recovery_avg:.2f}")

        if any(score < 0.3 for score in self._rubric_scores.values()):
            lines.append("Key insight: answers need more depth, evidence, or clearer adaptation to the rubric.")
        elif self._recovery_scores:
            lines.append("Key insight: you recovered well after weaker turns.")
        else:
            lines.append("Key insight: performance stayed steady across the interview.")

        return "\n".join(lines)


def grade_easy(env: InterviewEnv) -> float:
    if not env._done:
        return 0.0

    candidate_messages = [item["content"] for item in env._history if item["role"] == "candidate"]
    avg_specificity = (
        sum(env._score_specificity(message) for message in candidate_messages) / len(candidate_messages)
        if candidate_messages
        else 0.0
    )
    final_score = env._rubric_scores.get("cultural_fit", 0.0) * 0.70 + avg_specificity * 0.30
    return round(min(max(final_score, 0.0), 1.0), 4)


def grade_medium(env: InterviewEnv) -> float:
    if not env._done:
        return 0.0

    candidate_messages = [item["content"] for item in env._history if item["role"] == "candidate"]
    avg_specificity = (
        sum(env._score_specificity(message) for message in candidate_messages) / len(candidate_messages)
        if candidate_messages
        else 0.0
    )
    recovery = sum(env._recovery_scores) / len(env._recovery_scores) if env._recovery_scores else 0.0

    final_score = (
        env._rubric_scores.get("depth", 0.0) * 0.30
        + env._rubric_scores.get("clarity", 0.0) * 0.25
        + env._rubric_scores.get("honesty", 0.0) * 0.20
        + avg_specificity * 0.15
        + recovery * 0.10
    )
    return round(min(max(final_score, 0.0), 1.0), 4)


def grade_hard(env: InterviewEnv) -> float:
    if not env._done:
        return 0.0

    candidate_messages = [item["content"] for item in env._history if item["role"] == "candidate"]
    avg_specificity = (
        sum(env._score_specificity(message) for message in candidate_messages) / len(candidate_messages)
        if candidate_messages
        else 0.0
    )
    recovery = sum(env._recovery_scores) / len(env._recovery_scores) if env._recovery_scores else 0.0
    collapse_penalty = sum(1 for message in candidate_messages if len(message.split()) < 20) * 0.05

    final_score = (
        env._rubric_scores.get("composure", 0.0) * 0.30
        + env._rubric_scores.get("evidence", 0.0) * 0.35
        + env._rubric_scores.get("pushback_handling", 0.0) * 0.20
        + avg_specificity * 0.10
        + recovery * 0.05
        - collapse_penalty
    )
    return round(min(max(final_score, 0.0), 1.0), 4)


GRADERS = {"easy": grade_easy, "medium": grade_medium, "hard": grade_hard}


def get_grader(task_id: str):
    return GRADERS[task_id]
