const $ = (id) => document.getElementById(id);
const API_BASE = "/interview-practice";
const REPORT_KEY = "futureskill_hr_reports_v2";
const pageQuery = new URLSearchParams(window.location.search);
let sessionId = null;
let mediaRecorder = null;
let mediaStream = null;
let chunks = [];
let recording = false;
let currentQuestion = "";
let answerMode = "text";
let providerAvailable = false;
let availableCareers = [];
let feedbackLanguageManuallyChosen = false;

function error(message = "") {
  $("error").textContent = message;
}

function loading(button, isLoading) {
  button.disabled = isLoading || !providerAvailable;
}

async function api(path, options = {}) {
  const response = await fetch(API_BASE + path, options);
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error("The interview service returned an unexpected response.");
  }
  if (!response.ok) throw new Error(body.error || "This action is temporarily unavailable.");
  return body;
}

function jsonPost(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function show(which) {
  for (const id of ["setup", "interview", "report", "historyPage"]) {
    $(id).classList.toggle("hidden", id !== which);
  }
  if (which === "setup") $("careerSearch").focus({ preventScroll: true });
  else document.getElementById(which).scrollIntoView({ block: "start" });
}

function updateAnswerCount() {
  const text = $("answer").value;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  $("answerCount").textContent = `${words} words · ${text.length}/3500 characters`;
}

function setAnswerMode(mode) {
  if (recording) {
    error("Stop recording before switching answer methods.");
    return;
  }
  answerMode = mode;
  $("textMode").setAttribute("aria-pressed", String(mode === "text"));
  $("voiceMode").setAttribute("aria-pressed", String(mode === "voice"));
  $("textPanel").classList.toggle("hidden", mode !== "text");
  $("voicePanel").classList.toggle("hidden", mode !== "voice");
  $("answer").placeholder = mode === "text"
    ? "Explain your approach and include an example if you have one."
    : "Your editable voice transcript will appear here after you stop recording.";
  error();
}

$("textMode").addEventListener("click", () => setAnswerMode("text"));
$("voiceMode").addEventListener("click", () => setAnswerMode("voice"));
$("answer").addEventListener("input", updateAnswerCount);

function setQuestion(data) {
  currentQuestion = data.question;
  $("questionText").textContent = data.question;
  $("focusText").textContent = `Focus: ${data.focus || "Interview practice"}`;
  $("counter").textContent = `Question ${data.question_number} of ${data.max_questions || 5}`;
  $("answer").value = "";
  updateAnswerCount();
  $("feedbackBox").classList.add("hidden");
  $("submit").disabled = false;
  $("record").disabled = !providerAvailable;
  $("answer").focus({ preventScroll: true });
}

function bars(scores, mount) {
  mount.replaceChildren();
  for (const [name, value] of Object.entries(scores || {})) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) continue;
    const score = Math.max(0, Math.min(100, numeric));
    const row = document.createElement("div");
    row.className = "interview-barrow";
    const label = document.createElement("span");
    label.textContent = name[0].toUpperCase() + name.slice(1);
    const bar = document.createElement("div");
    bar.className = "interview-bar";
    bar.setAttribute("role", "meter");
    bar.setAttribute("aria-label", `${label.textContent} practice estimate`);
    bar.setAttribute("aria-valuemin", "0");
    bar.setAttribute("aria-valuemax", "100");
    bar.setAttribute("aria-valuenow", String(score));
    const fill = document.createElement("div");
    fill.className = "interview-fill";
    fill.style.width = `${score}%`;
    const number = document.createElement("span");
    number.textContent = `${Math.round(score)}%`;
    bar.append(fill);
    row.append(label, bar, number);
    mount.append(row);
  }
}

function fillList(id, values) {
  const list = $(id);
  list.replaceChildren();
  for (const value of values || []) {
    const item = document.createElement("li");
    item.setAttribute("data-i18n-ignore", "");
    item.textContent = String(value);
    list.append(item);
  }
}

