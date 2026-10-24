/* Shared appearance only. Existing page controllers and real APIs stay in place. */
(() => {
  "use strict";
  const key = "futureskill-theme-preference";
  const root = document.documentElement;
  const media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  const normalize = choice => ["light", "dark", "system"].includes(choice) ? choice : "system";
  let preference = "system";
  try { preference = normalize(localStorage.getItem(key)); } catch { /* Private storage can be unavailable. */ }
  let resolved;

  function updateControls() {
    document.querySelectorAll('#themePreference input[name="themePreference"]').forEach(input => {
      input.checked = input.value === preference;
    });
    document.querySelectorAll("[data-theme-toggle]").forEach(button => {
      const next = resolved === "dark" ? "light" : "dark";
      button.setAttribute("aria-label", `Switch to ${next} mode`);
      button.setAttribute("title", `Switch to ${next} mode`);
      button.setAttribute("aria-pressed", String(resolved === "dark"));
      button.querySelector("[data-theme-label]").textContent = next === "light" ? "Light mode" : "Dark mode";
      button.querySelector("[data-sun]").toggleAttribute("hidden", next !== "light");
      button.querySelector("[data-moon]").toggleAttribute("hidden", next !== "dark");
    });
    const themeColor = document.querySelector('meta[name="theme-color"]');
    if (themeColor) themeColor.content = resolved === "dark" ? "#111b2a" : "#edf3f5";
  }

  function setPreference(choice, persist = true) {
    preference = normalize(choice);
    resolved = preference === "system" ? (media?.matches ? "dark" : "light") : preference;
    root.dataset.futureTheme = resolved;
    root.dataset.theme = resolved;
    root.dataset.themePreference = preference;
    if (persist) {
      try { localStorage.setItem(key, preference); } catch { /* Appearance still works for this visit. */ }
    }
    updateControls();
    window.dispatchEvent(new CustomEvent("futureskill:themechange", { detail: { preference, resolved } }));
    return { preference, resolved };
  }
  window.FutureSkillTheme = {
    setPreference,
    getState: () => ({ preference, resolved }),
  };
  // Run in the head before CSS paints, so saved dark mode does not flash light.
  setPreference(preference, false);

  const onSystemChange = () => {
    if (preference === "system") setPreference("system", false);
  };
  if (media?.addEventListener) media.addEventListener("change", onSystemChange);
  else if (media?.addListener) media.addListener(onSystemChange);
  window.addEventListener("storage", event => {
    if (event.key === key || event.key === null) setPreference(normalize(event.newValue), false);
  });

  function buildNavigation() {
    if (document.querySelector(".fs-site-nav")) return;
    const nav = document.createElement("nav");
    nav.className = "fs-site-nav";
    nav.setAttribute("aria-label", "Main navigation");
    const brand = document.createElement("a");
    brand.className = "fs-site-brand";
    brand.href = "/";
    brand.setAttribute("aria-label", "FutureSkill AI home");
    brand.innerHTML = '<img src="/static/futureskill-atom.svg?v=1" alt="" aria-hidden="true"><span>FutureSkill AI</span>';
    nav.appendChild(brand);
    const links = document.createElement("div");
    links.className = "fs-site-links";
    const items = [
      ["/", "Career assessment"], ["/reskilling", "Reskilling"], ["/ai-trend", "AI trends"],
      ["/uncertainty", "Uncertainty Lab"], ["/sdg-impact", "SDG connections"],
      ["/hr-interview/", "Interview practice"],
    ];
    // The existing inventory remains development-only, not a new learner feature.
    if (root.dataset.futureskillPage === "inventory") items.push(["/__dev/screens", "Screen inventory"]);
    items.forEach(([href, label]) => {
      const link = document.createElement("a");
      link.href = href;
      link.textContent = label;
      if (window.location.pathname === href) link.setAttribute("aria-current", "page");
      links.appendChild(link);
    });
    nav.appendChild(links);
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "fs-theme-toggle";
    toggle.dataset.themeToggle = "";
    toggle.innerHTML = '<svg data-sun viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg><svg data-moon viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14a8 8 0 0 1-10-10 8.5 8.5 0 1 0 10 10Z"/></svg><span data-theme-label></span>';
    toggle.addEventListener("click", () => setPreference(resolved === "dark" ? "light" : "dark"));
    nav.appendChild(toggle);
    document.body.prepend(nav);
    updateControls();
    // Keep the existing development warning visible without covering navigation.
    const sizeNavigation = () => root.style.setProperty("--fs-navigation-height", `${Math.ceil(nav.getBoundingClientRect().height)}px`);
    sizeNavigation();
    if (window.ResizeObserver) new ResizeObserver(sizeNavigation).observe(nav);
    else window.addEventListener("resize", sizeNavigation);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", buildNavigation, { once: true });
  else buildNavigation();
})();
