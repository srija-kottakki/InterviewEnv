---
title: InterviewEnv
emoji: "🎙️"
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# InterviewEnv

InterviewEnv is an OpenEnv Round 1 submission that turns interview practice into a typed, deterministic, RL-style environment. An agent receives an adaptive interview state, chooses a structured interview action, and receives a reward from deterministic graders that score correctness, clarity, confidence, consistency, and improvement over time.

The app works with or without resume upload. Without a resume, it uses a general interview bank. With a PDF/text resume, it parses skills, projects, tools, education, and experience to personalize follow-up questions.

## Demo Flow

The live Space opens to a clean browser UI for quick hackathon demos:

- Select `Easy`, `Medium`, or `Hard`
- Optionally upload a resume
- Click `Generate Question`
- Submit an answer with strategy and confidence
- Review the score, behavioral feedback, and adaptive next question

The OpenEnv API remains available behind the UI:

- `GET /api`
- `GET /metadata`
- `GET /reset?task_id=easy`
- `POST /step`
- `GET /state`
- `POST /upload_resume`

## Why This Is RL-Based

InterviewEnv is not only an LLM evaluator. It has a Markov-style transition loop:

- **State**: current question, task, difficulty, stress level, score trend, score history, behavioral feedback, resume context, question history, QA history, and performance history.
- **Action**: structured candidate policy choice with `answer`, `answer_strategy`, `confidence_level`, and `tone`.
- **Transition**: `step(action)` grades the answer, shapes reward from improvement and memory, updates cumulative score/performance history, adapts difficulty, updates stress/adaptivity factor, selects a new question, and terminates on sustained success or max turns.
- **Reward**: deterministic shaped float in `[0.0, 1.0]` using current performance, strategy/confidence choices, consistency, improvement over previous steps, and repetition penalties.

## 🧠 Reinforcement Learning Environment

InterviewEnv is a sequential decision-making environment where:

- Each agent action influences future interview difficulty
- Rewards are accumulated across multiple steps
- Performance improves over time through feedback and adaptation

Unlike static evaluation systems, this environment models a **dynamic interview process** where the agent must learn, adapt, and improve across turns.

## 🎯 Objective

The agent’s goal is to maximize cumulative reward by:

- Improving answer quality
- Maintaining consistency
- Adapting to increasing difficulty

This creates a true reinforcement learning loop with evolving state transitions.

## Folder Structure

```text
InterviewEnv/
├── api/
│   ├── __init__.py
│   └── main.py
├── env/
│   ├── __init__.py
│   ├── env.py
│   ├── graders.py
│   ├── models.py
│   └── tasks.py
├── utils/
│   ├── __init__.py
│   ├── feedback_analyzer.py
│   └── resume_parser.py
├── ui/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── docs/
├── examples/
├── screenshots/
├── app.py
├── models.py
├── graders.py
├── inference.py
├── openenv.yaml
├── launch.sh
├── Dockerfile
└── requirements.txt
```
## 🌍 Environment Description

InterviewEnv is a **sequential decision-making environment** that mimics the flow of a real technical or behavioral interview session.

```
[ START ] ──▶ [ STEP ] ──▶ [ STEP ] ──▶ ... ──▶ [ END ]
   │              │                                   │
Initialize     Candidate                         Final Score
Interview      Answers Q                         + Feedback
```

| State   | Description                                              |
|---------|----------------------------------------------------------|
| `START` | Initializes the interview session and selects task track |
| `STEP`  | Candidate receives a question and submits a response     |
| `END`   | Session closes; final score and detailed feedback issued |

The environment simulates **interviewer behavior** — it adapts based on your responses, escalates difficulty, and probes weak areas just like a human interviewer would.

---

## 🕹️ Action Space Definition

> **Action = Natural Language Response (string)**

Candidates interact with the environment through free-form natural language. There are no predefined choices or constraints — just like a real interview.

