from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from env.env import InterviewEnv
from env.models import InterviewAction, ResetRequest
from env.tasks import TASKS


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="InterviewEnv", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
ENV = InterviewEnv()


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/ui")
def ui():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/reset")
def reset_get(task_id: str = "easy"):
    return _reset(task_id)


@app.post("/reset")
def reset_post(request: Optional[ResetRequest] = None):
    task_id = request.task_id if request else "easy"
    return _reset(task_id)


def _reset(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"task_id must be one of {list(TASKS)}")
    state, info = ENV.reset(task_id)
    return {"state": state.model_dump(), "info": info}


@app.post("/step")
def step(action: InterviewAction):
    state, reward, done, info = ENV.step(action)
    return {"state": state.model_dump(), "reward": reward, "done": done, "info": info}


@app.get("/state")
def state():
    return {"state": ENV.state().model_dump()}
