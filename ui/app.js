const state = {
  current: null,
  lastStep: null,
  metadata: null,
};

const difficultyEl = document.getElementById("difficulty");
const strategyEl = document.getElementById("strategy");
const confidenceEl = document.getElementById("confidence");
const confidenceValueEl = document.getElementById("confidenceValue");
const resumeFileEl = document.getElementById("resumeFile");
const resumeStatusEl = document.getElementById("resumeStatus");
const answerInputEl = document.getElementById("answerInput");
const appStatusEl = document.getElementById("appStatus");
const questionCardEl = document.getElementById("questionCard");
const taskBadgeEl = document.getElementById("taskBadge");
const turnBadgeEl = document.getElementById("turnBadge");
const scorePillEl = document.getElementById("scorePill");
const averageScoreEl = document.getElementById("averageScore");
const clarityScoreEl = document.getElementById("clarityScore");
const confidenceScoreEl = document.getElementById("confidenceScore");
const relevanceScoreEl = document.getElementById("relevanceScore");
const commentsTextEl = document.getElementById("commentsText");
const adaptiveReasonEl = document.getElementById("adaptiveReason");
const followUpTextEl = document.getElementById("followUpText");
const totalScoreEl = document.getElementById("totalScore");
const difficultyLevelEl = document.getElementById("difficultyLevel");
const scoreTrendEl = document.getElementById("scoreTrend");
const stressLevelEl = document.getElementById("stressLevel");
const stateViewerEl = document.getElementById("stateViewer");
const errorBannerEl = document.getElementById("errorBanner");

document.getElementById("startButton").addEventListener("click", startInterview);
document.getElementById("submitButton").addEventListener("click", submitAnswer);
document.getElementById("refreshButton").addEventListener("click", refreshState);
document.getElementById("uploadButton").addEventListener("click", uploadResume);
document.getElementById("clearButton").addEventListener("click", () => {
  answerInputEl.value = "";
  answerInputEl.focus();
});
confidenceEl.addEventListener("input", () => {
  confidenceValueEl.textContent = `${confidenceEl.value}%`;
});

init();

async function init() {
  confidenceValueEl.textContent = `${confidenceEl.value}%`;
  setStatus("Loading");
  clearError();

  try {
    state.metadata = await requestJson("/metadata");
    const existingState = await requestJson("/state");
    renderState(existingState);
    setStatus("Ready");
  } catch (error) {
    showError(error.message);
    setStatus("Offline");
  }
}

async function startInterview() {
  clearError();
  setStatus("Generating");

  try {
    const taskId = difficultyEl.value;
    const response = await requestJson(`/reset?task_id=${encodeURIComponent(taskId)}`);
    state.lastStep = null;
    renderState(response);
    answerInputEl.value = "";
    answerInputEl.focus();
    setStatus("Question ready");
  } catch (error) {
    showError(error.message);
    setStatus("Retry");
  }
}

async function refreshState() {
  clearError();
  setStatus("Refreshing");

  try {
    const response = await requestJson("/state");
    renderState(response);
    setStatus("Synced");
  } catch (error) {
    showError(error.message);
    setStatus("Retry");
  }
}

async function uploadResume() {
  clearError();

  if (!resumeFileEl.files.length) {
    showError("Choose a PDF or text file before uploading.");
    return;
  }

  const file = resumeFileEl.files[0];
  const formData = new FormData();
  formData.append("file", file);

  setStatus("Uploading resume");
  resumeStatusEl.textContent = `Uploading ${file.name}...`;

  try {
    const response = await fetch("/upload_resume", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(await extractError(response));
    }

    const data = await response.json();
    renderState(data);
    resumeStatusEl.textContent = `${file.name} uploaded. Future questions can use your resume context.`;
    setStatus("Resume ready");
  } catch (error) {
    showError(error.message);
    resumeStatusEl.textContent = "Upload failed. Please try a PDF or text resume.";
    setStatus("Retry");
  }
}

