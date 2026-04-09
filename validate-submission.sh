#!/usr/bin/env bash
set -euo pipefail

SPACE_URL="${1:-}"
export PYTHONDONTWRITEBYTECODE=1

python3 - <<'PY'
import os
import re
import subprocess
import sys

import yaml
from fastapi.testclient import TestClient

from api.main import app
from env.env import InterviewEnv
from env.tasks import TASKS
from models import ActionModel


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[FAIL] {message}")


manifest = yaml.safe_load(open("openenv.yaml", "r", encoding="utf-8").read())
require(manifest.get("entrypoint"), "openenv.yaml must define entrypoint")
require(manifest.get("inference") == "inference.py", "openenv.yaml must point to root inference.py")
require(manifest.get("launch") == "launch.sh", "openenv.yaml must point to launch.sh")
require(len(manifest.get("tasks", [])) >= 3, "openenv.yaml must define at least 3 tasks")

client = TestClient(app)
for path in ("/", "/health", "/api", "/metadata", "/state", "/reset?task_id=easy"):
    response = client.get(path)
    require(response.status_code == 200, f"{path} returned {response.status_code}")

step_payload = {
    "answer": "I built a project, explained tradeoffs, and measured the result.",
    "answer_strategy": "structured",
    "confidence_level": 4,
    "confidence": 0.8,
    "strategy": "structured",
    "tone": "confident",
}
step_response = client.post("/step", json=step_payload)
require(step_response.status_code == 200, f"/step returned {step_response.status_code}")

env = InterviewEnv()
action = ActionModel(**step_payload)
for task_id in TASKS:
    state = env.reset(task_id)
    require(state.task_id == task_id, f"reset did not activate task {task_id}")
    observation, reward, done, info = env.step(action)
    require(0.0 <= reward <= 1.0, f"reward out of range for task {task_id}")

env_vars = os.environ.copy()
env_vars.setdefault("HF_TOKEN", "")
result = subprocess.run(
    [sys.executable, "inference.py"],
    capture_output=True,
    text=True,
    env=env_vars,
    check=False,
)
require(result.returncode == 0, "inference.py exited with a non-zero code")

lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
start_lines = [line for line in lines if line.startswith("[START]")]
step_lines = [line for line in lines if line.startswith("[STEP]")]
end_lines = [line for line in lines if line.startswith("[END]")]

require(len(start_lines) == len(TASKS), "inference.py must emit one [START] per task")
require(len(end_lines) == len(TASKS), "inference.py must emit one [END] per task")
require(len(step_lines) >= len(TASKS), "inference.py must emit [STEP] lines")

start_re = re.compile(r"^\[START\] task=\S+ env=\S+ model=.+$")
step_re = re.compile(r"^\[STEP\] step=\d+ action=.* reward=\d+\.\d{2} done=(true|false) error=.*$")
end_re = re.compile(r"^\[END\] success=(true|false) steps=\d+ score=\d+\.\d{3} rewards=(?:\d+\.\d{2}(?:,\d+\.\d{2})*)?$")

for line in start_lines:
    require(bool(start_re.match(line)), f"invalid [START] line: {line}")
for line in step_lines:
    require(bool(step_re.match(line)), f"invalid [STEP] line: {line}")
for line in end_lines:
    require(bool(end_re.match(line)), f"invalid [END] line: {line}")

print("[OK] local validation passed")
PY

if [[ -n "$SPACE_URL" ]]; then
  python3 - "$SPACE_URL" <<'PY'
import json
import sys
from urllib import request

space_url = sys.argv[1].rstrip("/")

for path in ("/", "/health", "/reset?task_id=easy"):
    with request.urlopen(f"{space_url}{path}", timeout=20) as response:
        if response.status != 200:
            raise SystemExit(f"[FAIL] remote check failed for {path}: HTTP {response.status}")
        body = response.read().decode("utf-8")
        if path != "/" and not body:
            raise SystemExit(f"[FAIL] remote check returned empty body for {path}")

print("[OK] remote validation passed")
PY
fi
