from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from environment import InterviewEnv, InterviewAction

app = FastAPI(title="InterviewEnv", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_env = None

class ResetRequest(BaseModel):
    task_id: str = "easy"

@app.get("/")
def root():
    return {"name": "InterviewEnv", "tasks": ["easy", "medium", "hard"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/reset")
def reset(request: ResetRequest = None):
    global _env
    task_id = request.task_id if request else "easy"
    if task_id not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail="task_id must be easy, medium, or hard")
    _env = InterviewEnv(task_id=task_id)
    obs = _env.reset()
    return obs.model_dump()

@app.post("/step")
def step(action: InterviewAction):
    global _env
    if _env is None:
        raise HTTPException(status_code=400, detail="Call /reset first")
    if _env._done:
        raise HTTPException(status_code=400, detail="Episode done. Call /reset to start new.")
    obs, reward, done = _env.step(action)
    return {"observation": obs.model_dump(), "reward": reward.model_dump(), "done": done}

@app.get("/state")
def state():
    global _env
    if _env is None:
        raise HTTPException(status_code=400, detail="Call /reset first")
    return _env.state()

@app.get("/tasks")
def list_tasks():
    return {"tasks": [
        {"id": "easy", "name": "HR Round", "max_turns": 5},
        {"id": "medium", "name": "Technical Round", "max_turns": 8},
        {"id": "hard", "name": "Stress Interview", "max_turns": 12},
    ]}
