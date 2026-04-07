from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from environment import InterviewAction, InterviewEnv, TASKS


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="InterviewEnv", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_env: Optional[InterviewEnv] = None


class ResetRequest(BaseModel):
    task_id: str = "easy"


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/metadata")
def metadata():
    return {
        "name": "InterviewEnv",
        "version": "1.0.0",
        "endpoints": {
            "reset": "GET /reset?task_id=easy or POST /reset",
            "step": "POST /step",
            "state": "GET /state",
            "tasks": "GET /tasks",
            "ui": "GET /ui",
        },
        "tasks": list(TASKS),
    }


@app.get("/ui")
def ui():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api")
def api_root():
    return {"name": "InterviewEnv", "tasks": list(TASKS)}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset")
def reset(request: Optional[ResetRequest] = None):
    task_id = request.task_id if request else "easy"
    return reset_task(task_id)


@app.get("/reset")
def reset_get(task_id: str = "easy"):
    return reset_task(task_id)


def reset_task(task_id: str):
    global _env
    if task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"task_id must be one of {list(TASKS)}")
    _env = InterviewEnv(task_id=task_id)
    observation = _env.reset()
    task = TASKS[task_id]
    return {
        "state": observation.model_dump(),
        "info": {
            "task_id": task_id,
            "task_name": task["name"],
            "difficulty": task["difficulty"],
            "max_turns": task["max_turns"],
            "pass_threshold": task["pass_threshold"],
        },
    }


@app.post("/step")
def step(action: InterviewAction):
    global _env
    if _env is None:
        raise HTTPException(status_code=400, detail="Call /reset first")
    if _env.state().done:
        raise HTTPException(status_code=400, detail="Episode done. Call /reset to start a new episode.")

    observation, reward, done = _env.step(action)
    return {
        "state": observation.model_dump(),
        "reward": reward.reward,
        "done": done,
        "info": {
            "rubric_score": reward.rubric_score,
            "recovery_score": reward.recovery_score,
            "specificity_score": reward.specificity_score,
            **reward.info,
        },
    }


@app.get("/state")
def state():
    global _env
    if _env is None:
        _env = InterviewEnv(task_id="easy")
        _env.reset()
    return _env.state().model_dump()


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