**Valid action types include:**

- 📝 **Explanations** — Describe your thought process or approach
- 💻 **Code Snippets** — Write and explain solutions inline
- 🧠 **Reasoning** — Walk through trade-offs, edge cases, or design decisions

**Properties:**

| Property        | Value                          |
|-----------------|--------------------------------|
| Type            | `string` (free-form text)      |
| Format          | Natural language               |
| Context-aware   | Yes — responses are evaluated relative to the current question and history |
| Length          | Unconstrained                  |

---

## 👁️ Observation Space Definition

> **Observation = `{ question, context, previous_feedback }`**

At every `STEP`, the agent receives a structured observation:

```python
observation = {
    "question":          str,            # The current interview question
    "context":           str,            # Topic, difficulty, and session state
    "previous_feedback": str | None      # Feedback from the last step (if any)
}
```

| Field               | Type          | Description                                        |
|---------------------|---------------|----------------------------------------------------|
| `question`          | `str`         | The question posed by the simulated interviewer    |
| `context`           | `str`         | Track (DSA/HR/Design), difficulty, and round info  |
| `previous_feedback` | `str \| None` | Feedback from prior response; `None` on first step |

This design enables **iterative improvement** — candidates can learn from feedback mid-session and adjust their strategy.

---

## 📋 Task Descriptions with Difficulty Levels

InterviewEnv ships with three task tracks, each with three difficulty tiers.

### 🧩 Track 1 — Data Structures & Algorithms (DSA)

| Difficulty | Topics Covered                              |
|------------|---------------------------------------------|
| 🟢 Easy    | Arrays, strings, basic sorting              |
| 🟡 Medium  | Recursion, binary trees, linked lists        |
| 🔴 Hard    | Graphs, dynamic programming, advanced trees |

### 🤝 Track 2 — Behavioral / HR

| Difficulty | Topics Covered                                    |
|------------|---------------------------------------------------|
| 🟢 Easy    | Self-introductions, background questions           |
| 🟡 Medium  | Conflict resolution, teamwork scenarios            |
| 🔴 Hard    | Ambiguous dilemmas, leadership under pressure      |

### 🏗️ Track 3 — System Design *(Extendable)*

| Difficulty | Topics Covered                                         |
|------------|--------------------------------------------------------|
| 🟡 Medium  | Component design, API modeling                         |
| 🔴 Hard    | Distributed architecture, scalability, trade-off analysis |

> 💡 New tracks can be added by extending the task config — the environment is fully modular.

---

## State Space

`StateModel` includes:

```json
{
  "task_id": "easy",
  "difficulty": "easy",
  "current_difficulty": 1,
  "turn": 0,
  "max_turns": 3,
  "current_question": "Why are you interested in this role?",
  "history": [],
  "qa_history": [],
  "question_history": [],
  "resume_text": "",
  "parsed_resume_data": {},
  "behavioral_feedback": {},
  "performance_history": [],
  "score_history": [],
  "score_trend": "flat",
  "stress_level": 0.15,
  "adaptivity_factor": 0.0,
  "reward_breakdown": {},
  "learning_metrics": {
    "average_score": 0.0,
    "total_score": 0.0,
    "turns": 0,
    "turns_taken": 0,
    "score_history": []
  },
  "last_action": {},
  "score": 0.0,
  "success": false,
  "done": false
}
```

## Action Space

Existing validators can still send only `answer`, but the stronger OpenEnv action is:

```json
{
  "answer": "I would explain the project goal, tradeoffs, result, and what I learned.",
  "answer_strategy": "structured",
  "confidence_level": 4,
  "strategy": "structured",
  "confidence": 0.8,
  "tone": "collaborative"
}
```

Valid values:

- `answer_strategy` / `strategy`: `direct`, `detailed`, `structured`, `concise`, `default`, `clarify`, `skip`
- `confidence_level`: integer `1` to `5`
- `confidence`: float `0.0` to `1.0`
- `tone`: `neutral`, `confident`, `collaborative`, `defensive`

