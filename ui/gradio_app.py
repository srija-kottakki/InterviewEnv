from __future__ import annotations

import time

import gradio as gr

from interview_logic import evaluate_answer, generate_question, normalize_difficulty


APP_CSS = """
.gradio-container {
  max-width: 980px !important;
  margin: 0 auto !important;
  background: #f8fafc !important;
}
.hero-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}
.hero-card h1 {
  margin-bottom: 4px;
}
.flow-note {
  color: #475569;
  font-size: 0.95rem;
}
"""


def build_gradio_demo() -> gr.Blocks:
    with gr.Blocks(title="InterviewEnv", theme=gr.themes.Soft(primary_hue="blue"), css=APP_CSS) as demo:
        session_history = gr.State([])
        current_question = gr.State("")

        gr.HTML(
            """
            <section class="hero-card">
              <h1>InterviewEnv</h1>
              <p><strong>AI Mock Interview Practice</strong></p>
              <p class="flow-note">Select a difficulty, generate a question, answer like a candidate, and get real-time interviewer feedback.</p>
            </section>
            """
        )

        with gr.Row():
            difficulty = gr.Dropdown(
                label="Select Difficulty",
                choices=["Easy", "Medium", "Hard"],
                value="Easy",
                interactive=True,
            )
            generate_button = gr.Button("Generate Question", variant="primary")

        interviewer_box = gr.Textbox(
            label="Interviewer",
            value="Click Generate Question to start your mock interview.",
            lines=3,
            interactive=False,
        )
        answer_box = gr.Textbox(
            label="Your Answer",
            placeholder="Type your answer here. Try to include context, your action, and the result.",
            lines=6,
        )
        submit_button = gr.Button("Submit Answer", variant="primary")
        feedback_box = gr.Textbox(label="Feedback", lines=7, interactive=False)

        generate_button.click(
            fn=_on_generate_question,
            inputs=[difficulty, session_history],
            outputs=[interviewer_box, feedback_box, answer_box, current_question, session_history],
        )
        submit_button.click(
            fn=_on_submit_answer,
            inputs=[difficulty, current_question, answer_box, session_history],
            outputs=[feedback_box, answer_box, session_history],
        )

    return demo


def _on_generate_question(difficulty: str, history: list[dict] | None):
    task_id = normalize_difficulty(difficulty)
    updated_history = list(history or [])
    question = generate_question(task_id, updated_history)
    updated_history.append({"difficulty": task_id, "question": question})
    return f"Interviewer: {question}", "", "", question, updated_history


def _on_submit_answer(difficulty: str, question: str, answer: str, history: list[dict] | None):
    question = question or generate_question(difficulty, history)
    updated_history = list(history or [])
    time.sleep(0.25)
    feedback = evaluate_answer(difficulty, question, answer, updated_history)
    score = _extract_score(feedback)
    if updated_history:
        updated_history[-1].update({"answer": answer, "feedback": feedback, "score": score})
    else:
        updated_history.append({"difficulty": normalize_difficulty(difficulty), "question": question, "answer": answer, "feedback": feedback, "score": score})
    return feedback, "", updated_history


def _extract_score(feedback: str) -> int:
    first_line = feedback.splitlines()[0] if feedback else "Score: 0/10"
    try:
        return int(first_line.split("Score:", 1)[1].split("/10", 1)[0].strip())
    except (IndexError, ValueError):
        return 0
