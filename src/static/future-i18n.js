/* Local, bounded phrase-catalog internationalization. User-entered values and identifiers are never rewritten. */
(function (root) {
  "use strict";
  const KEY = "futureskill-language-preference";
  const CODES = ["en", "zh-CN", "ms"];
  const originalText = new WeakMap();
  const renderedText = new WeakMap();
  const originalAttributes = new WeakMap();
  const renderedAttributes = new WeakMap();
  const loaded = new Map();
  const loadedResolved = new Set();
  let language = "en";
  let catalog = {};
  let persistence = "available";
  let observer;
  let requestNumber = 0;
  let loading = false;
  let initialError = "";

  function savedLanguage() {
    try {
      const saved = localStorage.getItem(KEY);
      return CODES.includes(saved) ? saved : "en";
    } catch (_) {
      persistence = "blocked";
      initialError = "Browser storage is blocked. Your language choice will apply for this visit only.";
      return "en";
    }
  }
  async function loadPack(code) {
    if (loaded.has(code)) return loaded.get(code);
    const pending = fetch(`/static/locales/${code}.json`, { credentials: "same-origin" })
      .then(response => {
        if (!response.ok) throw new Error("Language pack unavailable");
        return response.json();
      })
      .then(pack => {
        if (!pack || typeof pack !== "object" || Array.isArray(pack)) throw new Error("Invalid language pack");
        loaded.set(code, pack);
        loadedResolved.add(code);
        return pack;
      });
    loaded.set(code, pending);
    try { return await pending; }
    catch (error) { loaded.delete(code); loadedResolved.delete(code); throw error; }
  }
  function translateText(englishText) {
    const source = String(englishText);
    if (language === "en") return source;
    if (Object.prototype.hasOwnProperty.call(catalog, source)) return catalog[source];
    // The only supported interpolation is a whole-phrase template with named slots.
    for (const [pattern, translation] of Object.entries(catalog)) {
      if (!pattern.includes("{") || !translation.includes("{")) continue;
      const names = [];
      const parts = pattern.split(/(\{[a-z][a-zA-Z0-9]*\})/g);
      const escaped = parts.map(part => {
        const slot = /^\{([a-z][a-zA-Z0-9]*)\}$/.exec(part);
        if (slot) { names.push(slot[1]); return "([\\s\\S]*?)"; }
        return part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      }).join("");
      const match = new RegExp(`^${escaped}$`).exec(source);
      if (!match) continue;
      let output = translation;
      names.forEach((name, index) => {
        const value = match[index + 1];
        let replacement = value;
        if (["area", "areas", "subjects", "subject", "skills", "lowSkills", "ties", "fields", "first", "second", "question1", "question2"].includes(name)) {
          replacement = value.split(", ").map(item => {
            const scored = /^(.*?)(\s+\(\d+\))$/.exec(item);
            const label = scored ? scored[1] : item;
            const translatedLabel = Object.prototype.hasOwnProperty.call(catalog, label) ? catalog[label] : label;
            return translatedLabel + (scored ? scored[2] : "");
          }).join(", ");
        }
        output = output.replace(`{${name}}`, replacement);
      });
      if (output !== source) return output;
    }
    return source;
  }
  function excludedText(element) {
    if (!element || element.nodeType !== 1) return false;
    if (element.closest("input,textarea,script,style,code,pre,[contenteditable='true'],[data-i18n-ignore],.report-source-link,.sources a")) return true;
    if (element.closest("#careerName,#mapCareerName,#targetCareer,#career,#goalInfoTitle,#goalInfoCopy,#careerBridgeNote,#dashboardIntro")) return true;
    if (element.closest("[data-source-id],.career-option-title,.goal-name,.skill-name")) return true;
    return false;
  }
  function excludedElement(element) {
    return !element || element.nodeType !== 1 ||
      Boolean(element.closest("[data-i18n-ignore],.report-source-link,.sources a,[data-source-id],.career-option-title,.goal-name,.skill-name"));
  }
  function writeText(node) {
    const parent = node.parentElement;
    if (excludedText(parent)) return;
    let original = originalText.get(node);
    const prior = renderedText.get(node);
    if (original === undefined || node.nodeValue !== prior) {
      original = node.nodeValue;
      originalText.set(node, original);
    }
    const trimmed = original.trim();
    if (!trimmed) return;
    const leading = original.match(/^\s*/)[0];
    const trailing = original.match(/\s*$/)[0];
    let phrase = trimmed.replace(/\s+/g, " ");
    let translated = translateText(phrase);
    if (translated === phrase) {
      const prefixed = /^(\d+\.\s*)([\s\S]*)$/.exec(phrase);
      if (prefixed) {
        const body = translateText(prefixed[2]);
        if (body !== prefixed[2]) translated = prefixed[1] + body;
      }
    }
    const value = translated === phrase ? original : leading + translated + trailing;
    if (node.nodeValue !== value) node.nodeValue = value;
    renderedText.set(node, value);
  }
  const ATTRIBUTE_NAMES = ["aria-label", "aria-description", "title", "placeholder", "alt"];
  function writeAttributes(element) {
    if (excludedElement(element)) return;
    for (const name of ATTRIBUTE_NAMES) {
      if (!element.hasAttribute(name)) continue;
      let stored = originalAttributes.get(element);
      if (!stored) { stored = {}; originalAttributes.set(element, stored); }
      let drawn = renderedAttributes.get(element);
      if (!drawn) { drawn = {}; renderedAttributes.set(element, drawn); }
      const current = element.getAttribute(name);
      if (!(name in stored) || current !== drawn[name]) stored[name] = current;
      const translated = translateText(stored[name]);
      if (current !== translated) element.setAttribute(name, translated);
      drawn[name] = translated;
    }
  }
  function translateTree(node) {
    if (node.nodeType === 3) { writeText(node); return; }
    if (node.nodeType !== 1 || excludedText(node)) {
      // Form controls keep their values, while their accessible labels and hints are translatable.
      if (node.nodeType === 1 && /^(INPUT|TEXTAREA|SELECT)$/.test(node.tagName)) writeAttributes(node);
      return;
    }
    writeAttributes(node);
    node.childNodes.forEach(translateTree);
  }
  function applyLanguage() {
    document.documentElement.lang = language;
    translateTree(document.body);
    const select = document.getElementById("fsLanguageSelect");
    if (select) { select.value = language; select.disabled = loading; }
    const statusText = loading ? "Loading language pack…" : initialError;
    const status = document.getElementById("fsLanguageStatus");
    if (status) status.textContent = statusText;
    window.dispatchEvent(new CustomEvent("futureskill:languagechange", { detail: { language } }));
  }
  async function setLanguage(code) {
    if (!CODES.includes(code)) code = "en";
    const sequence = ++requestNumber;
    loading = !loadedResolved.has(code);
    initialError = "";
    syncSelectors();
    let nextCatalog = {};
    try {
      nextCatalog = await loadPack(code);
    } catch (error) {
      if (sequence === requestNumber) { loading = false; syncSelectors(); }
      throw error;
    }
    if (sequence !== requestNumber) return getState();
    // Commit only after the pack loaded; failure leaves both language and rendered content intact.
    language = code;
    catalog = nextCatalog;
    try {
      localStorage.setItem(KEY, code);
      persistence = "available";
    } catch (_) { persistence = "blocked"; }
    loading = false;
    applyLanguage();
    return getState();
  }
  function syncSelectors() {
    const select = document.getElementById("fsLanguageSelect");
    if (select) { select.value = language; select.disabled = loading; }
    if (loading) {
      const status = document.getElementById("fsLanguageStatus");
      if (status) status.textContent = "Loading language pack…";
    }
  }
  function getState() {
    return { language, persistence, loading, loadError: initialError, loaded: CODES.filter(code => loadedResolved.has(code)) };
  }
  function setPersistenceStatus(state) {
    const message = state.persistence === "blocked"
      ? "Language changed for this visit. Browser storage is blocked, so your preference could not be saved."
      : "";
    const status = document.getElementById("fsLanguageStatus");
    if (status) status.textContent = message;
  }
  function wireSettings() {
    const dialog = document.getElementById("fsSettingsDialog");
    const note = dialog?.querySelector(".fs-translation-note");
    if (!dialog || !note) return;
    if (dialog.dataset.i18nWired) return;
    dialog.dataset.i18nWired = "true";
    // Keep selector and status usable even when a pack request fails.
    const select = dialog.querySelector("#fsLanguageSelect");
    select.addEventListener("change", async () => {
      try {
        const state = await setLanguage(select.value);
        setPersistenceStatus(state);
      } catch (_) {
        select.value = language;
        dialog.querySelector("#fsLanguageStatus").textContent = "This language pack could not be loaded. Your previous language is still active.";
      }
    });
  }
  let readyPromise;
  const api = Object.freeze({
    get ready() { return readyPromise; },
    getLanguage: () => language,
    setLanguage,
    translateText,
    getState
  });
  root.FutureSkillI18n = api;
  function start() {
    wireSettings();
    observer = new MutationObserver(records => {
      for (const record of records) {
        if (record.type === "characterData") writeText(record.target);
        else {
          if (record.target.nodeType === 1) writeAttributes(record.target);
          record.addedNodes.forEach(translateTree);
        }
      }
    });
    observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRIBUTE_NAMES });
  }
  readyPromise = (async () => {
    const saved = savedLanguage();
    try { await loadPack("en"); }
    catch (_) { initialError = "English language pack could not be loaded; built-in English text remains available."; }
    if (saved !== "en") {
      try { catalog = await loadPack(saved); language = saved; }
      catch (_) { language = "en"; catalog = {}; initialError = "Saved language pack could not be loaded. English remains active."; }
    }
    if (document.readyState === "loading") await new Promise(resolve => document.addEventListener("DOMContentLoaded", resolve, { once: true }));
    start();
    applyLanguage();
    const select = document.getElementById("fsLanguageSelect");
    if (select) { select.value = language; select.disabled = false; }
    if (initialError) {
      const status = document.getElementById("fsLanguageStatus");
      if (status) status.textContent = initialError;
    }
    return getState();
  })();
  window.addEventListener("storage", event => {
    if (event.key !== KEY && event.key !== null) return;
    const next = CODES.includes(event.newValue) ? event.newValue : "en";
    setLanguage(next).catch(() => {});
  });
})(window);
