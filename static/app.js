const state = {
  selectedTask: "easy",
  tasks: [],
  history: [],
  active: false,
};

const taskGrid = document.querySelector("#taskGrid");
const resetButton = document.querySelector("#resetButton");
const answerForm = document.querySelector("#answerForm");
const answerInput = document.querySelector("#answerInput");
const sendButton = document.querySelector("#sendButton");
const chatLog = document.querySelector("#chatLog");
const turnBadge = document.querySelector("#turnBadge");
const rewardMetric = document.querySelector("#rewardMetric");
const rubricMetric = document.querySelector("#rubricMetric");
const specificityMetric = document.querySelector("#specificityMetric");
const progressBar = document.querySelector("#progressBar");
const feedbackBox = document.querySelector("#feedbackBox");
const helperText = document.querySelector("#helperText");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Request failed");
  }

  return response.json();
}

function formatScore(value) {
  return typeof value === "number" ? value.toFixed(2) : "--";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderTasks() {
  taskGrid.innerHTML = state.tasks
    .map(
      (task) => `
        <article class="task-card ${task.id === state.selectedTask ? "active" : ""}" data-task-id="${escapeHtml(task.id)}">
          <h3>${escapeHtml(task.name)}</h3>
          <p>${escapeHtml(task.description)}</p>
          <div class="task-meta">
            <span>${escapeHtml(task.difficulty)}</span>
            <span>${escapeHtml(task.max_turns)} turns</span>
            <span>pass ${escapeHtml(task.pass_threshold)}</span>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderChat() {
  if (state.history.length === 0) {
    chatLog.innerHTML = '<div class="empty-state">Pick a task and start the interview to see the first question.</div>';
    return;
  }

  chatLog.innerHTML = state.history
    .map(
      (message) => `
        <div class="message ${message.role}">
          <strong>${escapeHtml(message.role)}</strong>
          ${escapeHtml(message.content)}
        </div>
      `,
    )
    .join("");
  chatLog.scrollTop = chatLog.scrollHeight;
}

function updateProgress(observation) {
  if (!observation) {
    turnBadge.textContent = "Not started";
    progressBar.style.width = "0%";
    return;
  }

  const progress = Math.min((observation.turn / observation.max_turns) * 100, 100);
  turnBadge.textContent = observation.done
    ? `Complete: ${observation.turn}/${observation.max_turns}`
    : `Turn ${observation.turn}/${observation.max_turns}`;
  progressBar.style.width = `${progress}%`;
}

function setInputEnabled(enabled) {
  answerInput.disabled = !enabled;
  sendButton.disabled = !enabled;
  state.active = enabled;
}

function setLoading(isLoading, label) {
  resetButton.disabled = isLoading;
  sendButton.disabled = isLoading || !state.active;
  if (label) {
    helperText.textContent = label;
  }
}

async function loadTasks() {
  const data = await api("/tasks");
  state.tasks = data.tasks;
  state.selectedTask = state.tasks[0]?.id || "easy";
  renderTasks();
}

async function resetInterview() {
  setLoading(true, "Starting a fresh interview...");
  try {
    const observation = await api("/reset", {
      method: "POST",
      body: JSON.stringify({ task_id: state.selectedTask }),
    });
    state.history = [{ role: "interviewer", content: observation.interviewer_message }];
    rewardMetric.textContent = "--";
    rubricMetric.textContent = "--";
    specificityMetric.textContent = "--";
    feedbackBox.textContent = "Interview started. Submit your first candidate response.";
    answerInput.value = "";
    updateProgress(observation);
    setInputEnabled(true);
    renderChat();
  } catch (error) {
    feedbackBox.textContent = error.message;
    setInputEnabled(false);
  } finally {
    setLoading(false, "Aim for 80-140 words with concrete examples.");
  }
}

async function submitAnswer(event) {
  event.preventDefault();
  const message = answerInput.value.trim();
  if (!message) {
    helperText.textContent = "Write an answer before submitting.";
    return;
  }

  state.history.push({ role: "candidate", content: message });
  renderChat();
  answerInput.value = "";
  setLoading(true, "Scoring your response...");

  try {
    const result = await api("/step", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    state.history.push({ role: "interviewer", content: result.observation.interviewer_message });
    rewardMetric.textContent = formatScore(result.reward.reward);
    rubricMetric.textContent = formatScore(result.reward.rubric_score);
    specificityMetric.textContent = formatScore(result.reward.specificity_score);
    feedbackBox.textContent = result.observation.feedback || JSON.stringify(result.reward.info, null, 2);
    updateProgress(result.observation);
    setInputEnabled(!result.done);
    renderChat();
  } catch (error) {
    feedbackBox.textContent = error.message;
    setInputEnabled(true);
  } finally {
    setLoading(false, "Aim for 80-140 words with concrete examples.");
  }
}

taskGrid.addEventListener("click", (event) => {
  const card = event.target.closest(".task-card");
  if (!card) {
    return;
  }

  state.selectedTask = card.dataset.taskId;
  state.history = [];
  setInputEnabled(false);
  updateProgress(null);
  feedbackBox.textContent = "Task selected. Start the interview when you are ready.";
  renderTasks();
  renderChat();
});

resetButton.addEventListener("click", resetInterview);
answerForm.addEventListener("submit", submitAnswer);

loadTasks().catch((error) => {
  taskGrid.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
});
