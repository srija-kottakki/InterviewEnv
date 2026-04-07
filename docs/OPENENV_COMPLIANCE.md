# OpenEnv Compliance

- Typed reset response: `StateModel`
- Typed step response: `{"observation": ObservationModel, "reward": float, "done": boolean, "info": {...}}`
- Typed state response: `StateModel`
- Typed Pydantic models: `models.py`
- Three tasks: `easy`, `medium`, `hard`
- Deterministic graders: `graders.py`
- Metadata: `openenv.yaml` and `/metadata`
- Hugging Face launch: `launch.sh`
