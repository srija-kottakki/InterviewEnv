---
title: InterviewEnv
emoji: "🎙️"
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🎯 InterviewEnv

> **A Reinforcement-Learning Ready AI Interview Simulation Environment**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HuggingFace Space](https://img.shields.io/badge/🤗%20HuggingFace-Space-blue)](https://huggingface.co/spaces/srija-kottakki/InterviewEnv)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-black?logo=github)](https://github.com/srija-kottakki/InterviewEnv)

---

## 📖 Introduction & Motivation

**InterviewEnv** is a customizable AI environment that simulates real interview scenarios. It is designed for agents that learn to answer questions, understand feedback, and improve over time — similar to real-world candidate preparation systems.

### Why an AI Interview Environment?

Real interviews involve adaptive difficulty, multi-turn reasoning, and behavioral feedback. Most RL environments focus on games; InterviewEnv focuses on **human–AI interaction**. This allows developers and researchers to train agents that can:

- Communicate clearly
- Respond contextually
- Handle increasing challenge levels
- Improve through feedback loops

### Who is it for?

- RL researchers
- AI/ML engineers
- HR-tech builders
- Hackathon participants
- Students learning RL or LLM agent design

### Real-World Use Cases

- Interview preparation platforms
- Adaptive tutoring systems
- HR screening and scoring automation
- Behavior-aware LLM agents
- AI coaching and assessment tools

---




https://github.com/user-attachments/assets/61159e11-12c2-4de3-93c6-c482f28236da






## 🏗️ Environment Description

InterviewEnv simulates a full interview loop:

```
Environment asks a question
       ↓
Agent sends an answer
       ↓
Environment evaluates
       ↓
Agent receives feedback + reward
       ↓
Loop continues until termination
```

### Core Architecture

| Component | Description |
|---|---|
| **Question Generator** | Selects or adapts question difficulty |
| **Response Evaluator** | Checks clarity, relevance, reasoning |
| **Feedback Layer** | Provides natural-language feedback |
| **Reward Engine** | Produces score per step |
| **Adaptive Difficulty Engine** | Adjusts levels (easy → hard) |

### Unique Features

- ✅ Adaptive multi-level difficulty
- ✅ Behavior-based scoring
- ✅ Fully text-based interaction
- ✅ Plug-and-play for any RL algorithm
- ✅ Works with LLM agents, rule-based agents, or human-in-the-loop

---

## 🕹️ Action Space

**Action Type:** String action (agent's answer to the interview question)

```python
action = "Your response as a single string."
```

**Agent may send:**
- Full sentences
- Short answers
- Explanations

**Agent must NOT send:**
- Empty strings
- Non-text objects
- JSON with metadata
- Multiple answers in one turn

**Valid Example:**
```python
action = "I enjoy solving problems and working in teams."
```

---

## 👁️ Observation Space

Each environment step returns an observation dictionary:

```json
{
    "question": "<string>",
    "difficulty": "<easy|medium|hard>",
    "feedback": "<string or None>",
    "reward": 0.75,
    "done": false
}
```

| Field | Description |
|---|---|
| `question` | Current interview question |
| `difficulty` | Difficulty level (auto-adaptive) |
| `feedback` | Behavior/evaluation message |
| `reward` | Score for the agent's answer |
| `done` | Whether the interview is finished |

### Termination Conditions

- Agent reaches max questions
- Agent gives consistently low-scoring answers
- Hard task completion
- Internal failure or invalid action

---

## 📋 Task Descriptions

### Task 1 – Easy: Basic Q&A

Personal background questions with no complex reasoning required. Reward is based on clarity and relevance.

> **Example questions:**
> - "Tell me about yourself."
> - "What are your hobbies?"

### Task 2 – Medium: Situational Questions

Behavioral and situational interviews where the agent must provide structured reasoning. Feedback becomes more detailed.

> **Example loop:**
> - **Obs:** "Describe a time you solved a problem."
> - **Act:** agent answer
> - **Env:** gives feedback + reward (0–1)

### Task 3 – Hard: Adaptive Role-Specific Interview

Dynamic difficulty engine with multi-turn, memory-based reasoning and role-specific topics (tech, HR, management). Complex scoring evaluates structure, accuracy, and depth.

> **Example questions:**
> - "Explain a complex technical project in simple terms."
> - "How would you design a scalable solution for handling real-time data?"

---

## 📊 Baseline Scores

Baseline performance across **20 episodes**:

| Agent Type | Avg Reward | Success Rate | Notes |
|---|---|---|---|
| Random Agent | 0.10 – 0.18 | ~5% | Usually irrelevant responses |
| Rule-based Agent | 0.35 – 0.45 | ~30% | Template-based answers |
| Simple LLM Agent | 0.55 – 0.70 | ~60% | Good structure, moderate depth |

**Expected ranges:**
- `< 0.3` → Poor performance
- `0.3 – 0.6` → Decent performance
- `> 0.6` → Strong interview behavior

---

## ⚙️ Setup & Installation

### 1. Clone the repo

```bash
git clone https://github.com/srija-kottakki/InterviewEnv
cd InterviewEnv
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the environment

```bash
python main.py
```

### 4. Run the RL agent example

```bash
python agent_example.py
```

### 5. Run HuggingFace Space locally

```bash
huggingface-cli login
python app.py
```

### Using the Web UI

The Gradio app launches automatically at:

```
http://localhost:7860
```

---

## 💻 Usage Examples

### Create the environment

```python
from interview_env import InterviewEnv

env = InterviewEnv()
obs = env.reset()
print(obs)
```

### Step example

```python
action = "I enjoy learning new technologies."
obs, reward, done, info = env.step(action)
```

### Full episode loop

```python
obs = env.reset()
done = False

while not done:
    action = "Sample answer"  # Your agent logic here
    obs, reward, done, info = env.step(action)
    print(obs, reward)
```

### RL Integration Example (pseudo-code)

```python
import stable_baselines3 as sb3

env = InterviewEnv()
model = sb3.PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=5000)
```

---

 Live Demo

| Link | Action |
|---|---|
| 🤗 [HuggingFace Space](https://huggingface.co/spaces/srija-kottakki/InterviewEnv) | Launch on HuggingFace |
| 🌐 [Live UI](https://srija-kottakki-interviewenv.hf.space) | Try the Live UI |
| 💻 [GitHub Repo](https://github.com/srija-kottakki/InterviewEnv) | Open GitHub Repo |

---

 UI Screenshots

<img width="1600" height="697" alt="image" src="https://github.com/user-attachments/assets/dee6fdaf-6573-4001-9084-b81c08ad147d" />

<img width="1600" height="643" alt="image" src="https://github.com/user-attachments/assets/28d3ac6c-9fec-4aee-927e-cf3b6cdb7bf5" />

<img width="1600" height="842" alt="image" src="https://github.com/user-attachments/assets/dc814f8e-4be9-4268-93b8-6159ac68fa2a" />



---

## 🛠️ Tools & Frameworks

- [Python](https://www.python.org/)
- [Gradio](https://www.gradio.app/)
- [Hugging Face Spaces](https://huggingface.co/spaces)
- [LangChain](https://www.langchain.com/)
- OpenEnv-style environment design

---

## 📄 License

This project is released under the [MIT License](LICENSE).

---

## 👤 Author

**Srija Kottakki**

[![GitHub](https://img.shields.io/badge/GitHub-srija--kottakki-black?logo=github)](https://github.com/srija-kottakki)
[![HuggingFace](https://img.shields.io/badge/🤗-srija--kottakki-blue)](https://huggingface.co/srija-kottakki)

