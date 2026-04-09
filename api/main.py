from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from env.env import InterviewEnv
from env.tasks import TASKS
from models import ActionModel, MetadataModel, ObservationModel, ResetRequest, StateModel, StepResponseModel
from utils.resume_parser import extract_resume_text, parse_resume_text

app = FastAPI(title="InterviewEnv", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

ENV = InterviewEnv()
BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"

app.mount("/assets", StaticFiles(directory=UI_DIR), name="assets")


@app.get("/")
def root():
    return FileResponse(UI_DIR / "index.html")


@app.get("/api")
def api_root():
    return {
        "env_id": "InterviewEnv",
        "status": "ok",
        "message": "InterviewEnv API is running. Use /metadata for schemas and /docs for interactive API docs.",
    }


@app.get("/health")
def health():
    return {
        "env_id": "InterviewEnv",
        "status": "ok",
        "message": "InterviewEnv API is running. Use /metadata for schemas and /docs for interactive API docs.",
    }


@app.get("/metadata", response_model=MetadataModel)
def metadata() -> MetadataModel:
    return MetadataModel(
        env_id="InterviewEnv",
        version="1.1.0",
        authors=["Kottakki Sai Srija"],
        description="OpenEnv Round 1 adaptive RL-style interview environment with structured actions, trend-aware rewards, resume context, and deterministic graders.",
        action_schema=ActionModel.model_json_schema(),
        observation_schema=ObservationModel.model_json_schema(),
        state_schema=StateModel.model_json_schema(),
        tasks=[dict(task) for task in TASKS.values()],
        graders={task_id: task["grader"] for task_id, task in TASKS.items()},
        api={
            "health": "GET /health",
            "reset": "GET /reset?task_id=easy or POST /reset",
            "step": "POST /step",
            "state": "GET /state",
            "metadata": "GET /metadata",
            "upload_resume": "POST /upload_resume",
        },
    )


@app.post("/upload_resume", response_model=StateModel)
async def upload_resume(request: Request) -> StateModel:
    form = await request.form()
    file = form.get("file")
    if file is None:
        raise HTTPException(status_code=400, detail="Upload a resume file using multipart field 'file'.")
    content = await file.read()
    resume_text = extract_resume_text(file.filename or "resume.txt", content)
    parsed_resume_data = parse_resume_text(resume_text)
    return ENV.update_resume(resume_text=resume_text, parsed_resume_data=parsed_resume_data)


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
