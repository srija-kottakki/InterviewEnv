# InterviewEnv

InterviewEnv is a real-world OpenEnv environment where an AI agent plays the role of a job candidate in a multi-turn interview. The interviewer uses a hidden rubric, and the agent must infer what is being evaluated from the questions, then adapt its answers over time.

## Tasks

| Task | Focus | Max Turns | Pass Threshold |
|---|---|---:|---:|
| `easy` | Cultural fit and teamwork | 5 | 0.55 |
| `medium` | Technical depth, clarity, and honesty | 8 | 0.60 |
| `hard` | Composure, evidence, and pushback handling | 12 | 0.65 |

## Action Space

```python
class InterviewAction(BaseModel):
    message: str
```

## Observation Space

```python
class InterviewObservation(BaseModel):
    interviewer_message: str
    turn: int
    max_turns: int
    task_id: str
    done: bool
    feedback: Optional[str]
```

## Reward

Each step returns a reward in the `0.0` to `1.0` range. The reward combines:

- rubric alignment
- answer specificity
- recovery after weak turns

Very short or generic answers are penalized.

## API

- `POST /reset` starts an episode for a task
- `POST /step` submits the candidate response
- `GET /state` returns current environment state
- `GET /tasks` lists available tasks

## Setup

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 7860
```

## Inference

The baseline script must be named `inference.py` and lives at the project root for validator compatibility.

Required environment variables:

- `API_BASE_URL`: model endpoint compatible with the OpenAI client
- `MODEL_NAME`: model identifier for inference
- `HF_TOKEN`: Hugging Face token or API key

Example:

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_token

python inference.py
```

The script uses the OpenAI Python client for model calls and emits structured stdout blocks marked with `[START]`, `[STEP]`, and `[END]`.

## Docker

```bash
docker build -t interview-env .
docker run -p 7860:7860 \
  -e API_BASE_URL=https://router.huggingface.co/v1 \
  -e MODEL_NAME=gpt-4o-mini \
  -e HF_TOKEN=your_token \
  interview-env
```

## Project Files

- `environment.py`: environment logic, typed models, and graders
- `server.py`: FastAPI app exposing `/reset`, `/step`, `/state`, and `/tasks`
- `openenv.yaml`: OpenEnv metadata and space definitions
- `inference.py`: reproducible baseline runner
- `Dockerfile`: container entrypoint for deployment
