---
title: InterviewEnv
emoji: "🎙️"
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# InterviewEnv

InterviewEnv is a Meta OpenEnv Round 1 submission for adaptive interview-answer evaluation. It provides typed Pydantic models, deterministic graders, three tasks with increasing difficulty, a FastAPI backend, a baseline OpenAI-client inference script, and an optional UI for manual testing.

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
├── ui/
├── docs/
├── examples/
├── screenshots/
├── models.py
├── graders.py
├── inference.py
├── openenv.yaml
├── launch.sh
├── Dockerfile
└── requirements.txt
```

## Tasks

| Task | Difficulty | Goal | Grader |
|---|---|---|---|
| `easy` | easy | Detect correct interview keywords | `grade_easy()` |
| `medium` | medium | Classify answer quality as poor/avg/good | `grade_medium()` |
| `hard` | hard | Score open-ended behavioral answer with rubric | `grade_hard()` |

## Adaptive Interviewer

The environment maintains `current_difficulty` from 1 to 3 and chooses the next question from difficulty buckets based on the previous answer and uploaded resume context. It tracks `resume_text`, `parsed_resume_data`, `question_history`, `qa_history`, `behavioral_feedback`, `last_feedback`, and `adaptive_reason` in state payloads.

## API

`GET /reset?task_id=easy`

Returns `StateModel`.

`POST /step`

Request:

```json
{"answer": "candidate answer"}
```

Returns:

```json
{"observation": {}, "reward": 0.0, "done": false, "info": {}}
```

`GET /state`

Returns `StateModel`.

`GET /metadata`

Returns `MetadataModel` with `env_id`, `version`, `authors`, schemas, and task list.

`POST /upload_resume`

Uploads a PDF or text resume as `multipart/form-data` field `file`, parses skills, projects, experience, education, and tools, and stores the parsed result in state.

## Models

Defined in `models.py`:

- `ActionModel`
- `ObservationModel`
- `StateModel`
- `MetadataModel`
- `StepResponseModel`

## Reward

Reward is exactly the selected grader score:

```text
reward = grader_score
```

The grader uses calibrated task-specific weights over clarity, confidence, relevance, resume match, and STAR/rubric evidence. Partial credit is supported. Episodes terminate when the score reaches the task threshold or when max steps are exhausted. Behavioral feedback includes filler usage, confidence, clarity, and comments.

## Run Locally

```bash
pip install -r requirements.txt
./launch.sh
```

Open the optional UI:

```text
http://localhost:7860
```

## Inference

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_token
python inference.py
```

The script uses the OpenAI client and emits:

```text
[START]
[STEP] {"task_id":"easy","step":1,"action":{"answer":"..."},"observation":{},"reward":0.5,"done":false,"info":{}}
[END] {"task_id":"easy","score":0.5,"steps":2,"done":true}
```

## Docker / Hugging Face

```bash
docker build -t interview-env .
docker run -p 7860:7860 interview-env
```
