from __future__ import annotations

import html
import time

from interview_logic import evaluate_answer, generate_question, normalize_difficulty


APP_CSS = """
:root {
  --surface: #ffffff;
  --muted: #64748b;
  --ink: #0f172a;
  --line: #e2e8f0;
  --blue: #2563eb;
  --blue-dark: #1d4ed8;
  --green: #16a34a;
}

.gradio-container {
  max-width: 1120px !important;
  margin: 0 auto !important;
  background: #f8fafc !important;
  color: var(--ink) !important;
}

footer {
  display: none !important;
}

.hero-card {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
  border-radius: 28px;
  color: white;
  margin-bottom: 18px;
  padding: 30px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
}

.hero-card h1 {
  font-size: 44px;
  letter-spacing: -0.04em;
  line-height: 1;
  margin: 0 0 8px;
}

.hero-card p {
  color: #dbeafe;
  font-size: 16px;
  margin: 0;
  max-width: 780px;
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.step-pill {
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 999px;
  color: #eff6ff;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 12px;
}

.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 24px;
  box-shadow: 0 18px 55px rgba(15, 23, 42, 0.08);
  padding: 18px;
}

.section-label {
  color: var(--blue-dark);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.12em;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.question-card {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 22px;
  padding: 20px;
}

.question-card h3 {
  color: #1d4ed8;
  font-size: 14px;
  letter-spacing: 0.1em;
  margin: 0 0 12px;
  text-transform: uppercase;
}

.question-card p {
  color: #0f172a;
  font-size: 22px;
  font-weight: 750;
  line-height: 1.38;
  margin: 0;
}

.feedback-card {
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 18px;
}

.score-badge {
  align-items: center;
  background: #dcfce7;
  border: 1px solid #bbf7d0;
  border-radius: 999px;
  color: #166534;
  display: inline-flex;
  font-size: 16px;
  font-weight: 900;
  margin-bottom: 14px;
  padding: 8px 14px;
}

.feedback-grid {
  display: grid;
  gap: 12px;
}

.feedback-item {
  background: #f8fafc;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 14px;
}

.feedback-item strong {
  color: #0f172a;
  display: block;
  margin-bottom: 4px;
}

.feedback-item span {
  color: #475569;
}

.summary-card {
  background: #f8fafc;
  border: 1px solid var(--line);
  border-radius: 18px;
  color: #334155;
  font-size: 14px;
  line-height: 1.55;
  padding: 14px;
}

.empty-state {
  color: var(--muted);
  font-size: 15px;
  line-height: 1.5;
}

.gr-button-primary {
  background: var(--blue) !important;
  border-color: var(--blue) !important;
}

.gr-button-primary:hover {
  background: var(--blue-dark) !important;
}
"""


