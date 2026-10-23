/* Preserve a selected career across the AI-trends and SDG exploration screens. */
(function () {
  "use strict";
  const idPattern = /^\d{2}-\d{4}\.\d{2}$/;
  const params = new URLSearchParams(window.location.search);
  const careerId = params.get("career_id") || "";
  if (!idPattern.test(careerId)) return;

  function safeReturn(value, id) {
    if (typeof value === "string" && /^\/career\/\d{2}-\d{4}\.\d{2}$/.test(value)) return value;
    return `/career/${encodeURIComponent(id)}`;
  }

  async function loadCareer() {
    const response = await fetch(`/api/careers/${encodeURIComponent(careerId)}`, { credentials: "same-origin" });
    if (!response.ok) throw new Error("Career context is not available.");
    return response.json();
  }

  function addBanner(career) {
    const banner = document.createElement("aside");
    banner.className = "career-context-banner";
    banner.setAttribute("aria-label", "Selected career context");
    const copy = document.createElement("div");
    copy.className = "career-context-copy";
    const label = document.createElement("span");
    label.className = "career-context-label";
    label.textContent = "CAREER CONTEXT";
    const title = document.createElement("strong");
    title.className = "career-context-title";
    title.textContent = career.title;
    const note = document.createElement("p");
    note.textContent = "You are exploring this career. It is separate from your saved learning target.";
    copy.append(label, title, note);
    banner.appendChild(copy);

    if (window.location.pathname === "/ai-trend") {
      const trend = document.createElement("p");
      trend.className = "career-context-trend";
      trend.textContent = "Career-specific trend mappings are shown only when the existing prototype includes this exact occupation.";
      banner.appendChild(trend);
    }

    const back = document.createElement("a");
    back.href = safeReturn(params.get("return_to"), career.id);
    back.textContent = "Return to career details";
    banner.appendChild(back);
    const nav = document.querySelector(".fs-site-nav");
    if (nav?.parentNode) nav.insertAdjacentElement("afterend", banner);
    else document.body.prepend(banner);
  }

  document.addEventListener("DOMContentLoaded", async () => {
    try { addBanner(await loadCareer()); }
    catch (_) {
      // The destination page still works; only the contextual banner is omitted.
    }
  }, { once: true });
})();
