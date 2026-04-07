# OpenEnv Compliance

- Strict reset response: `{"state": {...}, "info": {...}}`
- Strict step response: `{"state": {...}, "reward": float, "done": boolean, "info": {...}}`
- Strict state response: `{"state": {...}}`
- Typed Pydantic models: `models.py`
- Three tasks: `easy`, `medium`, `hard`
- Deterministic graders: `graders.py`
- Metadata: `openenv.yaml` and `/metadata`
- Hugging Face launch: `launch.sh`
