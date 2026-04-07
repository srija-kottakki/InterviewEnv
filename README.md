---
title: InterviewEnv
emoji: "🎙️"
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# InterviewEnv

InterviewEnv is an OpenEnv Round 1 environment for deterministic interview-answer evaluation. It exposes strict validator endpoints, typed Pydantic models, three increasing-difficulty tasks, deterministic graders, and an optional browser UI for manual testing.

## File Structure

```text
InterviewEnv/
├── app.py
├── main.py
├── models.py
├── graders.py
├── inference.py
├── openenv.yaml
├── launch.sh
├── Dockerfile
├── requirements.txt
├── env/
├── ui/
├── docs/
├── examples/
└── screenshots/
```

## OpenEnv API Contract

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

`GET /metadata` returns environment metadata, task definitions, model names, endpoint descriptions, and reward details.

The validator endpoints stay API-first. The optional UI is available at `GET /` and `GET /ui/`.

## Tasks

| Task | Difficulty | Description | Grader |
|---|---|---|---|
| `easy` | easy | Basic interview question answering | `graders.grade_easy` |
| `medium` | medium | Multi-turn follow-up reasoning | `graders.grade_medium` |
| `hard` | hard | Behavioral STAR-format interview simulation | `graders.grade_hard` |

## Typed Models

The public Pydantic models live in `models.py`:

- `Action`
- `Observation`
- `Metadata`
- `ResetRequest`
- `ResetResponse`
- `StepResponse`
- `StateResponse`

## Reward

Reward is exactly the selected deterministic grader score for the latest action. Each grader returns a float in `[0.0, 1.0]` based on keyword matching and answer completeness.

## Run Locally

```bash
pip install -r requirements.txt
./launch.sh
```

Open:

```text
http://localhost:7860
```

## Baseline Inference

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_token
python inference.py
```

If `HF_TOKEN` is not set, `inference.py` uses deterministic fallback answers. Logs are emitted as:

```text
[START] {"task_id":"easy","state":{},"info":{}}
[STEP] {"task_id":"easy","step":1,"action":{"message":"..."},"state":{},"reward":0.5,"done":false,"info":{}}
[END] {"task_id":"easy","score":0.5,"steps":2,"done":true}
```

## Docker / Hugging Face Space

```bash
docker build -t interview-env .
docker run -p 7860:7860 interview-env
```

The Docker container launches:

```bash
./launch.sh
```
