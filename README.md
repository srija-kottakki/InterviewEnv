---
title: InterviewEnv
emoji: "🎙️"
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# InterviewEnv

InterviewEnv is an OpenEnv-compatible interview simulation environment for the Meta PyTorch Hackathon x Scaler School of Technology. It models realistic interview behavior across three difficulty levels and exposes a typed `reset()` / `step()` / `state()` API for RL-style training and evaluation.

## What It Simulates

The environment asks adaptive interview questions, evaluates each answer with deterministic graders, and returns:

- structured behavioral feedback
- shaped rewards in the `0.0-1.0` range
- follow-up questions based on answer quality
- task success signals and episode state

This is designed as a real-world environment for interview preparation, coaching, and training agents that improve over repeated turns.

## Tasks

The environment includes three graded tasks:

| Task ID | Difficulty | Goal |
| --- | --- | --- |
| `easy` | easy | Answer basic interview questions clearly and relevantly |
| `medium` | medium | Explain projects and tradeoffs with structure and reasoning |
| `hard` | hard | Handle adaptive, pressure-style behavioral questions using STAR-style evidence |

Each task has:

- a deterministic grader
- a pass threshold
- dense reward shaping
- multi-step interaction

## Action Space

Actions are typed with `ActionModel`.

```json
{
  "answer": "I built a project and measured its impact.",
  "answer_strategy": "structured",
  "confidence_level": 4,
  "confidence": 0.8,
  "strategy": "structured",
  "tone": "confident"
}
```

Important fields:

- `answer` or `message`: the candidate response text
- `answer_strategy`: one of `direct`, `detailed`, `structured`, `concise`, `default`, `clarify`, `skip`
- `confidence_level`: integer `1-5`
- `tone`: one of `neutral`, `confident`, `collaborative`, `defensive`

## Observation Space

`step()` returns:

```json
{
  "observation": {
    "task_id": "easy",
    "prompt": "What is one strength you would bring to this team?",
    "turn": 1,
    "max_turns": 3,
    "done": false,
    "behavioral_feedback": {
      "filler_score": 1.0,
      "confidence_score": 0.65,
      "clarity_score": 0.78,
      "comments": "Clear structure."
    }
  },
  "reward": 0.91,
  "done": false,
  "info": {}
}
```

State returned by `reset()` and `state()` includes:

- question and prompt history
- QA history
- score history and trend
- reward breakdown
- stress/adaptivity metrics
- task success and final score

## Reward Design

Rewards are bounded in the `0.0-1.0` range and combine:

- relevance to the question
- clarity and behavioral quality
- confidence alignment
- action strategy quality
- improvement over previous turns
- consistency across recent turns
- repetition penalties

## API

The FastAPI app is available on port `7860`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | health check |
| `GET` | `/api` | API status |
| `GET` | `/metadata` | environment metadata and schemas |
| `GET` | `/reset?task_id=easy` | start an episode |
| `POST` | `/reset` | start an episode with JSON body |
| `POST` | `/step` | submit one action |
| `GET` | `/state` | fetch current state |
| `POST` | `/upload_resume` | upload a resume for optional personalization |

## Project Structure

```text
InterviewEnv/
├── api/
├── env/
├── server/
├── ui/
├── inference.py
├── openenv.yaml
├── Dockerfile
├── launch.sh
└── README.md
```

## Local Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the API locally

```bash
python app.py
```

Then open:

```text
http://localhost:7860
```

### 3. Run baseline inference locally

```bash
python inference.py
```

The script emits strict single-line logs in the required format:

```text
[START] task=easy env=InterviewEnv model=gpt-4o-mini
[STEP] step=1 action={"answer":"..."} reward=0.95 done=false error=null
[END] success=true steps=2 score=0.879 rewards=0.96,0.80
```

If `HF_TOKEN` is not set, `inference.py` uses deterministic fallback actions so it still produces reproducible scores.

## Required Environment Variables

The submission expects these variables:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`
- `PORT`

Defaults are provided for local execution where possible.

## Docker / Hugging Face Space

The repo is packaged as a Docker Space and serves the app on port `7860`.

Main files:

- `Dockerfile`
- `launch.sh`
- `openenv.yaml`

## Validation

A local validation helper is included:

```bash
./validate-submission.sh
```

You can also validate a deployed HF Space:

```bash
./validate-submission.sh https://your-space-url.hf.space
```

## Baseline Scores

Current deterministic local baseline from `inference.py`:

| Task | Score |
| --- | --- |
| `easy` | `~0.879` |
| `medium` | `~0.995` |
| `hard` | `~0.942` |

These values are reproducible with the fallback policy and may vary if a remote model is enabled with `HF_TOKEN`.
