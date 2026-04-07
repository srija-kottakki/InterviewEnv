from __future__ import annotations

import html
import time

from interview_logic import evaluate_answer, generate_question, normalize_difficulty


APP_CSS = """
:root {
  --bg: #ffffff;
  --surface: #ffffff;
  --surface-soft: #f8fafc;
  --ink: #111827;
  --muted: #6b7280;
  --line: #e5e7eb;
  --blue: #2563eb;
  --blue-dark: #1d4ed8;
  --teal: #14b8a6;
  --teal-soft: #f0fdfa;
  --shadow: 0 10px 30px rgba(17, 24, 39, 0.05);
}

* {
  box-sizing: border-box;
}

body,
.gradio-container {
  background: var(--bg) !important;
  color: var(--ink) !important;
}

.gradio-container {
  min-height: 100vh !important;
  margin: 0 !important;
  padding: 0 18px 40px !important;
}

.main,
.contain {
  margin: 0 auto !important;
  max-width: 760px !important;
  padding: 32px 0 0 !important;
}

footer {
  display: none !important;
}

.app-shell {
  display: grid !important;
  gap: 24px !important;
}

.page-header {
  text-align: center;
}

.page-header h1 {
  color: var(--ink);
  font-size: 24px;
  font-weight: 650;
  letter-spacing: -0.02em;
  margin: 0 0 10px;
}

.page-header p {
  color: var(--muted);
  font-size: 16px;
  line-height: 1.6;
  margin: 0 auto;
  max-width: 620px;
}

.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 22px;
}

.section-label {
  color: var(--ink);
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 14px;
}

.setup-note {
  color: var(--muted);
  font-size: 15px;
  line-height: 1.55;
  margin: 0 0 14px;
}

.question-card,
.feedback-card,
.summary-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 22px;
}

.question-meta {
  align-items: center;
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}

.pill {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  color: var(--blue);
  display: inline-flex;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 12px;
}

.pill.teal {
  background: var(--teal-soft);
  border-color: #99f6e4;
  color: #0f766e;
}

.question-copy {
  color: var(--ink);
  font-size: 16px;
  line-height: 1.65;
  margin: 0;
}

.score-list {
  display: grid;
  gap: 12px;
  margin: 0 0 18px;
}

.score-row {
  align-items: center;
  background: var(--surface-soft);
  border: 1px solid var(--line);
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  padding: 12px 14px;
}

.score-row span {
  color: var(--muted);
  font-size: 15px;
}

.score-row strong {
  color: var(--ink);
  font-size: 15px;
  font-weight: 600;
}

.feedback-copy {
  color: var(--ink);
  display: grid;
  gap: 14px;
}

.feedback-block strong {
  color: var(--teal);
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
}

.feedback-block p {
  color: var(--ink);
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
}

.summary-copy {
  color: var(--muted);
  font-size: 15px;
  line-height: 1.65;
  margin: 0;
}

.empty-state {
  color: var(--muted);
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
}

.controls-row {
  align-items: end;
  display: grid !important;
  gap: 12px !important;
  grid-template-columns: minmax(0, 1fr) auto;
}

.submit-row {
  display: grid !important;
  gap: 12px !important;
  grid-template-columns: minmax(0, 1fr);
}

.control-label {
  color: var(--ink);
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 8px;
}

button,
textarea,
input,
select {
  font-family: inherit !important;
}

button {
  border-radius: 12px !important;
  box-shadow: none !important;
  font-weight: 600 !important;
  min-height: 46px !important;
}

.gr-button-primary,
.generate-button button,
.submit-button button {
  background: var(--blue) !important;
  border: 1px solid var(--blue) !important;
  color: #ffffff !important;
}

.gr-button-primary:hover,
.generate-button button:hover,
.submit-button button:hover {
  background: var(--blue-dark) !important;
  border-color: var(--blue-dark) !important;
}

.secondary-button button {
  background: #ffffff !important;
  border: 1px solid var(--line) !important;
  color: var(--ink) !important;
}

.secondary-button button:hover {
  background: var(--surface-soft) !important;
}

textarea,
input,
select,
.gr-box,
.gr-input,
.gr-text-input,
.gr-textbox,
.gr-dropdown {
  border-color: var(--line) !important;
}

textarea,
input,
select {
  background: #ffffff !important;
  border-radius: 12px !important;
  color: var(--ink) !important;
  font-size: 15px !important;
}

textarea {
  line-height: 1.6 !important;
  min-height: 190px !important;
}

.answer-box textarea {
  padding: 14px 16px !important;
}

label,
.gradio-container .block-title {
  color: var(--ink) !important;
  font-weight: 600 !important;
}

@media (max-width: 640px) {
  .gradio-container {
    padding: 0 14px 32px !important;
  }

  .panel,
  .question-card,
  .feedback-card,
  .summary-card {
    padding: 18px;
  }

  .controls-row,
  .submit-row {
    grid-template-columns: minmax(0, 1fr) !important;
  }

  .generate-button button,
  .submit-button button,
  .secondary-button button {
    width: 100% !important;
  }
}
"""


