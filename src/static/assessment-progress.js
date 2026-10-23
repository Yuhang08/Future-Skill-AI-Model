/* Browser-local questionnaire drafts. No CV text, scores or server writes. */
(function (root) {
  "use strict";
  const DRAFT_KEY = "futureskill-assessment-draft-v1";
  const MAX_AGE = 30 * 24 * 60 * 60 * 1000;

  function fingerprint(parts) {
    const text = JSON.stringify(parts.map(part => part.questions));
    let hash = 2166136261;
    for (let i = 0; i < text.length; i++) hash = Math.imul(hash ^ text.charCodeAt(i), 16777619);
    return (hash >>> 0).toString(16);
  }

  function validateDraft(raw, parts, now = Date.now()) {
    if (typeof raw !== "string" || raw.length > 16384) return null;
    try {
      const draft = JSON.parse(raw);
      if (!draft || draft.version !== 1 || draft.questionnaire !== fingerprint(parts) ||
          !Number.isFinite(draft.savedAt) || now - draft.savedAt > MAX_AGE ||
          draft.savedAt > now + 60000 || !Number.isInteger(draft.currentPart) ||
          !parts[draft.currentPart] || !Number.isInteger(draft.currentQuestion) ||
          !parts[draft.currentPart].questions[draft.currentQuestion] ||
          !draft.answers || typeof draft.answers !== "object" || Array.isArray(draft.answers)) return null;
      const allowed = new Set(parts.flatMap((part, p) => part.questions.map((_, q) => `${p}_${q}`)));
      const answers = {};
      for (const [key, rating] of Object.entries(draft.answers)) {
        if (!allowed.has(key) || !Number.isInteger(rating) || rating < 1 || rating > 5) return null;
        answers[key] = rating;
      }
      return { ...draft, answers };
    } catch { return null; }
  }

  function create({ parts, getAnswers, setAnswers, getPart, setPart, render, demo = false }) {
    let currentQuestion = 0;
    const invalidQuestions = new Set();
    const byId = id => document.getElementById(id);
    const status = message => { byId("assessmentSaveStatus").textContent = message; };
    const key = (p, q) => `${p}_${q}`;
    const answered = (p, q) => Object.hasOwn(getAnswers(), key(p, q));
    const count = p => parts[p].questions.filter((_, q) => answered(p, q)).length;
    const position = () => {
      if (!parts[getPart()].questions[currentQuestion]) currentQuestion = 0;
      return currentQuestion;
    };

    function save() {
      if (demo) {
        status("Preview only — sample answers are not saved.");
        return;
      }
      try {
        const draft = {
          version: 1, questionnaire: fingerprint(parts), savedAt: Date.now(),
          currentPart: getPart(), currentQuestion: position(), answers: getAnswers(),
        };
        localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
        status("Saved on this device for 30 days. Not synced.");
      } catch {
        status("Device storage is unavailable. Answers are kept only until this page closes.");
      }
    }

    function update() {
      position();
      const activePart = getPart();
      for (const id of invalidQuestions) {
        if (Object.hasOwn(getAnswers(), id)) invalidQuestions.delete(id);
      }
      const nav = byId("assessmentQuestionButtons");
      nav.replaceChildren();
      parts[activePart].questions.forEach((_, q) => {
        const done = answered(activePart, q);
        const invalid = invalidQuestions.has(key(activePart, q));
        const button = document.createElement("button");
        button.type = "button";
        button.className = "question-jump";
        button.dataset.questionState = done ? "answered" : "unanswered";
        button.dataset.questionIndex = String(q);
        button.dataset.invalid = String(invalid);
        button.setAttribute("aria-label", `Question ${q + 1}, ${invalid ? "answer required" : done ? "answered" : "unanswered"}`);
        if (q === currentQuestion) button.setAttribute("aria-current", "true");
        button.append(document.createTextNode(String(q + 1)));
        const mark = document.createElement("span");
        mark.className = "question-nav-mark";
        mark.setAttribute("aria-hidden", "true");
        mark.textContent = invalid ? "!" : done ? "✓" : "·";
        button.append(mark);
        button.addEventListener("click", () => jump(q));
        nav.append(button);
      });
      byId("assessmentPartProgress").textContent =
        `${parts[activePart].title.split(":")[0]}: ${count(activePart)} of ${parts[activePart].questions.length} answered`;
      document.querySelectorAll("[data-assessment-part]").forEach(button => {
        const p = Number(button.dataset.assessmentPart);
        button.querySelector(".part-count").textContent = `${count(p)}/${parts[p].questions.length}`;
        if (p === activePart) button.setAttribute("aria-current", "step");
        else button.removeAttribute("aria-current");
      });
      document.querySelectorAll("#questionContainer .question").forEach((question, q) => {
        const invalid = invalidQuestions.has(key(activePart, q));
        question.dataset.current = String(q === currentQuestion);
        question.dataset.invalid = String(invalid);
        question.querySelector(".question-state").textContent = answered(activePart, q) ? "Answered" : "Unanswered";
        const group = question.querySelector('[role="radiogroup"]');
        let error = question.querySelector(".question-validation-error");
        if (invalid) {
          if (!error) {
            error = document.createElement("p");
            error.id = `${question.id}-error`;
            error.className = "question-validation-error";
            error.textContent = "! This question needs an answer. Choose a rating from 1 to 5.";
            question.append(error);
          }
          group.setAttribute("aria-invalid", "true");
          group.setAttribute("aria-describedby", error.id);
          question.setAttribute("aria-describedby", error.id);
        } else {
          error?.remove();
          group.removeAttribute("aria-invalid");
          group.removeAttribute("aria-describedby");
          question.removeAttribute("aria-describedby");
        }
      });
      byId("clearAssessmentDraft").disabled = demo || Object.keys(getAnswers()).length === 0;
    }

    function jump(q) {
      if (!Number.isInteger(q) || !parts[getPart()].questions[q]) return;
      currentQuestion = q;
      update();
      const question = byId(`assessment-question-${getPart()}-${q}`);
      question?.focus({ preventScroll: true });
      question?.scrollIntoView({ block: "nearest", behavior: "auto" });
      save();
    }

    function goToPart(p) {
      if (!Number.isInteger(p) || !parts[p]) return;
      setPart(p);
      currentQuestion = 0;
      render();
      byId("assessmentModal").scrollTop = 0;
      save();
    }

    function showMissing(p) {
      if (!Number.isInteger(p) || !parts[p]) return;
      const missing = parts[p].questions
        .map((_, q) => q).filter(q => !answered(p, q));
      if (!missing.length) return;
      missing.forEach(q => invalidQuestions.add(key(p, q)));
      if (getPart() !== p) goToPart(p);
      jump(missing[0]);
    }

    function clear({ confirm = true, redraw = true } = {}) {
      if (demo) return false;
      if (confirm && !window.confirm("Clear all assessment answers saved on this device? Existing career results and learning plans will not be deleted.")) return false;
      setAnswers({});
      invalidQuestions.clear();
      setPart(0);
      currentQuestion = 0;
      try {
        localStorage.removeItem(DRAFT_KEY);
        status("Draft cleared. New answers will be saved on this device.");
      } catch {
        status("Device storage is unavailable. An older saved draft could not be removed.");
      }
      if (redraw) render();
      return true;
    }

    document.querySelectorAll("[data-assessment-part]").forEach(button => {
      button.addEventListener("click", () => goToPart(Number(button.dataset.assessmentPart)));
    });
    byId("clearAssessmentDraft").addEventListener("click", () => clear());
    byId("questionContainer").addEventListener("focusin", event => {
      const question = event.target.closest(".question");
      if (!question) return;
      const index = Number(question.dataset.questionIndex);
      if (index !== currentQuestion) {
        currentQuestion = index;
        update();
        save();
      }
    });

    if (demo) status("Preview only — sample answers are not saved.");
    else {
      try {
        const raw = localStorage.getItem(DRAFT_KEY);
        const draft = validateDraft(raw, parts);
        if (draft) {
          setAnswers(draft.answers);
          setPart(draft.currentPart);
          currentQuestion = draft.currentQuestion;
          status("Draft restored. Stored on this device for 30 days; not synced.");
        } else if (raw) {
          status("The saved draft is expired or incompatible. Start fresh; new answers will save on this device.");
        } else status("Answers save on this device for 30 days. On a shared device, clear your draft when finished.");
      } catch {
        status("Device storage is unavailable. Answers are kept only until this page closes.");
      }
    }
    return Object.freeze({ update, save, jump, goToPart, showMissing, clear });
  }

  root.FutureSkillAssessmentProgress = Object.freeze({ create, validateDraft, fingerprint, DRAFT_KEY });
})(globalThis);
