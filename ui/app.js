const taskSelect = document.querySelector("#taskSelect");
const resumeForm = document.querySelector("#resumeForm");
const resumeInput = document.querySelector("#resumeInput");
const uploadButton = document.querySelector("#uploadButton");
const resetButton = document.querySelector("#resetButton");
const answerForm = document.querySelector("#answerForm");
const answerInput = document.querySelector("#answerInput");
const submitButton = document.querySelector("#submitButton");
const questionCard = document.querySelector("#questionCard");
const feedbackBox = document.querySelector("#feedbackBox");
const summaryBox = document.querySelector("#summaryBox");
const errorBox = document.querySelector("#error");
const stateViewer = document.querySelector("#stateViewer");
const metadataViewer = document.querySelector("#metadataViewer");
const resumeViewer = document.querySelector("#resumeViewer");
const refreshStateButton = document.querySelector("#refreshStateButton");
const refreshMetadataButton = document.querySelector("#refreshMetadataButton");

let latestReward = null;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function toTitleCase(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function formatScore(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "--";
  }
  return `${(numeric * 10).toFixed(1)}/10`;
}

function renderJson(node, data) {
  node.textContent = JSON.stringify(data, null, 2);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.detail || response.statusText || "Request failed");
  }
  return data;
}

function setError(message = "") {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

function renderQuestion(state) {
  if (!state) {
    questionCard.innerHTML = `
      <div class="pill-row">
        <span class="pill pill-teal">Ready</span>
      </div>
      <p class="question-text">Click Generate Question to start your mock interview.</p>
    `;
    return;
  }

  const progressLabel = state.done
    ? "Complete"
    : `Turn ${Math.min(state.turn + 1, state.max_turns)} of ${state.max_turns}`;

  questionCard.innerHTML = `
    <div class="pill-row">
      <span class="pill pill-blue">${escapeHtml(toTitleCase(state.difficulty))}</span>
      <span class="pill pill-teal">${escapeHtml(progressLabel)}</span>
    </div>
    <p class="question-text">${escapeHtml(state.current_question)}</p>
  `;
}

function renderFeedback(state) {
  if (!state || state.score_history.length === 0) {
    feedbackBox.innerHTML = '<p class="empty-text">Feedback will appear here after you submit an answer.</p>';
    return;
  }

  const latestKnownReward = latestReward ?? state.score_history[state.score_history.length - 1];
  const metrics = [
    ["Latest reward", formatScore(latestKnownReward)],
    ["Correctness", formatScore(state.reward_breakdown?.correctness)],
    ["Clarity", formatScore(state.behavioral_feedback?.clarity_score)],
    ["Confidence", formatScore(state.behavioral_feedback?.confidence_score)],
  ];

  feedbackBox.innerHTML = `
    <div class="score-list">
      ${metrics
        .map(
          ([label, value]) => `
            <div class="score-row">
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(value)}</strong>
            </div>
          `,
        )
        .join("")}
    </div>
    <div class="feedback-stack">
      <div class="feedback-block">
        <strong>Speaking signals</strong>
        <p>${escapeHtml(state.behavioral_feedback?.comments || "Submit an answer to receive feedback.")}</p>
      </div>
      <div class="feedback-block">
        <strong>Adaptive note</strong>
        <p>${escapeHtml(state.adaptive_reason || "The next question will adapt as you continue.")}</p>
      </div>
      <div class="feedback-block">
        <strong>Current level</strong>
        <p>${escapeHtml(`Difficulty ${toTitleCase(state.difficulty)} · Adaptive level ${state.current_difficulty}`)}</p>
      </div>
    </div>
  `;
}

function renderSummary(state) {
  if (!state || state.score_history.length === 0) {
    summaryBox.innerHTML = "<p>No answers submitted yet. Generate a question to begin your practice session.</p>";
    return;
  }

  const answersSubmitted = state.qa_history?.length || state.score_history.length || 0;
  const averageScore = Number(state.learning_metrics?.average_score || 0);
  const statusText = state.done ? "Session complete." : "Session in progress.";

  summaryBox.innerHTML = `
    <p>
      ${escapeHtml(String(answersSubmitted))} answer(s) submitted. Average score: <strong>${escapeHtml(
        formatScore(averageScore),
      )}</strong>. Trend: <strong>${escapeHtml(toTitleCase(state.score_trend))}</strong>. ${escapeHtml(statusText)}
    </p>
  `;
}

function renderState(state) {
  renderQuestion(state);
  renderFeedback(state);
  renderSummary(state);
  renderJson(stateViewer, state);

  const resumeContext =
    state.parsed_resume_data && Object.keys(state.parsed_resume_data).length > 0
      ? state.parsed_resume_data
      : { status: "No resume uploaded. Using general interview questions." };
  renderJson(resumeViewer, resumeContext);

  answerInput.disabled = state.done;
  submitButton.disabled = state.done;
  answerInput.placeholder = state.done
    ? "Session complete. Generate a new question to start again."
    : "Write a clear answer with context, your action, and the result.";
}

async function refreshState() {
  const data = await request("/state");
  renderState(data);
}

async function refreshMetadata() {
  const data = await request("/metadata");
  renderJson(metadataViewer, data);
}

resetButton.addEventListener("click", async () => {
  resetButton.disabled = true;
  setError();
  try {
    latestReward = null;
    const data = await request(`/reset?task_id=${encodeURIComponent(taskSelect.value)}`);
    answerInput.value = "";
    renderState(data);
  } catch (error) {
    setError(error.message);
  } finally {
    resetButton.disabled = false;
  }
});

resumeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = resumeInput.files[0];
  if (!file) {
    setError("Choose a PDF or text resume first.");
    return;
  }

  uploadButton.disabled = true;
  setError();
  try {
    const body = new FormData();
    body.append("file", file);
    const response = await fetch("/upload_resume", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data?.detail || response.statusText || "Resume upload failed");
    }
    latestReward = null;
    renderState(data);
  } catch (error) {
    setError(error.message);
  } finally {
    uploadButton.disabled = false;
  }
});

answerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = answerInput.value.trim();
  if (!message) {
    setError("Enter an answer before submitting.");
    return;
  }

  answerInput.value = "";
  submitButton.disabled = true;
  setError();
  try {
    const data = await request("/step", {
      method: "POST",
      body: JSON.stringify({
        answer: message,
        answer_strategy: "structured",
        strategy: "structured",
        confidence_level: 3,
        confidence: 0.6,
        tone: "neutral",
      }),
    });
    latestReward = data.reward;
    const state = await request("/state");
    renderState(state);
  } catch (error) {
    setError(error.message);
  } finally {
    submitButton.disabled = false;
  }
});

refreshStateButton.addEventListener("click", () => refreshState().catch((error) => setError(error.message)));
refreshMetadataButton.addEventListener("click", () => refreshMetadata().catch((error) => setError(error.message)));

renderJson(stateViewer, { status: "Generate a question to populate live state." });
renderJson(metadataViewer, { status: "Loading metadata..." });
renderJson(resumeViewer, { status: "No resume uploaded. Using general interview questions." });

refreshMetadata().catch((error) => setError(error.message));
