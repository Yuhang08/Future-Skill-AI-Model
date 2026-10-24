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
    document.querySelectorAll(".fs-site-brand img").forEach(image => {
      image.src = resolved === "dark" ? "/static/brand-forward-dark.svg" : "/static/brand-forward.svg";
    });
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
    if (themeColor) themeColor.content = resolved === "dark" ? "#030b16" : "#edf5fc";
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

  function buildCyberGrid() {
    if (!root.hasAttribute("data-futureskill-page") || document.querySelector(".fs-cyber-field")) return;
    const namespace = "http://www.w3.org/2000/svg";
    const field = document.createElementNS(namespace, "svg");
    field.classList.add("fs-cyber-field");
    field.setAttribute("aria-hidden", "true");
    field.setAttribute("focusable", "false");
    const traces = Array.from({ length: 6 }, () => {
      const path = document.createElementNS(namespace, "path");
      path.classList.add("fs-cyber-trace");
      field.appendChild(path);
      return path;
    });
    document.body.prepend(field);

    const snap = value => Math.round(value / 24) * 24;
    function measureGrid() {
      const width = window.innerWidth, height = window.innerHeight;
      // All turns land at grid intersections; long routes leave quiet gaps.
      const routes = [
        [[-96, snap(height * .24)], [snap(width * .26), snap(height * .24)], [snap(width * .26), snap(height * .48)], [snap(width * .62), snap(height * .48)]],
        [[snap(width * .79), -96], [snap(width * .79), snap(height * .36)], [snap(width * .55), snap(height * .36)], [snap(width * .55), snap(height * .74)]],
        [[width + 96, snap(height * .82)], [snap(width * .72), snap(height * .82)], [snap(width * .72), snap(height * .60)], [snap(width * .30), snap(height * .60)]],
        [[snap(width * .12), height + 96], [snap(width * .12), snap(height * .68)], [snap(width * .35), snap(height * .68)], [snap(width * .35), snap(height * .38)]],
        [[snap(width * .44), -96], [snap(width * .44), snap(height * .14)], [snap(width * .92), snap(height * .14)], [snap(width * .92), snap(height * .52)]],
        [[width + 96, snap(height * .94)], [snap(width * .46), snap(height * .94)], [snap(width * .46), snap(height * .76)], [snap(width * .18), snap(height * .76)]],
      ];
      routes.forEach((points, index) => {
        const path = traces[index];
        const length = points.slice(1).reduce((sum, point, i) => sum + Math.abs(point[0] - points[i][0]) + Math.abs(point[1] - points[i][1]), 0);
        path.setAttribute("d", points.map(([x, y], i) => `${i ? "L" : "M"}${x} ${y}`).join(" "));
        path.style.setProperty("--cyber-trace-length", `${length + 100}px`);
        path.style.setProperty("--cyber-trace-duration", `${Math.max(12, (length + 180) / 70)}s`);
        path.style.setProperty("--cyber-trace-delay", `${-3.1 * index - 2}s`);
      });
    }
    const pause = () => field.classList.toggle("is-paused", document.hidden);
    let resizeFrame = 0;
    const onResize = () => {
      if (!resizeFrame) resizeFrame = requestAnimationFrame(() => { resizeFrame = 0; measureGrid(); });
    };
    const cleanup = event => {
      if (event.persisted) return;
      cancelAnimationFrame(resizeFrame);
      window.removeEventListener("resize", onResize);
      document.removeEventListener("visibilitychange", pause);
      window.removeEventListener("pagehide", cleanup);
    };
    window.addEventListener("resize", onResize, { passive: true });
    document.addEventListener("visibilitychange", pause);
    window.addEventListener("pagehide", cleanup);
    measureGrid();
    pause();
  }

  function buildNavigation() {
    buildCyberGrid();
    if (document.querySelector(".fs-site-nav")) return;
    const refinement = document.createElement("link");
    refinement.rel = "stylesheet";
    refinement.href = "/static/ui-refinement.css?v=1";
    let cyber = document.querySelector('link[href^="/static/future-cyber.css"]');
    if (!cyber) {
      cyber = document.createElement("link");
      cyber.rel = "stylesheet";
      cyber.href = "/static/future-cyber.css?v=3";
      document.head.appendChild(cyber);
    }
    document.head.insertBefore(refinement, cyber);
    document.querySelectorAll('link[rel="icon"]').forEach(icon => {
      icon.href = "/static/brand-forward.svg";
      icon.type = "image/svg+xml";
    });
    document.querySelectorAll('img[src*="futureskill-atom.svg"]').forEach(image => {
      image.src = "/static/brand-forward.svg";
    });
    const nav = document.createElement("nav");
    nav.className = "fs-site-nav";
    nav.setAttribute("aria-label", "Main navigation");
    const brand = document.createElement("a");
    brand.className = "fs-site-brand";
    brand.href = "/";
    brand.setAttribute("aria-label", "FutureSkill AI home");
    brand.innerHTML = '<img src="/static/brand-forward.svg" alt="" aria-hidden="true"><span>FutureSkill AI</span>';
    nav.appendChild(brand);
    const links = document.createElement("div");
    links.className = "fs-site-links";
    const items = [
      ["/", "Career assessment"], ["/reskilling", "Reskilling"], ["/ai-trend", "Future Job Trend"],
      ["/uncertainty", "Employability Predictor"], ["/sdg-impact", "SDG connections"],
      ["/interview-practice/", "Interview practice"],
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
    const settingsButton = document.createElement("button");
    settingsButton.type = "button";
    settingsButton.id = "fsSettingsButton";
    settingsButton.className = "fs-settings-button";
    settingsButton.setAttribute("aria-haspopup", "dialog");
    settingsButton.setAttribute("aria-controls", "fsSettingsDialog");
    settingsButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 8.25a3.75 3.75 0 1 0 0 7.5 3.75 3.75 0 0 0 0-7.5Z"/><path d="m19.2 13.6 1.1.85-1.5 2.6-1.3-.5a7.7 7.7 0 0 1-1.6.95l-.2 1.4h-3l-.2-1.4a7.7 7.7 0 0 1-1.6-.95l-1.3.5-1.5-2.6 1.1-.85a7.6 7.6 0 0 1 0-1.85l-1.1-.85 1.5-2.6 1.3.5a7.7 7.7 0 0 1 1.6-.95l.2-1.4h3l.2 1.4a7.7 7.7 0 0 1 1.6.95l1.3-.5 1.5 2.6-1.1.85a7.6 7.6 0 0 1 0 1.85Z"/></svg><span>Settings</span>';
    nav.appendChild(settingsButton);
    document.body.prepend(nav);
    if (!document.getElementById("fsSettingsDialog")) {
      const dialog = document.createElement("dialog");
      dialog.id = "fsSettingsDialog";
      dialog.className = "fs-settings-dialog";
      dialog.setAttribute("aria-labelledby", "fsSettingsTitle");
      dialog.innerHTML = `
        <div class="fs-settings-heading">
          <div><p class="fs-settings-kicker">FUTURESKILL</p><h2 id="fsSettingsTitle">Settings</h2></div>
          <button type="button" class="fs-settings-close" aria-label="Close settings">×</button>
        </div>
        <div class="fs-settings-body">
          <section class="fs-settings-section">
            <h3>Profile</h3>
            <p>Review the details shaping your learning plan.</p>
          <a id="editProfileFromSettings" href="/reskilling?editProfile=1">Open learning profile <span aria-hidden="true">→</span></a>
          </section>
          <section class="fs-settings-section">
            <h3>Appearance</h3>
            <p>Choose how FutureSkill looks on this browser.</p>
            <fieldset id="themePreference" class="fs-theme-options">
              <legend class="visually-hidden">Appearance preference</legend>
              <label><input type="radio" name="themePreference" value="light"><span>Light</span></label>
              <label><input type="radio" name="themePreference" value="dark"><span>Dark</span></label>
              <label><input type="radio" name="themePreference" value="system"><span>System</span></label>
            </fieldset>
          </section>
          <section class="fs-settings-section">
          <label class="fs-settings-label" for="fsLanguageSelect">Language</label>
          <select id="fsLanguageSelect" aria-describedby="fsLanguageStatus" disabled>
            <option value="en">English</option><option value="zh-CN">简体中文</option><option value="ms">Bahasa Melayu</option>
          </select>
          <p id="fsLanguageStatus" class="fs-language-status" role="status" aria-live="polite"></p>
          <p class="fs-translation-note">Occupational titles, imported career information, and external source titles may remain in English.</p>
          </section>
          <section class="fs-settings-section">
            <h3>More for your workspace</h3>
            <p>These options are not available yet.</p>
            <ul class="fs-availability">
              <li><span><strong>CV import</strong><small>Unavailable; enter skills manually during setup</small></span><span>Not available</span></li>
              <li><span><strong>Notifications</strong><small>Choose learning reminders</small></span><span>Not available</span></li>
              <li><span><strong>Cross-device sync</strong><small>Continue your plan on another device</small></span><span>Not available</span></li>
            </ul>
          </section>
          <section class="fs-settings-section">
            <h3>Privacy and data</h3>
            <p>This prototype does not offer account-level cross-device sync. Your appearance choice is saved in this browser; learning data uses the app’s existing session.</p>
          </section>
        </div>`;
      document.body.appendChild(dialog);
      const close = dialog.querySelector(".fs-settings-close");
      const closeDialog = () => {
        if (dialog.close && dialog.open) dialog.close();
        else { dialog.removeAttribute("open"); settingsButton.focus(); }
      };
      settingsButton.addEventListener("click", () => {
        if (dialog.showModal) dialog.showModal();
        else dialog.setAttribute("open", "");
        dialog.querySelector(".fs-settings-close").focus();
      });
      dialog.querySelector("#themePreference").addEventListener("change", event => {
        if (event.target.matches('input[name="themePreference"]')) setPreference(event.target.value);
      });
      close.addEventListener("click", closeDialog);
      dialog.addEventListener("click", event => {
        if (event.target === dialog) closeDialog();
      });
      dialog.addEventListener("keydown", event => {
        if (event.key === "Escape" && !dialog.close) closeDialog();
        if (event.key === "Tab" && !dialog.showModal) {
          const focusable = [...dialog.querySelectorAll("button,a,select,input")].filter(item => !item.disabled);
          if (event.shiftKey && document.activeElement === focusable[0]) { event.preventDefault(); focusable.at(-1).focus(); }
          else if (!event.shiftKey && document.activeElement === focusable.at(-1)) { event.preventDefault(); focusable[0].focus(); }
        }
      });
      dialog.addEventListener("close", () => settingsButton.focus());
    }
    if (!document.querySelector('script[src^="/static/future-i18n.js"]')) {
      const i18nScript = document.createElement("script");
      i18nScript.src = "/static/future-i18n.js?v=6";
      i18nScript.async = true;
      document.head.appendChild(i18nScript);
    }
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
