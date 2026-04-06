from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from environment import InterviewAction, InterviewEnv, TASKS


app = FastAPI(title="InterviewEnv", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_env: Optional[InterviewEnv] = None


class ResetRequest(BaseModel):
    task_id: str = "easy"


@app.get("/")
def root():
    return {"name": "InterviewEnv", "tasks": list(TASKS)}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset")
def reset(request: Optional[ResetRequest] = None):
    global _env
    task_id = request.task_id if request else "easy"
    if task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"task_id must be one of {list(TASKS)}")
    _env = InterviewEnv(task_id=task_id)
    return _env.reset().model_dump()


@app.post("/step")
def step(action: InterviewAction):
    global _env
    if _env is None:
        raise HTTPException(status_code=400, detail="Call /reset first")
    if _env.state()["done"]:
        raise HTTPException(status_code=400, detail="Episode done. Call /reset to start a new episode.")

    observation, reward, done = _env.step(action)
    return {"observation": observation.model_dump(), "reward": reward.model_dump(), "done": done}


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
            {
                "id": task_id,
                "name": task["name"],
                "description": task["description"],
                "max_turns": task["max_turns"],
                "pass_threshold": task["pass_threshold"],
                "difficulty": task["difficulty"],
            }
            for task_id, task in TASKS.items()
        ]
    }