function chooseCareer(option) {
  $("role").value = option.title;
  $("careerId").value = option.id || "";
  $("careerSearch").value = option.title;
  $("careerOptions").classList.add("collapsed");
  $("careerSearch").setAttribute("aria-expanded", "false");
  $("changeCareer").hidden = false;
  $("careerContextWarning").hidden = true;
  const evidence = option.supported_context;
  $("careerScopeNote").textContent = evidence
    ? "General interview practice informed by the catalogue entry. The supplied profile is not a verified occupational requirement."
    : "General practice for this career title. A sourced skills profile or verified occupational requirements are not available in the current catalogue.";
  $("careerScopeNote").hidden = false;
  $("start").disabled = !providerAvailable;
}

function renderCareers(search = $("careerSearch").value.trim()) {
  const normalized = search.toLocaleLowerCase();
  const matching = availableCareers.filter(option =>
    option.title.toLocaleLowerCase().includes(normalized)
  );
  $("careerCount").textContent =
    `${matching.length} matching · ${availableCareers.length} careers total`;
  const mount = $("careerOptions");
  mount.replaceChildren();
  if (!matching.length) {
    const empty = document.createElement("div");
    empty.className = "interview-help";
    empty.setAttribute("role", "option");
    empty.setAttribute("aria-disabled", "true");
    empty.setAttribute("aria-selected", "false");
    empty.textContent = "No careers match this search. Try a broader title.";
    mount.append(empty);
    return;
  }
  for (const option of matching) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "interview-career-option";
    button.setAttribute("role", "option");
    button.setAttribute("aria-selected", String(option.title === $("role").value));
    button.setAttribute("aria-label", `Select ${option.title} for interview practice`);
    button.setAttribute("data-i18n-ignore", "");
    button.textContent = option.title;
    button.addEventListener("click", () => {
      chooseCareer(option);
      $("changeCareer").focus({ preventScroll: true });
    });
    mount.append(button);
  }
}

function clearCareer() {
  $("role").value = "";
  $("careerId").value = "";
  $("careerSearch").value = "";
  $("careerScopeNote").hidden = true;
  $("changeCareer").hidden = true;
  $("careerContextWarning").hidden = true;
  $("careerOptions").classList.remove("collapsed");
  $("careerSearch").setAttribute("aria-expanded", "true");
  renderCareers("");
  $("start").disabled = !providerAvailable;
  $("careerSearch").focus();
}

$("changeCareer").addEventListener("click", clearCareer);
$("careerSearch").addEventListener("input", () => {
  $("role").value = "";
  $("careerId").value = "";
  $("careerScopeNote").hidden = true;
  $("changeCareer").hidden = true;
  $("careerOptions").classList.remove("collapsed");
  $("careerSearch").setAttribute("aria-expanded", "true");
  renderCareers();
});
$("careerSearch").addEventListener("focus", () => {
  if (!$("role").value) {
    $("careerOptions").classList.remove("collapsed");
    $("careerSearch").setAttribute("aria-expanded", "true");
    renderCareers();
  }
});
$("careerSearch").addEventListener("keydown", event => {
  if (event.key === "ArrowDown") {
    const first = $("careerOptions").querySelector(".interview-career-option");
    if (first) {
      event.preventDefault();
      first.focus();
    }
  } else if (event.key === "Escape") {
    $("careerOptions").classList.add("collapsed");
    $("careerSearch").setAttribute("aria-expanded", "false");
  }
});
$("careerOptions").addEventListener("keydown", event => {
  if (event.key === "Escape") {
    event.preventDefault();
    $("careerOptions").classList.add("collapsed");
    $("careerSearch").setAttribute("aria-expanded", "false");
    $("careerSearch").focus();
    return;
  }
  if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
  const options = [...$("careerOptions").querySelectorAll(".interview-career-option")];
  const index = options.indexOf(document.activeElement);
  const nextIndex = event.key === "ArrowDown"
    ? Math.min(options.length - 1, index + 1)
    : Math.max(-1, index - 1);
  event.preventDefault();
  if (nextIndex < 0) $("careerSearch").focus();
  else options[nextIndex]?.focus();
});
$("mode").addEventListener("change", error);
$("language").addEventListener("change", () => {
  feedbackLanguageManuallyChosen = true;
  error();
});
$("questionCount").addEventListener("change", () => {
  const count = Number($("questionCount").value);
  $("setupIntro").textContent =
    `Choose a career and practise with ${count} question${count === 1 ? "" : "s"}. You’ll receive coaching feedback after each answer.`;
  error();
});

