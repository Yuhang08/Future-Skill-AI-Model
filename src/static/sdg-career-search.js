/* Canonical career selection. Suggestions never create a selected career. */
(function (root) {
  "use strict";
  function create({ input, listbox, submit, status, onInvalidate, onSelect }) {
    let selected = null, items = [], active = -1, sequence = 0, controller = null;
    const normalize = value => String(value || "").trim().toLowerCase().replace(/\s+/g, " ");
    function close() {
      sequence++;
      controller?.abort();
      listbox.hidden = true;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      active = -1;
    }
    function announce(text) {
      items = []; active = -1;
      listbox.replaceChildren();
      const message = document.createElement("div");
      message.className = "career-search-message";
      message.setAttribute("role", "status");
      message.textContent = text;
      listbox.append(message);
      listbox.hidden = false;
      input.setAttribute("aria-expanded", "true");
      input.removeAttribute("aria-activedescendant");
    }
    function choose(item) {
      close();
      selected = item;
      input.value = item.title;
      input.removeAttribute("aria-invalid");
      submit.disabled = false;
      status.textContent = `${item.title} · ${item.kind === "occupation" ? `O*NET ${item.id}` : "FutureSkill prototype role"} · ${item.mapping_availability === "curated" ? "Curated mapping + role suggestions" : "Rule-based SDG suggestions"}.`;
      onSelect?.(item);
      input.focus();
    }
    function highlight(index) {
      if (!items.length) return;
      active = (index + items.length) % items.length;
      const options = [...listbox.querySelectorAll('[role="option"]')];
      options.forEach((option, i) => option.setAttribute("aria-selected", String(i === active)));
      input.setAttribute("aria-activedescendant", options[active].id);
      options[active].scrollIntoView({ block: "nearest" });
    }
    function render(results) {
      items = results; active = -1;
      listbox.replaceChildren();
      results.forEach((item, index) => {
        const option = document.createElement("div");
        option.id = `career-option-${index}`;
        option.className = "career-option";
        option.dataset.careerId = item.id;
        option.setAttribute("role", "option");
        option.setAttribute("aria-selected", "false");
        const title = document.createElement("span");
        title.className = "career-option-title";
        title.textContent = item.title;
        const label = document.createElement("span");
        label.className = "career-option-status";
        label.textContent = item.mapping_availability === "curated" ? "Curated + suggested" : "SDG suggestions";
        option.append(title, label);
        option.addEventListener("pointerdown", event => event.preventDefault());
        option.addEventListener("click", () => choose(item));
        listbox.append(option);
      });
      listbox.hidden = false;
      input.setAttribute("aria-expanded", "true");
      input.removeAttribute("aria-activedescendant");
    }
    async function search() {
      const request = ++sequence, query = input.value.trim();
      controller?.abort();
      controller = new AbortController();
      const currentController = controller;
      announce("Searching careers…");
      const timeout = setTimeout(() => currentController.abort(), 10000);
      try {
        const response = await fetch(`/api/sdg/careers?q=${encodeURIComponent(query)}`, { signal: currentController.signal });
        const data = await response.json();
        if (request !== sequence || normalize(input.value) !== normalize(query)) return;
        if (!response.ok) throw new Error("Career search is unavailable.");
        const results = data.results;
        if (!Array.isArray(results) || results.length > 12 || results.some(item =>
          !item || typeof item.id !== "string" || typeof item.title !== "string" ||
          !["occupation", "prototype"].includes(item.kind) ||
          !["curated", "suggested"].includes(item.mapping_availability))) {
          throw new Error("Career search returned an invalid response.");
        }
        if (!results.length) announce("No matching careers. Try another search.");
        else render(results);
      } catch (error) {
        if (request !== sequence) return;
        announce(error.name === "AbortError"
          ? "Career search timed out. Edit your search to try again."
          : "Career search failed. Check your connection and edit your search to retry.");
      } finally {
        clearTimeout(timeout);
      }
    }
    function invalidate() {
      selected = null;
      submit.disabled = true;
      input.removeAttribute("aria-invalid");
      status.textContent = "Choose a catalogue result. Partial and spelling matches are suggestions only.";
      onInvalidate();
    }
    input.addEventListener("input", () => { invalidate(); search(); });
    input.addEventListener("focus", () => { if (!selected && listbox.hidden) search(); });
    input.addEventListener("keydown", event => {
      if (event.key === "Escape") {
        if (!listbox.hidden) { event.preventDefault(); event.stopPropagation(); close(); }
      } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        if (!listbox.hidden && items.length) highlight(active < 0
          ? (event.key === "ArrowDown" ? 0 : items.length - 1)
          : active + (event.key === "ArrowDown" ? 1 : -1));
        else search();
      } else if (event.key === "Enter" && !listbox.hidden) {
        event.preventDefault();
        if (active >= 0) choose(items[active]);
        else if (items.length === 1 && items[0].matched_by === "exact") choose(items[0]);
        else status.textContent = "Use the arrow keys to choose a suggestion, then press Enter.";
      }
    });
    input.addEventListener("blur", close);
    return Object.freeze({
      selection: () => selected && normalize(input.value) === normalize(selected.title) ? selected : null,
      search, close,
      requireSelection() {
        input.setAttribute("aria-invalid", "true");
        status.textContent = "Select a supported career from the suggestions before exploring.";
        input.focus();
      },
    });
  }
  root.FutureSkillCareerSearch = Object.freeze({ create });
})(globalThis);
