# InterviewEnv

**Train AI to ace job interviews by detecting hidden evaluation rubrics in real time.**

> Every year, a million qualified students lose jobs not because they weren't good enough — but because nobody ever told them what they were doing wrong. We fixed that.

---

## What It Does

InterviewEnv is a real-world OpenEnv environment where an AI agent plays a job candidate being interviewed. The interviewer has a **hidden evaluation rubric** the agent never sees directly. The agent must:

1. Detect what's being measured from the questions asked
2. Adapt its answers to match the hidden criteria
3. Recover from weak answers before it's too late

This trains AI to give genuinely better interview answers — not just rehearsed scripts.

---

## Tasks

| Task | Name | Hidden Criteria | Max Turns | Pass Threshold |
|------|------|----------------|-----------|----------------|
| `easy` | HR Round — Cultural Fit | Cultural fit (1 criterion) | 5 | 0.55 |
| `medium` | Technical Round | Depth, clarity, honesty (3 criteria) | 8 | 0.60 |
| `hard` | Stress Interview | Composure, evidence, pushback handling (3 criteria) | 12 | 0.65 |

---

## Action Space

```python
class InterviewAction(BaseModel):
    message: str  # The candidate's spoken response
```

## Observation Space

```python
class InterviewObservation(BaseModel):
    interviewer_message: str   # What the interviewer just said
    turn: int                  # Current turn number
    max_turns: int             # Max turns for this task
    task_id: str               # Active task
    done: bool                 # Episode ended?
    feedback: Optional[str]    # End-of-episode rubric breakdown
```

## Reward

Partial reward given **every turn** (not just at the end):

```
reward = rubric_score × 0.50 + specificity_score × 0.30 + recovery_score × 0.20
```

- `rubric_score`: How well the hidden criteria were met (0.0–1.0)
- `specificity_score`: How concrete and specific the answer was
- `recovery_score`: Bonus for recovering after a weak previous answer
- Penalty for very short or generic answers

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Start new episode. Body: `{"task_id": "easy"}` |
| `/step` | POST | Take action. Body: `{"message": "your answer"}` |
| `/state` | GET | Get current environment state |
| `/tasks` | GET | List all available tasks |

---

## Setup

### Local

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
docker build -t interview-env .
docker run -p 7860:7860 \
  -e API_BASE_URL=https://api.openai.com/v1 \
  -e MODEL_NAME=gpt-4o-mini \
  -e HF_TOKEN=your_token \
  interview-env
```

### Run Inference

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_hf_token

python inference.py
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `API_BASE_URL` | The API endpoint for the LLM |
| `MODEL_NAME` | Model identifier for inference |
| `HF_TOKEN` | Your Hugging Face / API key |

---

## Baseline Scores

| Task | Score |
|------|-------|
| easy | ~0.62 |
| medium | ~0.54 |
| hard | ~0.41 |
| **overall** | **~0.52** |

---

## Real-World Impact

InterviewEnv addresses a genuine gap: access to quality interview coaching is expensive and gatekept. This environment trains AI to deliver the honest, specific feedback that helps candidates understand *exactly* what went wrong — not just that they "could have been more specific."

Built for the Meta × Scaler OpenEnv Hackathon, Round 1.