async function loadAvailability() {
  const notice = $("availabilityNotice");
  $("start").disabled = true;
  try {
    const status = await api("/api/interview/availability");
    providerAvailable = status.available === true;
  } catch {
    providerAvailable = false;
  }
  notice.hidden = providerAvailable;
  $("start").disabled = !providerAvailable || !$("role").value;
  $("record").disabled = !providerAvailable;
}

$("start").addEventListener("click", async () => {
  error();
  if (!providerAvailable) {
    $("availabilityNotice").hidden = false;
    error("AI interview practice is temporarily unavailable.");
    return;
  }
  const role = $("role").value;
  if (!role) {
    error("Select a supported career from the list first.");
    $("careerSearch").focus();
    return;
  }
  loading($("start"), true);
  try {
    const data = await jsonPost("/api/interview/start", {
      role,
      career_id: $("careerId").value,
      mode: $("mode").value,
      language: $("language").value,
      question_count: Number($("questionCount").value),
    });
    sessionId = data.session_id;
    $("careerLabel").textContent = `${role} · ${$("mode").value}`;
    if (data.practice_scope === "general") {
      $("careerScopeNote").textContent =
        "General practice based on the career title only; sourced occupational skills are not available for this role.";
    }
    setQuestion(data);
    show("interview");
  } catch (requestError) {
    error(requestError.message);
    if (/temporarily unavailable/i.test(requestError.message)) {
      providerAvailable = false;
      $("availabilityNotice").hidden = false;
      $("start").disabled = true;
    }
  } finally {
    loading($("start"), false);
  }
});

$("speak").addEventListener("click", () => {
  if (!("speechSynthesis" in window)) {
    error("Question read-aloud is not available in this browser.");
    return;
  }
  window.speechSynthesis.cancel();
  const message = new SpeechSynthesisUtterance(currentQuestion);
  message.lang = $("language").value === "中文" ? "zh-CN"
    : $("language").value === "Bahasa Melayu" ? "ms-MY" : "en-US";
  message.rate = 0.95;
  window.speechSynthesis.speak(message);
});

$("record").addEventListener("click", async () => {
  error();
  if (!providerAvailable) {
    error("AI interview practice is temporarily unavailable.");
    return;
  }
  if (recording) {
    mediaRecorder.stop();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    error("Microphone recording is not supported in this browser. You can type your answer.");
    return;
  }
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
    const mime = candidates.find(type => MediaRecorder.isTypeSupported(type));
    if (!mime) throw new Error("No supported recording format. Please type your answer.");
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType: mime });
    chunks = [];
    mediaRecorder.ondataavailable = event => {
      if (event.data.size) chunks.push(event.data);
    };
    mediaRecorder.onstop = async () => {
      recording = false;
      $("record").textContent = "Start recording";
      $("recordStatus").textContent = "Transcribing…";
      mediaStream?.getTracks().forEach(track => track.stop());
      const blob = new Blob(chunks, { type: mime });
      if (!blob.size) {
        error("No audio was captured.");
        $("recordStatus").textContent = "";
        return;
      }
      if (blob.size > 10 * 1024 * 1024) {
        error("Audio exceeds the 10 MB limit. Record a shorter answer.");
        $("recordStatus").textContent = "";
        return;
      }
      $("record").disabled = true;
      try {
        const form = new FormData();
        form.append("session_id", sessionId);
        const extension = mime.includes("mp4") ? "mp4" : mime.includes("ogg") ? "ogg" : "webm";
        form.append("audio", blob, `answer.${extension}`);
        const data = await api("/api/interview/transcribe", { method: "POST", body: form });
        $("answer").value = `${$("answer").value.trim()} ${data.transcript}`.trim();
        updateAnswerCount();
        $("answer").focus();
      } catch (requestError) {
        error(requestError.message);
      } finally {
        $("record").disabled = !providerAvailable;
        $("recordStatus").textContent = "";
      }
    };
    mediaRecorder.start();
    recording = true;
    $("record").textContent = "Stop recording";
    $("recordStatus").textContent = "Recording…";
  } catch (requestError) {
    mediaStream?.getTracks().forEach(track => track.stop());
    error(requestError.message || "Microphone access was denied.");
  }
});

