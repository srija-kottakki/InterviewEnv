# OpenEnv Compliance

- Typed reset response: `StateModel`
- Typed step response: `{"observation": ObservationModel, "reward": float, "done": boolean, "info": {...}}`
- Typed state response: `StateModel`
- Typed Pydantic models: `models.py`
- Three tasks: `easy`, `medium`, `hard`
- Deterministic graders: `graders.py`
- Metadata: `openenv.yaml` and `/metadata`
- Hugging Face launch: `launch.sh`
- Adaptive interviewer state: `current_difficulty`, `current_question`, `question_history`, `qa_history`
- Behavioral feedback: `filler_score`, `confidence_score`, `clarity_score`, `comments`
