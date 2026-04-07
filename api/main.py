from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from env.env import InterviewEnv
from env.tasks import TASKS
from models import ActionModel, MetadataModel, ResetRequest, StateModel, StepResponseModel


BASE_DIR = Path(__file__).resolve().parents[1]
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


@app.get("/metadata", response_model=MetadataModel)
def metadata() -> MetadataModel:
    return MetadataModel(
        env_id="InterviewEnv",
        version="1.0.0",
        authors=["Kottakki Sai Srija"],
        description="OpenEnv Round 1 interview-answer environment with deterministic typed models and graders.",
        action_schema=ActionModel.model_json_schema(),
        observation_schema=StepResponseModel.model_json_schema()["properties"]["observation"],
        state_schema=StateModel.model_json_schema(),
        tasks=[dict(task) for task in TASKS.values()],
        graders={task_id: task["grader"] for task_id, task in TASKS.items()},
        api={
            "reset": "GET /reset?task_id=easy or POST /reset",
            "step": "POST /step",
            "state": "GET /state",
            "metadata": "GET /metadata",
        },
    )


@app.get("/reset", response_model=StateModel)
def reset_get(task_id: str = "easy") -> StateModel:
    return _reset(task_id)


@app.post("/reset", response_model=StateModel)
def reset_post(request: Optional[ResetRequest] = None) -> StateModel:
    task_id = request.task_id if request else "easy"
    return _reset(task_id)


def _reset(task_id: str) -> StateModel:
    if task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"task_id must be one of {list(TASKS)}")
    return ENV.reset(task_id)


@app.post("/step", response_model=StepResponseModel)
def step(action: ActionModel) -> StepResponseModel:
    observation, reward, done, info = ENV.step(action)
    return StepResponseModel(observation=observation, reward=reward, done=done, info=info)


@app.get("/state", response_model=StateModel)
def state() -> StateModel:
    return ENV.state()