$("submit").addEventListener("click", async () => {
  error();
  if (!providerAvailable) {
    error("AI interview practice is temporarily unavailable.");
    return;
  }
  if (recording) {
    error("Stop recording before submitting your answer.");
    return;
  }
  const answer = $("answer").value.trim();
  if (answer.length < 3) {
    error("Enter an answer with at least 3 characters.");
    $("answer").focus();
    return;
  }
  if (answer.length > 3500) {
    error("Keep your answer under 3,500 characters.");
    return;
  }
  $("submit").disabled = true;
  try {
    const data = await jsonPost("/api/interview/feedback", { session_id: sessionId, answer });
    const feedback = data.feedback;
    $("totalScore").textContent = `${feedback.total} / 100 · Practice estimate`;
    $("summary").textContent = feedback.summary;
    bars(feedback.scores, $("dimensions"));
    fillList("strengths", feedback.strengths);
    fillList("improvements", feedback.improvements);
    $("example").textContent = feedback.example_answer;
    $("next").textContent = data.finished ? "View final report" : "Next question";
    $("feedbackBox").classList.remove("hidden");
    $("next").focus();
  } catch (requestError) {
    error(requestError.message);
    $("submit").disabled = false;
  }
});

function presentReport(report) {
  $("reportIntro").textContent = `${report.role} · ${report.questions_completed} questions completed`;
  $("reportIntro").setAttribute("data-i18n-ignore", "");
  $("finalScore").textContent = `${report.overall} / 100 · Average practice estimate`;
  const reflection = practiceReflection(report.readiness);
  $("readinessTitle").textContent = reflection.title;
  $("readinessMessage").textContent = reflection.message;
  $("evidenceInfo").textContent =
    `Practice answers in this summary: ${report.readiness.evidence_count}.`;
  $("proficiency").replaceChildren();
  for (const item of report.proficiency) {
    const group = document.createElement("div");
    group.className = "interview-proficiency-item";
    const heading = document.createElement("div");
    heading.className = "interview-proficiency-heading";
    const label = document.createElement("strong");
    label.textContent = item.label;
    const level = document.createElement("span");
    level.textContent = `${item.level} · ${item.score}/100`;
    heading.append(label, level);
    const bar = document.createElement("div");
    bar.className = "interview-bar";
    bar.setAttribute("role", "meter");
    bar.setAttribute("aria-label", `${item.label} practice estimate`);
    bar.setAttribute("aria-valuemin", "0");
    bar.setAttribute("aria-valuemax", "100");
    bar.setAttribute("aria-valuenow", String(item.score));
    const fill = document.createElement("div");
    fill.className = "interview-fill";
    fill.style.width = `${Math.max(0, Math.min(100, item.score))}%`;
    bar.append(fill);
    group.append(heading, bar);
    $("proficiency").append(group);
  }
  fillList("reportStrengths", report.strengths_summary.map(item =>
    `${item.dimension} (${item.score}/100)${item.example ? `: ${item.example}` : ""}`
  ));
  fillList("reportWeaknesses", report.weaknesses_summary.map(item =>
    `${item.dimension} (${item.score}/100): ${item.action}`
  ));
  fillList("priorities", report.practice_priorities.map(item =>
    `Consider practising ${item} next.`
  ));
  $("reportDisclaimer").textContent = report.disclaimer;
  $("reportDisclaimer").setAttribute("data-i18n-ignore", "");
  $("history").replaceChildren();
  report.history.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "interview-history-item";
    const title = document.createElement("strong");
    title.setAttribute("data-i18n-ignore", "");
    title.textContent = `Question ${index + 1}: ${item.question}`;
    const answer = document.createElement("p");
    answer.setAttribute("data-i18n-ignore", "");
    answer.textContent = `Your answer: ${item.answer}`;
    const score = document.createElement("p");
    score.textContent = `Practice estimate: ${item.feedback.total}/100`;
    const improvement = document.createElement("p");
    improvement.textContent = `Try next: ${item.feedback.improvements.join(" · ")}`;
    card.append(title, answer, score, improvement);
    $("history").append(card);
  });
  saveReportLocally({ ...report, readiness: reflection });
  sessionId = null;
  show("report");
  $("reportTitle").focus({ preventScroll: true });
}

