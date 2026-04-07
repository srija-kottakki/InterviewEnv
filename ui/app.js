const taskSelect = document.querySelector("#taskSelect");
const resumeForm = document.querySelector("#resumeForm");
const resumeInput = document.querySelector("#resumeInput");
const uploadButton = document.querySelector("#uploadButton");
const resetButton = document.querySelector("#resetButton");
const strategySelect = document.querySelector("#strategySelect");
const confidenceSelect = document.querySelector("#confidenceSelect");
const toneSelect = document.querySelector("#toneSelect");
const answerForm = document.querySelector("#answerForm");
const answerInput = document.querySelector("#answerInput");
const submitButton = document.querySelector("#submitButton");
const chat = document.querySelector("#chat");
const turnBadge = document.querySelector("#turnBadge");
const reward = document.querySelector("#reward");
const done = document.querySelector("#done");
const difficulty = document.querySelector("#difficulty");
const adaptiveLevel = document.querySelector("#adaptiveLevel");
const stressLevel = document.querySelector("#stressLevel");
const scoreTrend = document.querySelector("#scoreTrend");
const feedbackViewer = document.querySelector("#feedbackViewer");
const resumeViewer = document.querySelector("#resumeViewer");
const errorBox = document.querySelector("#error");
const stateViewer = document.querySelector("#stateViewer");
const metadataViewer = document.querySelector("#metadataViewer");
const refreshStateButton = document.querySelector("#refreshStateButton");
const refreshMetadataButton = document.querySelector("#refreshMetadataButton");

let currentHistory = [];

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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
}

function renderJson(node, data) {
  node.textContent = JSON.stringify(data, null, 2);
}

function renderChat() {
  if (currentHistory.length === 0) {
    chat.innerHTML = '<p class="empty">Choose a task and press Reset.</p>';
    return;
  }
  chat.innerHTML = currentHistory
    .map(
      (item) => `
        <div class="message ${escapeHtml(item.role)}">
          <strong>${escapeHtml(item.role)}</strong>
          ${escapeHtml(item.content)}
        </div>
      `,
    )
    .join("");
  chat.scrollTop = chat.scrollHeight;
}

function renderState(state) {
  turnBadge.textContent = `${state.turn}/${state.max_turns}`;
  difficulty.textContent = state.difficulty;
  adaptiveLevel.textContent = String(state.current_difficulty);
  stressLevel.textContent = Number(state.stress_level || 0).toFixed(2);
  scoreTrend.textContent = state.score_trend || "flat";
  done.textContent = String(state.done);
  currentHistory = state.history;
  renderChat();
  renderJson(stateViewer, state);
  renderJson(feedbackViewer, {
    behavioral_feedback: state.behavioral_feedback,
    reward_breakdown: state.reward_breakdown,
    last_action: state.last_action,
    score_history: state.score_history,
    adaptive_reason: state.adaptive_reason,
    follow_up_question: state.current_question,
    current_question: state.current_question,
  });
  const resumeContext =
    state.parsed_resume_data && Object.keys(state.parsed_resume_data).length > 0
      ? state.parsed_resume_data
      : { status: "No resume uploaded. Using general interview questions." };
  renderJson(resumeViewer, resumeContext);
  answerInput.disabled = state.done;
  submitButton.disabled = state.done;
}

async function refreshState() {
  const data = await request("/state");
  renderState(data);
}

async function refreshMetadata() {
  const data = await request("/metadata");
  renderJson(metadataViewer, data);
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.tab}`).classList.add("active");
  });
});

resetButton.addEventListener("click", async () => {
  resetButton.disabled = true;
  setError();
  try {
    const data = await request(`/reset?task_id=${encodeURIComponent(taskSelect.value)}`);
    renderState(data);
    reward.textContent = "--";
    renderJson(metadataViewer, { reset: data });
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
    setError("Enter an action.message before stepping.");
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
        answer_strategy: strategySelect.value,
        confidence_level: Number(confidenceSelect.value),
        tone: toneSelect.value,
      }),
    });
    const state = await request("/state");
    renderState(state);
    reward.textContent = data.reward.toFixed(4);
    done.textContent = String(data.done);
    renderJson(metadataViewer, data.info);
  } catch (error) {
    setError(error.message);
  } finally {
    submitButton.disabled = false;
  }
});

refreshStateButton.addEventListener("click", () => refreshState().catch((error) => setError(error.message)));
refreshMetadataButton.addEventListener("click", () => refreshMetadata().catch((error) => setError(error.message)));

refreshMetadata().catch(() => {});
