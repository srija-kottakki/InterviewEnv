const taskSelect = document.querySelector("#taskSelect");
const resetButton = document.querySelector("#resetButton");
const answerForm = document.querySelector("#answerForm");
const answerInput = document.querySelector("#answerInput");
const submitButton = document.querySelector("#submitButton");
const chat = document.querySelector("#chat");
const turnBadge = document.querySelector("#turnBadge");
const reward = document.querySelector("#reward");
const done = document.querySelector("#done");
const difficulty = document.querySelector("#difficulty");
const info = document.querySelector("#info");

let history = [];

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
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
}

function renderChat() {
  if (history.length === 0) {
    chat.innerHTML = '<p class="empty">Choose a task and start the interview.</p>';
    return;
  }
  chat.innerHTML = history
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
  done.textContent = String(state.done);
  history = state.history;
  renderChat();
  answerInput.disabled = state.done;
  submitButton.disabled = state.done;
}

resetButton.addEventListener("click", async () => {
  resetButton.disabled = true;
  try {
    const data = await request(`/reset?task_id=${encodeURIComponent(taskSelect.value)}`);
    renderState(data.state);
    reward.textContent = "--";
    info.textContent = JSON.stringify(data.info, null, 2);
  } catch (error) {
    info.textContent = error.message;
  } finally {
    resetButton.disabled = false;
  }
});

answerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = answerInput.value.trim();
  if (!message) {
    return;
  }
  answerInput.value = "";
  submitButton.disabled = true;
  try {
    const data = await request("/step", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    renderState(data.state);
    reward.textContent = data.reward.toFixed(4);
    done.textContent = String(data.done);
    info.textContent = JSON.stringify(data.info, null, 2);
  } catch (error) {
    info.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});