def build_gradio_demo():
    import gradio as gr

    with gr.Blocks(title="InterviewEnv", theme=gr.themes.Soft(primary_hue="blue"), css=APP_CSS) as demo:
        session_history = gr.State([])
        current_question = gr.State("")

        with gr.Column(elem_classes=["app-shell"]):
            gr.HTML(
                """
                <section class="page-header">
                  <h1>InterviewEnv</h1>
                  <p>Practice interview questions with a clean, focused flow and clear feedback after every answer.</p>
                </section>
                """
            )

            with gr.Group(elem_classes=["panel"]):
                gr.HTML(
                    """
                    <p class="section-label">Interview Setup</p>
                    <p class="setup-note">Choose a difficulty and generate a question to begin.</p>
                    """
                )
                with gr.Row(elem_classes=["controls-row"]):
                    difficulty = gr.Dropdown(
                        label="Difficulty",
                        choices=["Easy", "Medium", "Hard"],
                        value="Easy",
                        interactive=True,
                    )
                    generate_button = gr.Button("Generate Question", variant="primary", elem_classes=["generate-button"])

            with gr.Group(elem_classes=["panel"]):
                gr.HTML('<p class="section-label">Question</p>')
                interviewer_box = gr.HTML(_render_question("Click Generate Question to start your mock interview.", "ready"))

            with gr.Group(elem_classes=["panel"]):
                gr.HTML('<p class="section-label">Your Answer</p>')
                answer_box = gr.Textbox(
                    label="Answer",
                    placeholder="Write a clear answer with context, your action, and the result.",
                    lines=8,
                    elem_classes=["answer-box"],
                )
                with gr.Row(elem_classes=["submit-row"]):
                    submit_button = gr.Button("Submit Answer", variant="primary", elem_classes=["submit-button"])

            with gr.Group(elem_classes=["panel"]):
                gr.HTML('<p class="section-label">Feedback</p>')
                feedback_box = gr.HTML(_render_empty_feedback())

            with gr.Group(elem_classes=["panel"]):
                gr.HTML('<p class="section-label">Session Summary</p>')
                summary_box = gr.HTML(_render_summary([]))

        generate_button.click(
            fn=_on_generate_question,
            inputs=[difficulty, session_history],
            outputs=[interviewer_box, feedback_box, answer_box, current_question, session_history, summary_box],
        )
        submit_button.click(
            fn=_on_submit_answer,
            inputs=[difficulty, current_question, answer_box, session_history],
            outputs=[feedback_box, answer_box, session_history, summary_box],
        )

    return demo


def _on_generate_question(difficulty: str, history: list[dict] | None):
    task_id = normalize_difficulty(difficulty)
    updated_history = list(history or [])
    question = generate_question(task_id, updated_history)
    updated_history.append({"difficulty": task_id, "question": question})
    return (
        _render_question(question, task_id),
        _render_empty_feedback("Question ready. Submit your answer to receive feedback."),
        "",
        question,
        updated_history,
        _render_summary(updated_history),
    )


