/* Optional diagram presentation; occupational scores and evidence stay in the page controller. */
(() => {
  "use strict";
  const root = document.documentElement;
  const grid = document.getElementById("goalGrid");
  const stage = document.getElementById("hudGoalStage");
  const explorer = document.getElementById("allGoals");
  const results = document.getElementById("results");
  const role = document.getElementById("roleTitle");
  const center = document.getElementById("hudCareerCenter");
  const note = document.getElementById("hudDiagramNote");
  if (!grid || !stage || !explorer || !center || !results) return;
  const buttons = Array.from(document.querySelectorAll("[data-hud-layout]"));
  let diagramRequested = false;
  let lines = null;
  let frame = 0;
  let destroyed = false;
  let resizeObserver;
  let lastWidth = -1;

  function setText(selector, text) {
    const element = center.querySelector(selector);
    if (element && element.textContent !== text) element.textContent = text;
  }

  function clearDiagram() {
    grid.classList.remove("is-perimeter");
    stage.classList.remove("is-diagram");
    note.classList.remove("is-visible");
    lines?.remove();
    lines = null;
    grid.querySelectorAll(".goal-list-item").forEach(item => {
      item.style.removeProperty("--goal-x");
      item.style.removeProperty("--goal-y");
    });
  }

  function update() {
    frame = 0;
    if (destroyed) return;
    const width = grid.clientWidth;
    const diagram = diagramRequested && innerWidth > 900 && width >= 820 && explorer.open && !results.hidden;
    buttons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.hudLayout === (diagramRequested ? "diagram" : "list"))));
    if (!diagram) { clearDiagram(); return; }
    const items = Array.from(grid.querySelectorAll(".goal-list-item"));
    const nodes = items.map(item => item.querySelector(".goal-node"));
    if (nodes.length !== 17 || nodes.some(node => !node)) { clearDiagram(); return; }

    const pad = 16, gap = 14;
    const cardWidth = Math.min(160, (width - 2 * pad - 6 * gap) / 7);
    const cardHeight = 112;
    const height = 2 * pad + 6 * cardHeight + 5 * gap;
    const leftX = width / 2 - 3 * (cardWidth + gap);
    const rightX = width / 2 + 3 * (cardWidth + gap);
    stage.classList.add("is-diagram");
    grid.classList.add("is-perimeter");
    note.classList.add("is-visible");
    [["--perimeter-height",height],["--goal-card-width",cardWidth],["--goal-card-height",cardHeight]].forEach(([property,value]) => stage.style.setProperty(property, `${value}px`));
    items.forEach((item,index) => {
      let x, y;
      if (index < 5) { x = width/2 + (index - 2) * (cardWidth + gap); y = pad + cardHeight/2; }
      else if (index < 9) { x = rightX; y = pad + cardHeight/2 + (index - 4) * (cardHeight + gap); }
      else if (index < 13) { x = width/2 + (1.5 - (index - 9)) * (cardWidth + gap); y = height - pad - cardHeight/2; }
      else { x = leftX; y = pad + cardHeight/2 + (4 - (index - 13)) * (cardHeight + gap); }
      item.style.setProperty("--goal-x", `${x}px`);
      item.style.setProperty("--goal-y", `${y}px`);
    });

    const linked = nodes.filter(node => node.classList.contains("linked"));
    const exploratory = nodes.filter(node => node.classList.contains("top-ranked") && !node.classList.contains("linked"));
    const selected = (role?.textContent || "").trim();
    setText("[data-hud-career]", selected === "Explore all 17 goals" ? "Explore the goals" : selected || "Explore the goals");
    setText("[data-hud-count]", linked.length
      ? `${linked.length} Target hypotheses${exploratory.length ? ` · ${exploratory.length} exploratory Top 3` : ""}`
      : exploratory.length ? `${exploratory.length} exploratory Goal connections · not verified`
      : "No task-based connections available");
    if (!lines) {
      lines = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      lines.id = "mapLines";
      lines.classList.add("hud-connector-lines");
      lines.setAttribute("aria-hidden", "true");
      lines.setAttribute("focusable", "false");
      stage.prepend(lines);
    }
    lines.setAttribute("viewBox", `0 0 ${width} ${height}`);
    lines.replaceChildren();
    const bounds = stage.getBoundingClientRect();
    const hub = center.getBoundingClientRect();
    const sx = hub.left + hub.width/2 - bounds.left;
    const sy = hub.top + hub.height/2 - bounds.top;
    [...linked, ...exploratory].forEach(button => {
      const target = button.getBoundingClientRect();
      const tx = target.left + target.width/2 - bounds.left;
      const ty = target.top + target.height/2 - bounds.top;
      const distance = Math.hypot(tx - sx, ty - sy);
      if (!distance) return;
      const ux = (tx - sx)/distance, uy = (ty - sy)/distance;
      const start = Math.min(hub.width,hub.height)/2 + 6;
      const targetEdge = Math.min(Math.abs(ux) > 1e-9 ? target.width/2/Math.abs(ux) : Infinity, Math.abs(uy) > 1e-9 ? target.height/2/Math.abs(uy) : Infinity) + 6;
      if (distance <= start + targetEdge) return;
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.dataset.sdgId = button.dataset.sdgId;
      if (!button.classList.contains("linked")) line.classList.add("exploratory");
      [["x1",sx+ux*start],["y1",sy+uy*start],["x2",tx-ux*targetEdge],["y2",ty-uy*targetEdge]].forEach(([name,value]) => line.setAttribute(name,String(value)));
      lines.appendChild(line);
    });
  }

  function schedule() {
    if (!destroyed && !document.hidden && !frame) frame = requestAnimationFrame(update);
  }
  buttons.forEach(button => button.addEventListener("click", () => {
    diagramRequested = button.dataset.hudLayout === "diagram";
    schedule();
  }));
  const observer = new MutationObserver(schedule);
  observer.observe(grid, { childList: true });
  observer.observe(results, { attributes: true, attributeFilter: ["hidden"] });
  if (role) observer.observe(role, { childList: true, characterData: true, subtree: true });
  explorer.addEventListener("toggle", schedule);
  if (typeof ResizeObserver === "function") {
    resizeObserver = new ResizeObserver(entries => {
      const width = entries[0]?.contentRect.width;
      if (width !== lastWidth) { lastWidth = width; schedule(); }
    });
    resizeObserver.observe(grid);
  }
  window.addEventListener("resize", schedule, { passive: true });
  function visibility() {
    root.dataset.hudMotion = document.hidden ? "paused" : "running";
    if (document.hidden) { cancelAnimationFrame(frame); frame = 0; }
    else schedule();
  }
  function cleanup(event) {
    if (event.persisted) return;
    destroyed = true;
    cancelAnimationFrame(frame);
    observer.disconnect();
    resizeObserver?.disconnect();
    window.removeEventListener("resize", schedule);
    window.removeEventListener("pagehide", cleanup);
    document.removeEventListener("visibilitychange", visibility);
    explorer.removeEventListener("toggle", schedule);
  }
  window.addEventListener("pagehide", cleanup);
  document.addEventListener("visibilitychange", visibility);
  visibility();
})();