def build_gradio_demo():
    import gradio as gr

    with gr.Blocks(title="InterviewEnv", theme=gr.themes.Soft(primary_hue="blue"), css=APP_CSS) as demo:
        session_history = gr.State([])
        current_question = gr.State("")

        gr.HTML(
            """
            <section class="hero-card">
              <h1>InterviewEnv</h1>
              <p>AI mock interview simulator with adaptive questions and real-time interviewer-style feedback.</p>
              <div class="pill-row">
                <span class="step-pill">1. Select difficulty</span>
                <span class="step-pill">2. Generate question</span>
                <span class="step-pill">3. Submit answer</span>
                <span class="step-pill">4. Improve with feedback</span>
              </div>
            </section>
            """
        )

        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                with gr.Group(elem_classes=["panel"]):
                    gr.HTML('<div class="section-label">Interview Setup</div>')
                    with gr.Row():
                        difficulty = gr.Dropdown(
                            label="Select Difficulty",
                            choices=["Easy", "Medium", "Hard"],
                            value="Easy",
                            interactive=True,
                        )
                        generate_button = gr.Button("Generate Question", variant="primary")
                    gr.HTML(
                        """
                        <div class="empty-state">
                          Tip: For a strong answer, include context, your action, and the result.
                        </div>
                        """
                    )

            with gr.Column(scale=3):
                with gr.Group(elem_classes=["panel"]):
                    gr.HTML('<div class="section-label">Session Summary</div>')
                    summary_box = gr.HTML(_render_summary([]))

        with gr.Group(elem_classes=["panel"]):
            interviewer_box = gr.HTML(_render_question("Click Generate Question to start your mock interview.", "ready"))

        with gr.Row(equal_height=True):
            with gr.Column(scale=5):
                with gr.Group(elem_classes=["panel"]):
                    gr.HTML('<div class="section-label">Your Answer</div>')
                    answer_box = gr.Textbox(
                        label="",
                        placeholder="Type your answer here. Example: Using STAR, the situation was...",
                        lines=8,
                        show_label=False,
                    )
                    with gr.Row():
                        sample_button = gr.Button("Use Sample Answer")
                        submit_button = gr.Button("Submit Answer", variant="primary")

            with gr.Column(scale=4):
                with gr.Group(elem_classes=["panel"]):
                    gr.HTML('<div class="section-label">Feedback</div>')
                    feedback_box = gr.HTML(_render_empty_feedback())

        generate_button.click(
            fn=_on_generate_question,
            inputs=[difficulty, session_history],
            outputs=[interviewer_box, feedback_box, answer_box, current_question, session_history, summary_box],
        )
        sample_button.click(
            fn=_sample_answer,
            inputs=[difficulty, current_question],
            outputs=[answer_box],
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


def _sample_answer(difficulty: str, question: str) -> str:
    task_id = normalize_difficulty(difficulty)
    if task_id == "hard":
        return (
            "Using STAR, the situation was a team project with unclear ownership and a tight deadline. "
            "My task was to clarify responsibilities and reduce delivery risk. I communicated the tradeoffs, "
            "took ownership of the highest-risk part, measured progress daily, and helped the team deliver a working result. "
            "The lesson was to align ownership earlier."
        )
    if task_id == "medium":
        return (
            "First, I defined the project goal and constraints. Then I compared speed versus reliability and chose the safer approach "
            "because correctness mattered more than a quick prototype. I measured success with tests, user feedback, and performance metrics, "
            "and I would improve observability next time."
        )
    return (
        "I am interested in this role because it matches my project experience, teamwork, and communication strengths. "
        "I enjoy building useful systems, explaining technical choices clearly, and learning from feedback."
    )


def _render_question(question: str, difficulty: str) -> str:
    safe_question = html.escape(question)
    safe_difficulty = html.escape(difficulty.title())
    return f"""
    <div class="question-card">
      <h3>Interviewer · {safe_difficulty}</h3>
      <p>{safe_question}</p>
    </div>
    """


def _render_empty_feedback(message: str = "Feedback will appear here after you submit an answer.") -> str:
    return f"""
    <div class="feedback-card">
      <div class="empty-state">{html.escape(message)}</div>
    </div>
    """


def _render_feedback(feedback: str) -> str:
    parsed = _parse_feedback(feedback)
    return f"""
    <div class="feedback-card">
      <div class="score-badge">Score: {html.escape(parsed["score"])}</div>
      <div class="feedback-grid">
        <div class="feedback-item"><strong>Strengths</strong><span>{html.escape(parsed["strengths"])}</span></div>
        <div class="feedback-item"><strong>Weakness</strong><span>{html.escape(parsed["weakness"])}</span></div>
        <div class="feedback-item"><strong>Improve by</strong><span>{html.escape(parsed["improve_by"])}</span></div>
      </div>
    </div>
    """


def _render_summary(history: list[dict]) -> str:
    answered = [item for item in history if item.get("answer")]
    if not answered:
        return """
        <div class="summary-card">
          <strong>0 answers submitted</strong><br />
          Generate a question to begin the interview.
        </div>
        """
    latest = answered[-1]
    average = round(sum(int(item.get("score", 0)) for item in answered) / len(answered), 1)
    return f"""
    <div class="summary-card">
      <strong>{len(answered)} answer(s) submitted</strong><br />
      Average score: <strong>{average}/10</strong><br />
      Latest difficulty: <strong>{html.escape(str(latest.get("difficulty", "easy")).title())}</strong>
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
