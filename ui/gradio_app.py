from __future__ import annotations

from html import escape

import gradio as gr

from env.env import InterviewEnv
from env.tasks import TASKS
from models import ActionModel, StateModel


PRIMARY = "#2563EB"
SECONDARY = "#14B8A6"
BACKGROUND = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT = "#111827"
MUTED = "#6B7280"


CUSTOM_CSS = f"""
:root {{
  --primary: {PRIMARY};
  --secondary: {SECONDARY};
  --background: {BACKGROUND};
  --border: {BORDER};
  --text: {TEXT};
  --muted: {MUTED};
}}

html, body, .gradio-container {{
  margin: 0 !important;
  background: var(--background) !important;
  color: var(--text) !important;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}}

.gradio-container {{
  max-width: 920px !important;
  margin: 0 auto !important;
  padding: 32px 20px 56px !important;
}}

#page-shell {{
  gap: 24px !important;
}}

#hero {{
  text-align: center;
  padding: 8px 0 4px;
}}

#hero .eyebrow {{
  margin: 0 0 10px;
  color: var(--secondary);
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}}

#hero h1 {{
  margin: 0;
  color: var(--text);
  font-size: 2.15rem;
  line-height: 1.1;
  font-weight: 600;
}}

#hero p {{
  margin: 12px auto 0;
  max-width: 620px;
  color: var(--muted);
  font-size: 1rem;
  line-height: 1.7;
}}

.panel {{
  background: #ffffff !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04) !important;
  padding: 22px !important;
}}

.panel-title {{
  margin: 0 0 16px;
  color: var(--text);
  font-size: 1rem;
  font-weight: 600;
}}

.section-kicker {{
  margin: 0 0 10px;
  color: var(--secondary);
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.question-card h2,
.feedback-card h2,
.summary-card h2 {{
  margin: 0;
  color: var(--text);
  font-size: 1.5rem;
  line-height: 1.35;
  font-weight: 600;
}}

.question-meta,
.feedback-meta,
.summary-meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin: 0 0 14px;
}}

.pill {{
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: var(--primary);
  font-size: 0.86rem;
  font-weight: 600;
}}

.pill.teal {{
  background: rgba(20, 184, 166, 0.10);
  color: #0f766e;
}}

.question-card p,
.feedback-card p,
.summary-card p,
.feedback-list li {{
  margin: 0;
  color: var(--muted);
  font-size: 0.98rem;
  line-height: 1.7;
}}

.feedback-list {{
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 12px;
}}

.feedback-list li strong {{
  color: var(--text);
  display: block;
  margin-bottom: 4px;
  font-size: 0.95rem;
}}

.metric-grid,
.summary-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}}

.metric,
.summary-stat {{
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px;
  background: #ffffff;
}}

.metric-label,
.summary-label {{
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.4;
}}

.metric-value,
.summary-value {{
  margin-top: 6px;
  color: var(--text);
  font-size: 1.12rem;
  font-weight: 600;
}}

.score-badge {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(20, 184, 166, 0.10);
  color: #0f766e;
  font-size: 1rem;
  font-weight: 700;
}}

.hint {{
  margin-top: 12px;
  color: var(--muted);
  font-size: 0.92rem;
}}

#setup-row {{
  align-items: end !important;
  gap: 12px !important;
}}

#generate-button,
#submit-button {{
  min-height: 46px !important;
}}

#generate-button button,
#submit-button button {{
  background: var(--primary) !important;
  color: #ffffff !important;
  border: 1px solid var(--primary) !important;
  border-radius: 12px !important;
  box-shadow: none !important;
  font-weight: 600 !important;
}}

#generate-button button:hover,
#submit-button button:hover {{
  background: #1d4ed8 !important;
  border-color: #1d4ed8 !important;
}}

.gradio-container .gr-form,
.gradio-container .gr-box,
.gradio-container .gr-panel {{
  border-color: var(--border) !important;
}}

.gradio-container textarea,
.gradio-container input,
.gradio-container select {{
  background: #ffffff !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}

.gradio-container label,
.gradio-container .gr-form label,
.gradio-container .gr-form span {{
  color: var(--text) !important;
}}

.gradio-container textarea::placeholder {{
  color: #9ca3af !important;
}}

@media (max-width: 768px) {{
  .gradio-container {{
    padding: 20px 16px 40px !important;
  }}

  #hero h1 {{
    font-size: 1.85rem;
  }}

  .metric-grid,
  .summary-grid {{
    grid-template-columns: 1fr;
  }}
}}
"""


