# API Reference

## GET /reset

Starts a new episode.

Query parameters:

- `task_id`: `easy`, `medium`, or `hard`

Response: `StateModel`

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

## GET /state

Returns current state.

Response: `StateModel`

## GET /metadata

Returns task, model, endpoint, and reward metadata.
