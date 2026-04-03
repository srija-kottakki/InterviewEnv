"""
InterviewEnv - A real-world OpenEnv environment for AI interview training.
Trains an AI agent to ace job interviews by detecting hidden evaluation rubrics
and adapting answers in real time.
"""

import random
import json
from typing import Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Typed Models (OpenEnv spec)
# ─────────────────────────────────────────────

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
    info: dict = Field(default_factory=dict)


# ─────────────────────────────────────────────
# Hidden Rubric Definitions
# ─────────────────────────────────────────────

RUBRICS = {
    "easy": {
        "name": "HR Round - Cultural Fit",
        "criteria": ["cultural_fit"],
        "weights": {"cultural_fit": 1.0},
        "keywords": {
            "cultural_fit": ["team", "collaborate", "learn", "grow", "contribute", "values", "mission"]
        },
        "description": "Interviewer is evaluating cultural fit above all else."
    },
    "medium": {
        "name": "Technical Round - Depth & Clarity",
        "criteria": ["depth", "clarity", "honesty"],
        "weights": {"depth": 0.4, "clarity": 0.35, "honesty": 0.25},
        "keywords": {
            "depth": ["specifically", "for example", "because", "resulted in", "measured", "impact"],
            "clarity": ["first", "then", "finally", "structured", "steps", "approach"],
            "honesty": ["i don't know", "i'm still learning", "i would ask", "i'd research", "gap"]
        },
        "description": "Interviewer scores on technical depth, structured clarity, and honest self-awareness."
    },
    "hard": {
        "name": "Stress Interview - Composure & Evidence",
        "criteria": ["composure", "evidence", "pushback_handling"],
        "weights": {"composure": 0.35, "evidence": 0.40, "pushback_handling": 0.25},
        "keywords": {
            "composure": ["understand", "fair point", "however", "i believe", "let me clarify"],
            "evidence": ["specifically", "in my experience", "the result was", "data", "metric", "project"],
            "pushback_handling": ["you raise a good point", "to add", "actually", "let me explain", "the reason"]
        },
        "description": "Interviewer will push back on every answer. Agent must stay composed and defend with evidence."
    }
}

INTERVIEW_SCENARIOS = {
    "easy": {
        "job_title": "Junior Software Engineer",
        "company": "TechCorp",
        "opening": "Hi! Thanks for coming in today. Tell me a little about yourself and why you're excited about TechCorp.",
        "followups": [
            "That's interesting. How do you usually work within a team?",
            "Can you tell me about a time you had to adapt to a new environment?",
            "What does growth mean to you professionally?",
            "Why do you think you'd be a good fit for our culture here?",
        ]
    },
    "medium": {
        "job_title": "Backend Developer",
        "company": "DataSystems",
        "opening": "Let's dive right in. Can you walk me through a technical project you're most proud of?",
        "followups": [
            "Interesting. Can you go deeper on the technical decisions you made?",
            "How would you explain that architecture to a non-technical stakeholder?",
            "What would you do differently if you built it again?",
            "What's an area in your technical skills you're actively improving?",
            "If you didn't know how to solve something, what would your process be?",
        ]
    },
    "hard": {
        "job_title": "Senior Product Engineer",
        "company": "ScaleUp",
        "opening": "I'll be honest — your resume is impressive but we've seen a lot of candidates. Why should we pick you over someone with more experience?",
        "followups": [
            "That sounds generic. Every candidate says that. Give me something specific.",
            "I'm not convinced that project was that impactful. How do you actually measure success?",
            "Our team moves extremely fast. How do I know you won't be a bottleneck?",
            "You've made mistakes before — tell me about a bad one and why it was your fault.",
            "I still think someone with 5 years more experience would outperform you. Convince me otherwise.",
        ]
    }
}


# ─────────────────────────────────────────────
# InterviewEnv Core Class
# ─────────────────────────────────────────────

