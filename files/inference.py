"""
inference.py - InterviewEnv baseline inference script.
Uses OpenAI client. Emits [START], [STEP], [END] structured logs.
Must complete in under 20 minutes on vcpu=2, memory=8gb.
"""

import os
import json
import asyncio
from openai import OpenAI
from environment import InterviewEnv, InterviewAction, get_grader

# ─────────────────────────────────────────────
# Config from environment variables
# ─────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or os.environ.get("OPENAI_API_KEY", "sk-placeholder"),
)

SYSTEM_PROMPT = """You are a job candidate in a real interview. 
Your goal is to give excellent, specific, well-structured answers.
- Always give concrete examples from past experience
- Be honest about gaps but show growth mindset
- Stay composed even under pressure
- Keep answers between 60-120 words unless more depth is needed
- Never be generic. Always be specific."""


def get_model_message(interviewer_msg: str, history: list, turn: int, task_id: str) -> str:
    """Call LLM to generate candidate response."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    for h in history:
        role = "user" if h["role"] == "interviewer" else "assistant"
        messages.append({"role": role, "content": h["content"]})
    
    messages.append({"role": "user", "content": interviewer_msg})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=200,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def run_task(task_id: str) -> dict:
    """Run one full episode for a given task. Returns results dict."""
    env = InterviewEnv(task_id=task_id)
    grader = get_grader(task_id)
    
    obs = env.reset()
    history = [{"role": "interviewer", "content": obs.interviewer_message}]
    
    total_reward = 0.0
    steps = []

    # ── [START] log ──
    print(json.dumps({
        "type": "START",
        "task_id": task_id,
        "max_turns": obs.max_turns,
        "interviewer_opening": obs.interviewer_message
    }))

    done = False
    while not done:
        # Generate candidate response
        candidate_response = get_model_message(
            obs.interviewer_message, history, obs.turn, task_id
        )
        
        action = InterviewAction(message=candidate_response)
        obs, reward, done = env.step(action)
        
        history.append({"role": "candidate", "content": candidate_response})
        history.append({"role": "interviewer", "content": obs.interviewer_message})
        
        total_reward += reward.reward
        steps.append({
            "turn": obs.turn,
            "candidate": candidate_response,
            "interviewer": obs.interviewer_message,
            "reward": reward.reward,
            "rubric_score": reward.rubric_score,
            "specificity_score": reward.specificity_score,
        })

        # ── [STEP] log ──
        print(json.dumps({
            "type": "STEP",
            "task_id": task_id,
            "turn": obs.turn,
            "candidate_message": candidate_response,
            "interviewer_message": obs.interviewer_message,
            "reward": reward.reward,
            "rubric_score": reward.rubric_score,
            "specificity_score": reward.specificity_score,
            "done": done
        }))

    # Final grader score
    final_score = grader(env)
    avg_reward = round(total_reward / max(len(steps), 1), 4)

    # ── [END] log ──
    print(json.dumps({
        "type": "END",
        "task_id": task_id,
        "final_score": final_score,
        "avg_reward": avg_reward,
        "total_turns": len(steps),
        "feedback": obs.feedback or "No feedback generated"
    }))

    return {
        "task_id": task_id,
        "final_score": final_score,
        "avg_reward": avg_reward,
        "steps": steps
    }


def main():
    """Run all 3 tasks and report scores."""
    print(json.dumps({"type": "START", "event": "inference_begin", "model": MODEL_NAME}))

    results = {}
    for task_id in ["easy", "medium", "hard"]:
        print(f"\n{'='*50}")
        print(f"Running task: {task_id.upper()}")
        print('='*50)
        result = run_task(task_id)
        results[task_id] = result["final_score"]

    print(json.dumps({
        "type": "END",
        "event": "inference_complete",
        "scores": results,
        "overall": round(sum(results.values()) / len(results), 4)
    }))

    print("\n── Final Scores ──")
    for task_id, score in results.items():
        print(f"  {task_id:8s}: {score:.4f}")
    print(f"  {'overall':8s}: {round(sum(results.values())/len(results), 4):.4f}")


if __name__ == "__main__":
    main()