async function submitAnswer() {
  clearError();
  const answer = answerInputEl.value.trim();

  if (!answer) {
    showError("Write an answer before submitting.");
    return;
  }

  setStatus("Evaluating");

  try {
    const confidence = Number(confidenceEl.value) / 100;
    const confidenceLevel = Math.max(1, Math.min(5, Math.round(confidence * 5)));
    const strategy = strategyEl.value;

    const response = await requestJson("/step", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        answer,
        answer_strategy: strategy,
        strategy,
        confidence,
        confidence_level: confidenceLevel,
        tone: confidence >= 0.7 ? "confident" : "neutral",
      }),
    });

    state.lastStep = response;
    const nextState = await requestJson("/state");
    renderState(nextState);
    answerInputEl.value = "";
    setStatus(response.done ? "Complete" : "Feedback ready");
  } catch (error) {
    showError(error.message);
    setStatus("Retry");
  }
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(await extractError(response));
  }
  return response.json();
}

async function extractError(response) {
  try {
    const data = await response.json();
    return data.detail || JSON.stringify(data);
  } catch (_) {
    return `${response.status} ${response.statusText}`;
  }
}

function renderState(nextState) {
  state.current = nextState;
  const taskLabel = titleCase(nextState.task_id || "easy");
  const stepFeedback = state.lastStep;
  const feedback = stepFeedback?.info?.behavioral_feedback || nextState.behavioral_feedback || {};
  const learning = stepFeedback?.info?.learning_metrics || nextState.learning_metrics || {};
  const rewardBreakdown = stepFeedback?.info?.reward_breakdown || nextState.reward_breakdown || {};
  const relevance = Number(stepFeedback?.info?.relevance_score || rewardBreakdown.correctness || 0);
  const score = Number(stepFeedback?.reward || 0);

  questionCardEl.innerHTML = escapeHtml(
    nextState.current_question || "Click Generate Question to begin your mock interview."
  ).replace(/\n/g, "<br>");
  taskBadgeEl.textContent = `${taskLabel} interview`;
  turnBadgeEl.textContent = `Turn ${nextState.turn} / ${nextState.max_turns}`;
  scorePillEl.textContent = stepFeedback ? `Score ${(score * 10).toFixed(1)} / 10` : "Score --";

  averageScoreEl.textContent = formatMetric(Number(learning.average_score || 0) * 10);
  clarityScoreEl.textContent = formatMetric(Number(feedback.clarity_score || 0) * 10);
  confidenceScoreEl.textContent = formatMetric(Number(feedback.confidence_score || 0) * 10);
  relevanceScoreEl.textContent = formatMetric(relevance * 10);

  commentsTextEl.textContent =
    feedback.comments || "Submit an answer to see personalized feedback.";
  adaptiveReasonEl.textContent =
    nextState.adaptive_reason || "Difficulty updates and coaching notes will appear here.";
  followUpTextEl.textContent =
    stepFeedback?.info?.follow_up_question || "No follow-up question yet.";

  totalScoreEl.textContent = formatMetric(Number(learning.total_score || nextState.score || 0));
  difficultyLevelEl.textContent = `${nextState.current_difficulty || 1} / 3`;
  scoreTrendEl.textContent = titleCase(nextState.score_trend || "flat");
  stressLevelEl.textContent = Number(nextState.stress_level || 0).toFixed(2);

  stateViewerEl.textContent = JSON.stringify(nextState, null, 2);
}

function setStatus(label) {
  appStatusEl.textContent = label;
}

function showError(message) {
  errorBannerEl.textContent = message;
  errorBannerEl.classList.remove("hidden");
}

function clearError() {
  errorBannerEl.textContent = "";
  errorBannerEl.classList.add("hidden");
}

function titleCase(value) {
  return String(value)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function formatMetric(value) {
  return Number.isFinite(value) ? value.toFixed(1) : "0.0";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
