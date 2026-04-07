from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from env.env import InterviewEnv
from env.tasks import TASKS
from models import Action, Metadata, ResetRequest, ResetResponse, StateResponse, StepResponse


BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"

app = FastAPI(title="InterviewEnv", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")

ENV = InterviewEnv()


@app.get("/")
def root():
    return FileResponse(UI_DIR / "index.html")


@app.get("/metadata", response_model=Metadata)
def metadata():
    return Metadata(
        name="InterviewEnv",
        version="1.0.0",
        description="OpenEnv Round 1 interview-answer environment with deterministic graders.",
        tasks=[dict(task) for task in TASKS.values()],
        action_model="models.Action",
        observation_model="models.Observation",
        endpoints={
            "reset": "GET /reset?task_id=easy or POST /reset",
            "step": "POST /step",
            "state": "GET /state",
            "metadata": "GET /metadata",
        },
        reward={
            "type": "float",
            "range": [0.0, 1.0],
            "definition": "reward equals deterministic grader score for the latest action",
        },
    )


@app.get("/reset", response_model=ResetResponse)
def reset_get(task_id: str = "easy"):
    return _reset(task_id)


@app.post("/reset", response_model=ResetResponse)
def reset_post(request: Optional[ResetRequest] = None):
    task_id = request.task_id if request else "easy"
    return _reset(task_id)


def _reset(task_id: str) -> ResetResponse:
    if task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"task_id must be one of {list(TASKS)}")
    state, info = ENV.reset(task_id)
    return ResetResponse(state=state, info=info)


@app.post("/step", response_model=StepResponse)
def step(action: Action):
    state, reward, done, info = ENV.step(action)
    return StepResponse(state=state, reward=reward, done=done, info=info)


@app.get("/state", response_model=StateResponse)
def state():
    return StateResponse(state=ENV.state())