function practiceReflection(readiness = {}) {
  const messages = {
    insufficient_evidence: {
      title: "A brief practice snapshot",
      message: `A brief session may not show a broad pattern. Responses included: ${readiness.evidence_count || 0}.`,
    },
    try_real_interviews: {
      title: "Higher coaching estimates this session",
      message: "Your answers received higher AI coaching estimates in this practice session. This does not measure job readiness or eligibility.",
    },
    practice_and_apply: {
      title: "Mixed practice feedback",
      message: "This practice session gave mixed coaching estimates. Choose a response suggestion to try; the result does not say whether you should apply.",
    },
    focus_practice_first: {
      title: "Ideas for another practice round",
      message: "Some answers received lower coaching estimates this session. Try one suggestion; these estimates do not measure workplace performance.",
    },
  };
  const reflection = messages[readiness.status] || {
    title: "Practice reflection",
    message: "Use these notes to reflect on this practice session, not to judge job readiness.",
  };
  return {
    status: readiness.status || "practice_reflection",
    title: reflection.title,
    message: reflection.message,
    evidence_count: Number(readiness.evidence_count) || 0,
    is_preliminary: Boolean(readiness.is_preliminary),
  };
}

$("next").addEventListener("click", async () => {
  error();
  $("next").disabled = true;
  try {
    const data = await jsonPost("/api/interview/next", { session_id: sessionId });
    if (data.finished) presentReport(data.report);
    else setQuestion(data);
  } catch (requestError) {
    error(requestError.message);
  } finally {
    $("next").disabled = false;
  }
});

$("finishEarly").addEventListener("click", async () => {
  error();
  $("finishEarly").disabled = true;
  try {
    const data = await jsonPost("/api/interview/end", { session_id: sessionId });
    presentReport(data.report);
  } catch (requestError) {
    error(requestError.message);
  } finally {
    $("finishEarly").disabled = false;
  }
});

$("restart").addEventListener("click", () => {
  sessionId = null;
  error();
  show("setup");
});

function readReports() {
  const saved = localStorage.getItem(REPORT_KEY);
  if (!saved) return [];
  const parsed = JSON.parse(saved);
  if (!Array.isArray(parsed)) throw new Error("Saved browser history is not a report list.");
  return parsed.filter(item => item?.report);
}

function saveReportLocally(report) {
  try {
    const records = readReports();
    records.push({
      id: crypto.randomUUID(),
      saved_at: new Date().toISOString(),
      report,
    });
    localStorage.setItem(REPORT_KEY, JSON.stringify(records));
  } catch {
    error("Your report is ready, but existing browser history could not be read or saved. Existing data was left unchanged.");
  }
}