class InterviewEnv:
    """
    OpenEnv-compliant environment for AI interview training.
    
    The agent plays a job candidate being interviewed.
    The interviewer has a hidden evaluation rubric the agent never sees directly.
    The agent must infer what's being measured from the questions and adapt.
    
    Tasks:
      - easy:   HR round, 1 hidden criterion (cultural fit), 5 turns
      - medium: Technical round, 3 hidden criteria, 8 turns  
      - hard:   Stress interview, 3 criteria + adversarial pushback, 12 turns
    """

    TASK_CONFIG = {
        "easy":   {"max_turns": 5,  "pass_threshold": 0.55},
        "medium": {"max_turns": 8,  "pass_threshold": 0.60},
        "hard":   {"max_turns": 12, "pass_threshold": 0.65},
    }

    def __init__(self, task_id: str = "easy"):
        assert task_id in self.TASK_CONFIG, f"task_id must be one of {list(self.TASK_CONFIG.keys())}"
        self.task_id = task_id
        self._rubric = RUBRICS[task_id]
        self._scenario = INTERVIEW_SCENARIOS[task_id]
        self._config = self.TASK_CONFIG[task_id]

        # Episode state
        self._turn = 0
        self._done = False
        self._history = []
        self._rubric_scores = {c: 0.0 for c in self._rubric["criteria"]}
        self._weak_answer_last_turn = False
        self._recovery_scores = []
        self._followup_index = 0

    def reset(self) -> InterviewObservation:
        """Reset environment to initial state. Returns first interviewer message."""
        self._turn = 0
        self._done = False
        self._history = []
        self._rubric_scores = {c: 0.0 for c in self._rubric["criteria"]}
        self._weak_answer_last_turn = False
        self._recovery_scores = []
        self._followup_index = 0

        opening = self._scenario["opening"]
        self._history.append({"role": "interviewer", "content": opening})

        return InterviewObservation(
            interviewer_message=opening,
            turn=self._turn,
            max_turns=self._config["max_turns"],
            task_id=self.task_id,
            done=False
        )

    def step(self, action: InterviewAction) -> tuple[InterviewObservation, InterviewReward, bool]:
        """
        Process candidate's answer. Returns (observation, reward, done).
        Reward is partial — given every turn, not just at the end.
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        self._turn += 1
        candidate_message = action.message
        self._history.append({"role": "candidate", "content": candidate_message})

        # Score this turn against the hidden rubric
        turn_rubric_score = self._score_rubric(candidate_message)
        turn_specificity = self._score_specificity(candidate_message)

        # Recovery: if last turn was weak and this one is strong
        recovery = 0.0
        if self._weak_answer_last_turn:
            if turn_rubric_score > 0.5:
                recovery = 0.3
                self._recovery_scores.append(recovery)
        
        self._weak_answer_last_turn = turn_rubric_score < 0.3

        # Partial reward this turn
        turn_reward = (
            turn_rubric_score * 0.50 +
            turn_specificity * 0.30 +
            recovery * 0.20
        )
        # Penalize very short/generic answers
        if len(candidate_message.split()) < 15:
            turn_reward *= 0.5
        
        turn_reward = round(min(max(turn_reward, 0.0), 1.0), 4)

        # Check if done
        done = self._turn >= self._config["max_turns"]
        self._done = done

        # Get next interviewer message
        if not done:
            next_msg = self._get_next_question()
        else:
            next_msg = self._closing_message(turn_rubric_score)

        self._history.append({"role": "interviewer", "content": next_msg})

        reward = InterviewReward(
            reward=turn_reward,
            rubric_score=round(turn_rubric_score, 4),
            recovery_score=round(recovery, 4),
            specificity_score=round(turn_specificity, 4),
            info={
                "turn": self._turn,
                "criteria_hit": self._rubric_scores,
                "weak_answer": self._weak_answer_last_turn
            }
        )

        obs = InterviewObservation(
            interviewer_message=next_msg,
            turn=self._turn,
            max_turns=self._config["max_turns"],
            task_id=self.task_id,
            done=done,
            feedback=self._generate_feedback() if done else None
        )

        return obs, reward, done

    def state(self) -> dict:
        """Return current environment state."""
        return {
            "task_id": self.task_id,
            "turn": self._turn,
            "max_turns": self._config["max_turns"],
            "done": self._done,
            "rubric_name": self._rubric["name"],
            "history_length": len(self._history),
            "current_rubric_scores": self._rubric_scores,
            "pass_threshold": self._config["pass_threshold"]
        }

    # ─────────────────────────────────────────
    # Internal scoring helpers
    # ─────────────────────────────────────────

    def _score_rubric(self, text: str) -> float:
        """Score text against hidden rubric criteria. Returns 0.0–1.0."""
        text_lower = text.lower()
        total_score = 0.0

        for criterion, weight in self._rubric["weights"].items():
            keywords = self._rubric["keywords"][criterion]
            hits = sum(1 for kw in keywords if kw in text_lower)
            criterion_score = min(hits / max(len(keywords) * 0.3, 1), 1.0)
            self._rubric_scores[criterion] = max(
                self._rubric_scores[criterion], criterion_score
            )
            total_score += criterion_score * weight

        return round(min(total_score, 1.0), 4)

    def _score_specificity(self, text: str) -> float:
        """Reward concrete, specific answers over generic ones."""
        text_lower = text.lower()
        specificity_markers = [
            "for example", "specifically", "in my project", "i built",
            "the result", "i measured", "we achieved", "concretely",
            "in that case", "at that time", "what i did was"
        ]
        hits = sum(1 for m in specificity_markers if m in text_lower)
        word_count = len(text.split())
        length_bonus = min(word_count / 80, 0.3)  # longer thoughtful answers
        return round(min(hits * 0.25 + length_bonus, 1.0), 4)

    def _get_next_question(self) -> str:
        """Get next interviewer question based on turn."""
        followups = self._scenario["followups"]
        if self._followup_index < len(followups):
            q = followups[self._followup_index]
            self._followup_index += 1
            return q
        # If we run out of scripted questions, use a generic probe
        probes = [
            "Can you expand on that with a specific example?",
            "That's interesting — what was the measurable outcome?",
            "How would you apply that here at our company?",
        ]
        return random.choice(probes)

    def _closing_message(self, last_score: float) -> str:
        """Closing message from interviewer."""
        if last_score > 0.6:
            return "Thank you — that was a strong interview. We'll be in touch soon."
        elif last_score > 0.35:
            return "Thanks for your time. We have a few more candidates to see."
        else:
            return "Thanks for coming in. We'll let you know our decision."

    def _generate_feedback(self) -> str:
        """End-of-episode feedback based on rubric performance."""
        lines = ["Interview complete. Here's your breakdown:"]
        for criterion, score in self._rubric_scores.items():
            grade = "Strong" if score > 0.6 else ("Developing" if score > 0.3 else "Needs work")
            lines.append(f"  {criterion.replace('_', ' ').title()}: {grade} ({score:.2f})")
        recovery_avg = sum(self._recovery_scores) / max(len(self._recovery_scores), 1)
        lines.append(f"  Recovery ability: {recovery_avg:.2f}")
        return "\n".join(lines)


# ─────────────────────────────────────────────
# Task Graders (OpenEnv spec — 0.0 to 1.0)
# ─────────────────────────────────────────────

def grade_easy(env: InterviewEnv) -> float:
    """
    Easy task grader: HR Round.
    Scores cultural fit detection and answer quality.
    """
    if not env._done:
        return 0.0
    
    cultural_fit_score = env._rubric_scores.get("cultural_fit", 0.0)
    avg_specificity = sum(
        env._score_specificity(h["content"])
        for h in env._history if h["role"] == "candidate"
    ) / max(len([h for h in env._history if h["role"] == "candidate"]), 1)

    final = cultural_fit_score * 0.7 + avg_specificity * 0.3
    return round(min(final, 1.0), 4)


def grade_medium(env: InterviewEnv) -> float:
    """
    Medium task grader: Technical Round.
    Scores depth, clarity, and honesty detection.
    """
    if not env._done:
        return 0.0

    depth = env._rubric_scores.get("depth", 0.0)
    clarity = env._rubric_scores.get("clarity", 0.0)
    honesty = env._rubric_scores.get("honesty", 0.0)

    candidate_msgs = [h["content"] for h in env._history if h["role"] == "candidate"]
    avg_specificity = sum(env._score_specificity(m) for m in candidate_msgs) / max(len(candidate_msgs), 1)
    recovery = sum(env._recovery_scores) / max(len(env._recovery_scores), 1) if env._recovery_scores else 0.0

    final = (
        depth * 0.30 +
        clarity * 0.25 +
        honesty * 0.20 +
        avg_specificity * 0.15 +
        recovery * 0.10
    )
    return round(min(final, 1.0), 4)


def grade_hard(env: InterviewEnv) -> float:
    """
    Hard task grader: Stress Interview.
    Scores composure, evidence quality, and pushback handling.
    """
    if not env._done:
        return 0.0

    composure = env._rubric_scores.get("composure", 0.0)
    evidence = env._rubric_scores.get("evidence", 0.0)
    pushback = env._rubric_scores.get("pushback_handling", 0.0)

    candidate_msgs = [h["content"] for h in env._history if h["role"] == "candidate"]
    avg_specificity = sum(env._score_specificity(m) for m in candidate_msgs) / max(len(candidate_msgs), 1)
    recovery = sum(env._recovery_scores) / max(len(env._recovery_scores), 1) if env._recovery_scores else 0.0

    # Penalise very short answers in stress interview (collapsing under pressure)
    short_answers = sum(1 for m in candidate_msgs if len(m.split()) < 20)
    collapse_penalty = short_answers * 0.05

    final = (
        composure * 0.30 +
        evidence * 0.35 +
        pushback * 0.20 +
        avg_specificity * 0.10 +
        recovery * 0.05 -
        collapse_penalty
    )
    return round(min(max(final, 0.0), 1.0), 4)


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}


def get_grader(task_id: str):
    return GRADERS[task_id]