def build_gradio_demo() -> gr.Blocks:
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="teal",
        neutral_hue="slate",
        radius_size="lg",
    )

    with gr.Blocks(theme=theme, css=CUSTOM_CSS, title="InterviewEnv") as demo:
        session_env = gr.State(value=None)

        with gr.Column(elem_id="page-shell"):
            gr.HTML(
                """
                <section id="hero">
                  <div class="eyebrow">AI Mock Interview Practice</div>
                  <h1>InterviewEnv</h1>
                  <p>
                    Practice one question at a time with clean, instant feedback.
                    Pick a difficulty, generate a question, and improve with each response.
                  </p>
                </section>
                """
            )

            with gr.Group(elem_classes=["panel"]):
                gr.HTML('<div class="panel-title">Interview Setup</div>')
                with gr.Row(elem_id="setup-row"):
                    difficulty = gr.Dropdown(
                        choices=["Easy", "Medium", "Hard"],
                        value="Easy",
                        label="Select Difficulty",
                        container=False,
                        scale=3,
                    )
                    generate_button = gr.Button("Generate Question", elem_id="generate-button", scale=2)

            question_box = gr.HTML(_render_question_card(None, "easy", 1, False))

            with gr.Group(elem_classes=["panel"]):
                gr.HTML('<div class="panel-title">Your Answer</div>')
                answer_box = gr.Textbox(
                    label="Your Answer",
                    placeholder="Write a focused answer with context, what you did, and the result.",
                    lines=8,
                )
                gr.HTML('<div class="hint">Tip: concise, specific examples read best in a demo.</div>')
                submit_button = gr.Button("Submit Answer", elem_id="submit-button")

            feedback_box = gr.HTML(_render_feedback_placeholder())
            summary_box = gr.HTML(_render_summary_placeholder())

            generate_button.click(
                fn=_on_generate_question,
                inputs=[difficulty, session_env],
                outputs=[question_box, answer_box, feedback_box, summary_box, session_env],
            )

            submit_button.click(
                fn=_on_submit_answer,
                inputs=[difficulty, answer_box, session_env],
                outputs=[question_box, answer_box, feedback_box, summary_box, session_env],
            )

    return demo


def _on_generate_question(difficulty: str, session_env: InterviewEnv | None):
    env = _ensure_env(session_env)
    task_id = _normalize_difficulty(difficulty)
    state = env.reset(task_id)
    question_html = _render_question_card(state.current_question, task_id, state.turn + 1, state.done)
    feedback_html = _render_feedback_placeholder()
    summary_html = _render_summary_card(state)
    return question_html, "", feedback_html, summary_html, env


def _on_submit_answer(difficulty: str, answer: str, session_env: InterviewEnv | None):
    env = _ensure_env(session_env)
    state_before = env.state()

    if not state_before.question_history:
        state_before = env.reset(_normalize_difficulty(difficulty))

    if not (answer or "").strip():
        return (
            _render_question_card(
                state_before.current_question,
                state_before.task_id,
                state_before.turn + 1,
                state_before.done,
            ),
            answer,
            _render_feedback_placeholder(message="Type an answer first so I can evaluate it."),
            _render_summary_card(state_before),
            env,
        )

    observation, reward, done, info = env.step(
        ActionModel(
            answer=answer,
            answer_strategy="detailed",
            confidence=0.72,
            tone="confident",
        )
    )
    state_after = env.state()

    question_html = _render_question_card(
        state_after.current_question,
        state_after.task_id,
        state_after.turn + (0 if state_after.done else 1),
        done,
    )
    feedback_html = _render_feedback_card(reward, observation.behavioral_feedback, info, state_after)
    summary_html = _render_summary_card(state_after)
    return question_html, "", feedback_html, summary_html, env


def _ensure_env(session_env: InterviewEnv | None) -> InterviewEnv:
    return session_env if isinstance(session_env, InterviewEnv) else InterviewEnv()


def _normalize_difficulty(value: str) -> str:
    normalized = (value or "easy").strip().lower()
    return normalized if normalized in TASKS else "easy"


def _render_question_card(question: str | None, difficulty: str, turn_number: int, done: bool) -> str:
    label = TASKS.get(difficulty, TASKS["easy"])["name"]
    if not question:
        question = "Click Generate Question to start your mock interview."
    helper = (
        "Choose a clear, specific example and keep your answer focused."
        if not done
        else "This round is complete. Generate a fresh question whenever you want to continue."
    )
    return f"""
    <div class="panel question-card">
      <div class="section-kicker">Interviewer</div>
      <div class="question-meta">
        <span class="pill">{escape(difficulty.title())}</span>
        <span class="pill teal">{escape(label)}</span>
        <span class="pill">Turn {turn_number}</span>
      </div>
      <h2>{escape(question)}</h2>
      <p style="margin-top: 14px;">{escape(helper)}</p>
    </div>
    """


