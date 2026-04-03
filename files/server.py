"""
server.py - FastAPI server exposing OpenEnv API endpoints.
Endpoints: POST /reset, POST /step, GET /state
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from environment import InterviewEnv, InterviewAction, InterviewObservation, InterviewReward

app = FastAPI(
    title="InterviewEnv",
    description="OpenEnv environment for AI interview training",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global env instance (one session at a time for HF Spaces demo)
_env: InterviewEnv = None


@app.get("/")
def root():
    return {
        "name": "InterviewEnv",
        "version": "1.0.0",
        "description": "Train AI to ace job interviews by detecting hidden evaluation rubrics",
        "tasks": ["easy", "medium", "hard"],
        "endpoints": ["/reset", "/step", "/state"]
    }


@app.get("/health")
def health():
    return {"status": "ok"}


class ResetRequest(BaseModel_):
    task_id: str = "easy"

from pydantic import BaseModel as BaseModel_

class ResetRequest(BaseModel_):
    task_id: str = "easy"

@app.post("/reset")
def reset(request: ResetRequest = None):
    global _env
    task_id = (request.task_id if request else "easy")
    if task_id not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail=f"task_id must be easy, medium, or hard")
    
    _env = InterviewEnv(task_id=task_id)
    obs = _env.reset()
    return obs.model_dump()


@app.post("/step")
def step(action: InterviewAction):
    global _env
    if _env is None:
        raise HTTPException(status_code=400, detail="Call /reset first")
    if _env._done:
        raise HTTPException(status_code=400, detail="Episode done. Call /reset to start a new one.")
    
    obs, reward, done = _env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done
    }


@app.get("/state")
def state():
    global _env
    if _env is None:
        raise HTTPException(status_code=400, detail="Call /reset first")
    return _env.state()


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"id": "easy",   "name": "HR Round — Cultural Fit",          "max_turns": 5},
            {"id": "medium", "name": "Technical Round — Depth & Clarity", "max_turns": 8},
            {"id": "hard",   "name": "Stress Interview — Composure",      "max_turns": 12},
        ]
    }