function openSavedHistory() {
  show("historyPage");
  let records = [];
  let historyReadFailed = false;
  try {
    records = readReports().slice().reverse();
  } catch {
    historyReadFailed = true;
  }
  $("historyCount").textContent =
    historyReadFailed
      ? "Saved browser history could not be read."
      : `Completed practice sessions saved in this browser: ${records.length}`;
  const mount = $("savedInterviews");
  mount.replaceChildren();
  if (historyReadFailed) {
    const warning = document.createElement("p");
    warning.className = "interview-context-warning";
    warning.textContent = "Existing history was left unchanged. You can delete browser history if you no longer want to keep it.";
    mount.append(warning);
  } else if (!records.length) {
    const empty = document.createElement("p");
    empty.textContent = "No completed sessions are saved in this browser yet.";
    mount.append(empty);
  }
  for (const entry of records) {
    const card = document.createElement("article");
    card.className = "interview-history-item";
    const heading = document.createElement("h3");
    heading.setAttribute("data-i18n-ignore", "");
    heading.textContent = `${entry.report.role} · ${entry.report.overall}/100`;
    const date = document.createElement("p");
    const parsedDate = new Date(entry.saved_at);
    date.textContent = Number.isNaN(parsedDate.getTime()) ? "" : parsedDate.toLocaleString();
    const readiness = document.createElement("p");
    readiness.textContent = entry.report.readiness?.message || "";
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "View saved questions and answers";
    details.append(summary);
    for (const [index, item] of (entry.report.history || []).entries()) {
      const row = document.createElement("p");
      row.textContent =
        `Q${index + 1}: ${item.question} | Answer: ${item.answer} | Practice estimate: ${item.feedback.total}`;
      details.append(row);
    }
    card.append(heading, date, readiness, details);
    mount.append(card);
  }
}

$("openHistory").addEventListener("click", openSavedHistory);
$("backHome").addEventListener("click", () => show("setup"));
$("deleteHistory").addEventListener("click", () => {
  const confirmation =
    window.FutureSkillI18n?.translateText("Delete all interview reports saved in this browser?")
    || "Delete all interview reports saved in this browser?";
  if (confirm(confirmation)) {
    localStorage.removeItem(REPORT_KEY);
    openSavedHistory();
  }
});

window.addEventListener("beforeunload", event => {
  if (sessionId && !document.getElementById("interview").classList.contains("hidden")) {
    event.preventDefault();
    event.returnValue = "";
  }
});

(async () => {
  window.addEventListener("futureskill:languagechange", event => {
    if (feedbackLanguageManuallyChosen) return;
    const preference = {
      en: "English",
      "zh-CN": "中文",
      ms: "Bahasa Melayu",
    }[event.detail?.language];
    if (preference) $("language").value = preference;
  });
  if (window.FutureSkillI18n?.ready) {
    try {
      await window.FutureSkillI18n.ready;
      const preference = {
        en: "English",
        "zh-CN": "中文",
        ms: "Bahasa Melayu",
      }[window.FutureSkillI18n.getLanguage()];
      if (preference) $("language").value = preference;
    } catch {
      // The browser language preference remains independently usable when a pack fails.
    }
  }
  try {
    const result = await api("/api/careers");
    availableCareers = result.career_options
      .filter(item => typeof item.title === "string")
      .sort((a, b) => a.title.localeCompare(b.title, "en", { sensitivity: "base" }));
    renderCareers("");
    const requestedId = pageQuery.get("career_id");
    const requestedTitle = pageQuery.get("career");
    const requested = requestedId
      ? availableCareers.find(item => item.id === requestedId)
      : availableCareers.find(item =>
        requestedTitle && item.title.toLocaleLowerCase() === requestedTitle.trim().toLocaleLowerCase()
      );
    if (requested) {
      chooseCareer(requested);
    } else if (requestedId || requestedTitle) {
      $("careerContextWarning").textContent =
        "That career isn’t in the current interview catalogue. Select a supported title to continue; your learning pathway will not be changed.";
      $("careerContextWarning").hidden = false;
      $("careerOptions").classList.remove("collapsed");
      $("careerSearch").setAttribute("aria-expanded", "true");
    }
  } catch {
    $("careerCount").textContent = "The FutureSkill career catalogue is temporarily unavailable.";
  }

  await loadAvailability();
  $("questionCount").dispatchEvent(new Event("change"));
  if (pageQuery.get("view") === "history") openSavedHistory();
})();