These fields affect reward, stress, difficulty adaptation, and next-question selection.

## Tasks

| Task | Name | Max Steps | Success | Environment Behavior |
|---|---|---:|---:|---|
| `easy` | Basic Interview Simulation | 3 | 0.78 | Starts at difficulty 1 and rewards role-fit keywords, concise evidence, and confidence. |
| `medium` | Technical Interview Simulation | 4 | 0.80 | Starts at difficulty 2 and rewards tradeoffs, measurement, specificity, and improvement. |
| `hard` | Adaptive Stress Interview | 5 | 0.82 | Starts at difficulty 3 and rewards STAR structure, impact, recovery, consistency, and stress handling. |

## Reward Logic

Reward is deterministic and always clamped to `[0.0, 1.0]`. The returned step reward is shaped, while `score` is cumulative across the episode.

```text
base_reward = weighted(correctness, clarity, confidence, consistency, improvement, confidence_alignment, action_strategy)
shaped_reward = task_weight * (
  base_reward
  + 0.2 * max(base_reward - previous_reward, 0)
  + consistency_bonus
  + strategy_bonus
  + confidence_bonus
  - repetition_penalty
)
cumulative_score += shaped_reward
average_score = cumulative_score / steps
```

Components:

- `correctness`: question relevance, task-specific rubric keywords, resume match when available.
- `clarity`: structure, coherence, and directness from deterministic feedback analysis.
- `confidence`: decisive language and authority.
- `consistency_over_time`: avoids highly volatile performance across recent steps.
- `improvement_over_previous_step`: rewards upward score trend.
- `confidence_alignment`: compares claimed `confidence_level` against observed confidence.
- `action_strategy`: rewards suitable strategy choices and penalizes `skip`.
- `repetition_penalty`: discourages repeating recent answers.
- `learning_metrics`: exposes `average_score`, `total_score`, `turns_taken`, `score_history`, `improvement_trend`, `previous_reward`, `current_reward`, and `cumulative_score`.

Success requires sustained learning:

```text
success = average_score >= pass_threshold and steps >= 2
```

## API Contract

`GET /reset?task_id=easy`

Returns `StateModel`.

`POST /reset`

```json
{"task_id": "medium"}
```

Returns `StateModel`.

`POST /step`

```json
{
  "answer": "Using STAR, the situation was a team conflict...",
  "answer_strategy": "structured",
  "confidence_level": 4,
  "confidence": 0.8,
  "tone": "collaborative"
}
```

Returns:

```json
{
  "observation": {},
  "reward": 0.0,
  "done": false,
  "info": {}
}
```

`GET /state`

Returns `StateModel`.

`GET /metadata`

Returns `MetadataModel` with schemas, tasks, graders, and endpoint information.

`POST /upload_resume`

Optional. Upload a PDF or text resume as `multipart/form-data` field `file`. The environment still works without this endpoint.

## Run Locally

```bash
pip install -r requirements.txt
./launch.sh
```

Open the UI:

```text
http://localhost:7860
```

## Inference

The baseline script uses the OpenAI client with:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_token
python inference.py
```

Strict log format:

```text
[START]
[STEP] {"task_id":"easy","step":1,"action":{},"observation":{},"reward":0.5,"done":false,"info":{}}
[STEP] {"task_id":"medium","step":1,"action":{},"observation":{},"reward":0.6,"done":false,"info":{}}
[END] {"env_id":"InterviewEnv","model":"gpt-4o-mini","tasks":[],"mean_score":0.0}
```

If `HF_TOKEN` is not set, inference uses deterministic fallback actions so validators can still run it quickly.

## Docker / Hugging Face

```bash
docker build -t interview-env .
docker run -p 7860:7860 interview-env
```

The Space runs FastAPI through `launch.sh` and exposes port `7860`.
