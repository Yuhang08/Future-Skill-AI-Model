/* Preview-only dependency boundary. No live API request or real save is made. */
(() => {
  const config = window.__FUTURE_PREVIEW__;
  const { fixtures, channel, mode, search, origin } = config;
  window.__previewSearch = search;
  const memory = new Map([["futureskill-theme-preference", mode === "current" ? "light" : mode]]);
  window.__previewStorage = {
    getItem: key => memory.get(key) ?? null,
    setItem: (key, value) => memory.set(key, String(value)),
    removeItem: key => memory.delete(key),
    clear: () => memory.clear(),
  };
  const clone = data => JSON.parse(JSON.stringify(data));
  const response = (data, status = 200) => Promise.resolve(new Response(JSON.stringify(data), {
    status, headers: { "Content-Type": "application/json" },
  }));
  const message = "Design preview only: this action does not save or upload. Use the working website for personal changes.";
  const rounded = number => Math.round((number + Number.EPSILON) * 100) / 100;
  window.fetch = (input, options = {}) => {
    const url = new URL(typeof input === "string" ? input : input.url, origin);
    const method = options.method || "GET";
    let body = {};
    if (typeof options.body === "string") {
      try { body = JSON.parse(options.body); } catch { return response({ error: "Invalid preview input." }, 400); }
    }
    if (url.pathname === "/api/state") {
      const params = new URLSearchParams(search);
      const scenario = params.get("demo_scenario") || "dashboard";
      return response(clone(fixtures.states[scenario] || fixtures.states.dashboard));
    }
    if (url.pathname === "/api/ai-trends") return response(clone(fixtures.trends));
    if (url.pathname === "/api/uncertainty/scenarios") return response(clone(fixtures.scenarios));
    if (url.pathname === "/api/uncertainty/simulate" && method === "POST") {
      const keys = ["ai_growth", "automation", "adaptation", "economy", "alignment", "other_factors"];
      if (keys.some(key => !Number.isFinite(body[key]) || body[key] < 0 || body[key] > 100) ||
          !Number.isFinite(body.base_rate) || body.base_rate < 0 || body.base_rate > 100) {
        return response({ detail: "Inputs must be between 0 and 100." }, 422);
      }
      // Same illustrative arithmetic as reskilling/extra_features.py.
      const delta = .018 * (body.economy - 50) + .005 * (body.other_factors - 50)
        - .012 * Math.max(0, body.automation - body.adaptation) - .003 * body.alignment
        + .003 * body.ai_growth * body.adaptation / 100;
      let rate = body.base_rate;
      const employment_rate = {};
      fixtures.scenarios.years.forEach((year, index) => {
        if (index) rate = Math.max(0, Math.min(100, rate + delta));
        employment_rate[year] = rounded(rate);
      });
      const occupational_growth = Object.fromEntries(Object.entries(fixtures.occupational_weights)
        .map(([job, [economy, ai, automation, alignment]]) => [job, rounded(
          .06 * economy * (body.economy - 50) + .035 * ai * body.ai_growth
          - .045 * automation * Math.max(0, body.automation - .4 * body.adaptation)
          - .02 * alignment * body.alignment + .008 * (body.other_factors - 50)
        )]));
      return response({ employment_rate, occupational_growth, warning: fixtures.scenarios.warning });
    }
    if (url.pathname === "/api/sdg/mindmap" && method === "POST") {
      const requested = String(body.title || "").trim();
      const role = Object.keys(fixtures.sdg).find(name => name.toLowerCase() === requested.toLowerCase());
      const data = clone(fixtures.sdg[role || "Unreviewed role"]);
      if (!role) data.career = requested;
      return response(data);
    }
    if (url.pathname === "/api/recommend") {
      // The inventory's explicit S05 sample is a canned design fixture, not a personal score.
      if (new URLSearchParams(search).get("screen") === "S05") {
        return response(clone(fixtures.recommendations));
      }
      return response({ detail: "Design preview does not score your answers. Open Screen inventory → S05 to inspect the labeled sample results." }, 409);
    }
    return response({ error: message, detail: message }, 409);
  };
  window.addEventListener("message", event => {
    if (event.source !== parent || event.origin !== origin || event.data?.channel !== channel || event.data.kind !== "future-preview-mode") return;
    const theme = event.data.mode;
    if (!["dark", "light"].includes(theme)) return;
    document.documentElement.dataset.futureTheme = theme;
    document.documentElement.dataset.theme = theme;
    memory.set("futureskill-theme-preference", theme);
    document.querySelectorAll('#themePreference input[name="themePreference"]').forEach(input => {
      input.checked = input.value === theme;
    });
    if (typeof window.applyThemePreference === "function") window.applyThemePreference(theme, false);
  });
  document.addEventListener("click", event => {
    const anchor = event.target.closest("a[href]");
    if (!anchor) return;
    const href = anchor.getAttribute("href");
    if (!href || href.startsWith("#") || /^(https?:|mailto:|tel:)/i.test(href)) return;
    event.preventDefault();
    parent.postMessage({ channel, kind: "future-preview-navigate", href }, origin);
  }, true);
  window.addEventListener("DOMContentLoaded", () => {
    if (mode === "current") return;
    // Settings inside the extracted reskilling page use the same mode as the preview.
    new MutationObserver(() => {
      const theme = document.documentElement.dataset.theme;
      if (theme === "light" || theme === "dark") {
        document.documentElement.dataset.futureTheme = theme;
        parent.postMessage({ channel, kind: "future-preview-theme", mode: theme }, origin);
      }
    }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  });
})();