def _on_submit_answer(difficulty: str, question: str, answer: str, history: list[dict] | None):
    question = question or generate_question(difficulty, history)
    updated_history = list(history or [])
    time.sleep(0.25)
    feedback = evaluate_answer(difficulty, question, answer, updated_history)
    score = _extract_score(feedback)
    if updated_history:
        updated_history[-1].update({"answer": answer, "feedback": feedback, "score": score})
    else:
        updated_history.append(
            {
                "difficulty": normalize_difficulty(difficulty),
                "question": question,
                "answer": answer,
                "feedback": feedback,
                "score": score,
            }
        )
    return _render_feedback(feedback), "", updated_history, _render_summary(updated_history)


def _render_question(question: str, difficulty: str) -> str:
    safe_question = html.escape(question)
    safe_difficulty = html.escape(difficulty.title())
    accent_class = "pill teal" if difficulty == "ready" else "pill"
    accent_label = "Ready" if difficulty == "ready" else safe_difficulty
    return f"""
    <div class="question-card">
      <div class="question-meta">
        <span class="{accent_class}">{accent_label}</span>
      </div>
      <p class="question-copy">{safe_question}</p>
    </div>
    """


def _render_empty_feedback(message: str = "Feedback will appear here after you submit an answer.") -> str:
    return f"""
    <div class="feedback-card">
      <p class="empty-state">{html.escape(message)}</p>
    </div>
    """


def _render_feedback(feedback: str) -> str:
    parsed = _parse_feedback(feedback)
    return f"""
    <div class="feedback-card">
      <div class="score-list">
        <div class="score-row"><span>Overall score</span><strong>{html.escape(parsed["score"])}</strong></div>
      </div>
      <div class="feedback-copy">
        <div class="feedback-block">
          <strong>Strengths</strong>
          <p>{html.escape(parsed["strengths"])}</p>
        </div>
        <div class="feedback-block">
          <strong>Needs work</strong>
          <p>{html.escape(parsed["weakness"])}</p>
        </div>
        <div class="feedback-block">
          <strong>How to improve</strong>
          <p>{html.escape(parsed["improve_by"])}</p>
        </div>
      </div>
    </div>
    """


def _render_summary(history: list[dict]) -> str:
    answered = [item for item in history if item.get("answer")]
    if not answered:
        return """
        <div class="summary-card">
          <p class="summary-copy">No answers submitted yet. Generate a question to begin your practice session.</p>
        </div>
        """
    latest = answered[-1]
    average = round(sum(int(item.get("score", 0)) for item in answered) / len(answered), 1)
    return f"""
    <div class="summary-card">
      <p class="summary-copy">
        {len(answered)} answer(s) submitted. Average score: <strong>{average}/10</strong>.
        Latest difficulty: <strong>{html.escape(str(latest.get("difficulty", "easy")).title())}</strong>.
      </p>
    </div>
    """


def _parse_feedback(feedback: str) -> dict[str, str]:
    parsed = {
        "score": "0/10",
        "strengths": "No feedback yet.",
        "weakness": "No feedback yet.",
        "improve_by": "Submit an answer to receive guidance.",
    }
    for line in feedback.splitlines():
        if line.startswith("Score:"):
            parsed["score"] = line.replace("Score:", "", 1).strip()
        elif line.startswith("Strengths:"):
            parsed["strengths"] = line.replace("Strengths:", "", 1).strip()
        elif line.startswith("Weakness:"):
            parsed["weakness"] = line.replace("Weakness:", "", 1).strip()
        elif line.startswith("Improve by:"):
            parsed["improve_by"] = line.replace("Improve by:", "", 1).strip()
    return parsed


def _extract_score(feedback: str) -> int:
    first_line = feedback.splitlines()[0] if feedback else "Score: 0/10"
    try:
        return int(first_line.split("Score:", 1)[1].split("/10", 1)[0].strip())
    except (IndexError, ValueError):
        return 0
