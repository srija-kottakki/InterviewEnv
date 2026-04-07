# API Reference

## GET /reset

Starts a new episode.

Query parameters:

- `task_id`: `easy`, `medium`, or `hard`

Response: `StateModel`

State includes `current_difficulty`, `current_question`, `qa_history`, `question_history`, `behavioral_feedback`, and `adaptive_reason`.

## POST /step

Submits one action.

Request:

```json
{"message": "candidate answer"}
```

Response:

```json
{"observation": {}, "reward": 0.0, "done": false, "info": {}}
```

`observation.behavioral_feedback` contains `filler_score`, `confidence_score`, `clarity_score`, and `comments`.

## GET /state

Returns current state.

Response: `StateModel`

## GET /metadata

Returns task, model, endpoint, and reward metadata.
