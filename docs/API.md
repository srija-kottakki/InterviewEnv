# API Reference

## GET /reset

Starts a new episode.

Query parameters:

- `task_id`: `easy`, `medium`, or `hard`

Response:

```json
{"state": {}, "info": {}}
```

## POST /step

Submits one action.

Request:

```json
{"message": "candidate answer"}
```

Response:

```json
{"state": {}, "reward": 0.0, "done": false, "info": {}}
```

## GET /state

Returns current state.

Response:

```json
{"state": {}}
```

## GET /metadata

Returns task, model, endpoint, and reward metadata.
