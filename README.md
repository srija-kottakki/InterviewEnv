---
title: InterviewEnv
emoji: "🎙️"
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# InterviewEnv

InterviewEnv is an API-only OpenEnv Round 1 environment for deterministic interview-answer evaluation. It exposes strict `/reset`, `/step`, and `/state` endpoints and includes three tasks with increasing difficulty.

## API Contract

`GET /reset?task_id=easy` or `POST /reset`

```json
{"state": {}, "info": {}}
```

`POST /step`

```json
{"state": {}, "reward": 0.0, "done": false, "info": {}}
```

`GET /state`

```json
{"state": {}}
```

No UI or Gradio app is launched.

## Tasks

| Task | Difficulty | Description | Grader |
|---|---|---|---|
| `easy` | easy | Basic interview question answering | `grade_easy` |
| `medium` | medium | Multi-turn follow-up reasoning | `grade_medium` |
| `hard` | hard | Behavioral STAR-format interview simulation | `grade_hard` |

## Action Space

```json
{"message": "candidate answer"}
```

The action model is `env.models.InterviewAction`.

## Observation / State Space

The state model is `env.models.InterviewState`:

```json
{
  "task_id": "easy",
  "difficulty": "easy",
  "turn": 0,
  "max_turns": 2,
  "prompt": "Tell me about yourself...",
  "history": [],
  "done": false
}
```

## Reward

Reward is exactly the deterministic grader score for the latest answer. Each grader returns a float in `[0.0, 1.0]` using keyword matching and answer completeness criteria.

## Run Locally

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7860
```

## Baseline Inference

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_token
python inference.py
```

If `HF_TOKEN` is not set, the script uses deterministic fallback answers. Logs are emitted exactly as:

```text
[START] {"task_id":"easy","state":{},"info":{}}
[STEP] {"task_id":"easy","step":1,"action":{"message":"..."},"state":{},"reward":0.5,"done":false,"info":{}}
[END] {"task_id":"easy","score":0.5,"steps":2,"done":true}
```

## Docker

```bash
docker build -t interview-env .
docker run -p 7860:7860 interview-env
```