def _render_feedback_placeholder(message: str | None = None) -> str:
    body = message or "Submit an answer to receive a clear score, strengths, and one improvement tip."
    return f"""
    <div class="panel feedback-card">
      <div class="section-kicker">Feedback</div>
      <h2>Ready when you are</h2>
      <p style="margin-top: 12px;">{escape(body)}</p>
    </div>
    """


def _render_feedback_card(
    reward: float,
    behavioral_feedback: dict[str, object],
    info: dict[str, object],
    state: StateModel,
) -> str:
    relevance = float(info.get("relevance_score", 0.0))
    clarity = float(behavioral_feedback.get("clarity_score", 0.0))
    confidence = float(behavioral_feedback.get("confidence_score", 0.0))
    filler = float(behavioral_feedback.get("filler_score", 0.0))
    strengths = _strengths(clarity, confidence, relevance)
    weakness = _weakness(clarity, confidence, relevance, filler)
    improvement = _improvement_tip(state.task_id, clarity, confidence, relevance)
    comments = str(behavioral_feedback.get("comments", ""))

    return f"""
    <div class="panel feedback-card">
      <div class="feedback-meta">
        <div class="section-kicker" style="margin: 0;">Feedback</div>
        <span class="score-badge">Score {reward * 10:.1f}/10</span>
      </div>
      <h2>Here’s how that answer landed</h2>
      <ul class="feedback-list">
        <li>
          <strong>Strengths</strong>
          {escape(strengths)}
        </li>
        <li>
          <strong>Weakness</strong>
          {escape(weakness)}
        </li>
        <li>
          <strong>Improve by</strong>
          {escape(improvement)}
        </li>
        <li>
          <strong>Interviewer note</strong>
          {escape(comments)}
        </li>
      </ul>
      <div class="metric-grid">
        <div class="metric">
          <div class="metric-label">Clarity</div>
          <div class="metric-value">{clarity * 10:.1f}/10</div>
        </div>
        <div class="metric">
          <div class="metric-label">Confidence</div>
          <div class="metric-value">{confidence * 10:.1f}/10</div>
        </div>
        <div class="metric">
          <div class="metric-label">Relevance</div>
          <div class="metric-value">{relevance * 10:.1f}/10</div>
        </div>
      </div>
    </div>
    """


def _render_summary_placeholder() -> str:
    return """
    <div class="panel summary-card">
      <div class="section-kicker">Session Summary</div>
      <h2>Start with one question</h2>
      <p style="margin-top: 12px;">Your running score and interview progress will appear here.</p>
    </div>
    """


def _render_summary_card(state: StateModel) -> str:
    turns = state.learning_metrics.get("turns", state.turn)
    average = float(state.learning_metrics.get("average_score", 0.0)) * 10
    return f"""
    <div class="panel summary-card">
      <div class="section-kicker">Session Summary</div>
      <h2>{escape(TASKS[state.task_id]['name'])}</h2>
      <p style="margin-top: 12px;">A compact view of how the interview is progressing.</p>
      <div class="summary-grid">
        <div class="summary-stat">
          <div class="summary-label">Answers submitted</div>
          <div class="summary-value">{turns}</div>
        </div>
        <div class="summary-stat">
          <div class="summary-label">Average score</div>
          <div class="summary-value">{average:.1f}/10</div>
        </div>
        <div class="summary-stat">
          <div class="summary-label">Current difficulty</div>
          <div class="summary-value">{state.current_difficulty}/3</div>
        </div>
      </div>
    </div>
    """


def _strengths(clarity: float, confidence: float, relevance: float) -> str:
    points = []
    if clarity >= 0.65:
        points.append("clear structure")
    if confidence >= 0.60:
        points.append("confident tone")
    if relevance >= 0.60:
        points.append("good alignment with the question")
    return ", ".join(points) if points else "You gave the interviewer a starting point to build on."


def _weakness(clarity: float, confidence: float, relevance: float, filler: float) -> str:
    if relevance < 0.45:
        return "The answer needs to connect more directly to the actual question."
    if clarity < 0.55:
        return "The structure is still loose, so the main point gets buried."
    if confidence < 0.50:
        return "The delivery feels cautious; stronger ownership language would help."
    if filler < 0.60:
        return "Too many filler phrases reduce polish and precision."
    return "The answer is solid, but one measurable result would make it stronger."


def _improvement_tip(task_id: str, clarity: float, confidence: float, relevance: float) -> str:
    if relevance < 0.50:
        return "Anchor the answer to the prompt first, then add one supporting example."
    if clarity < 0.60:
        return "Use a simple structure: context, action, result."
    if task_id == "hard":
        return "Use STAR and finish with a measurable result plus one lesson learned."
    if confidence < 0.55:
        return "Use direct ownership language such as 'I led', 'I decided', or 'I improved'."
    return "Add one concrete metric or outcome to make the impact easier to trust."
