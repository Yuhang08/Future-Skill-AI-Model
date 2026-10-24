/* Read the existing SDG explorer state; this presentation layer makes no API calls. */
(() => {
  "use strict";

  const root = document.documentElement;
  const goalGrid = document.getElementById("goalGrid");
  const mappingList = document.getElementById("mappingList");
  const results = document.getElementById("results");
  const loading = document.getElementById("loading");
  const careerName = document.getElementById("mapCareerName");
  const reviewStatus = document.getElementById("reviewStatus");
  if (!goalGrid || !mappingList || !results) return;

  const elements = {};
  ["hudSelectedRole", "hudLinkedCount", "hudTotalCount", "hudUnreviewedCount",
    "hudCoverageDial", "hudMappingCount", "hudCoverageNote", "hudTargetList"]
    .forEach(id => { elements[id] = document.getElementById(id); });

  const requestFrame = window.requestAnimationFrame
    ? callback => window.requestAnimationFrame(callback)
    : callback => window.setTimeout(callback, 16);
  const cancelFrame = window.cancelAnimationFrame
    ? id => window.cancelAnimationFrame(id)
    : id => window.clearTimeout(id);
  let queuedFrame = 0;
  let observer;
  let suspended = false;
  let destroyed = false;
  let lastTargets = "";

  function write(id, value) {
    const element = elements[id];
    const text = String(value);
    if (element && element.textContent !== text) element.textContent = text;
  }

  function targetList(targets, emptyMessage) {
    const list = elements.hudTargetList;
    if (!list) return;
    const signature = JSON.stringify([targets, emptyMessage]);
    if (signature === lastTargets) return;
    lastTargets = signature;
    const fragment = document.createDocumentFragment();
    if (!targets.length) {
      const item = document.createElement("li");
      item.className = "hud-target-empty";
      item.textContent = emptyMessage;
      fragment.appendChild(item);
    } else {
      targets.forEach((target, index) => {
        const item = document.createElement("li");
        item.className = "hud-target-item";
        const number = document.createElement("span");
        number.className = "hud-target-index";
        number.textContent = String(index + 1).padStart(2, "0");
        const name = document.createElement("span");
        name.className = "hud-target-name";
        name.textContent = target;
        item.append(number, name);
        fragment.appendChild(item);
      });
    }
    list.replaceChildren(fragment);
  }

  function update() {
    queuedFrame = 0;
    if (destroyed || suspended) return;
    const busy = Boolean(loading && !loading.hidden);
    const ready = !results.hidden && !busy;
    const goals = ready ? Array.from(goalGrid.querySelectorAll(".goal-node")) : [];
    const total = goals.length;
    const linked = goals.filter(goal => goal.classList.contains("linked")).length;
    const mappings = ready ? Array.from(mappingList.querySelectorAll(".mapping")) : [];
    const independent = (reviewStatus?.textContent || "").trim() === "NO CAREER SELECTED";
    const selected = (careerName?.textContent || "").trim();

    write("hudSelectedRole", busy ? "Loading career evidence…" : selected || "Choose a supported career");
    write("hudLinkedCount", ready && total ? linked : "—");
    write("hudTotalCount", total || "—");
    write("hudUnreviewedCount", ready && total ? total - linked : "—");
    write("hudMappingCount", ready ? mappings.length : "—");
    const coverage = total ? linked / total * 100 : 0;
    elements.hudCoverageDial?.style.setProperty("--hud-coverage", `${coverage.toFixed(2)}%`);

    const targets = [];
    const seen = new Set();
    mappings.forEach(mapping => {
      const target = (mapping.querySelector(".target-tag")?.textContent || "").trim();
      if (target && !seen.has(target)) {
        targets.push(target);
        seen.add(target);
      }
    });

    let note;
    let emptyMessage;
    if (busy) {
      note = "Career evidence is loading; no links are shown yet.";
      emptyMessage = "Waiting for the selected career’s reviewed targets.";
    } else if (!ready || !total) {
      note = "The goal map is not available yet. No career links are inferred.";
      emptyMessage = "No reviewed targets are currently displayed.";
    } else if (independent) {
      note = `Browse all ${total} goals independently. Select a career to see reviewed potential links.`;
      emptyMessage = "Choose a career to inspect reviewed targets.";
    } else if (linked) {
      note = `${linked} of ${total} goals have reviewed potential career links; ${total - linked} are not assessed for this role. This is not an impact score.`;
      emptyMessage = "No target labels are currently displayed.";
    } else {
      note = "No reviewed links for this role. The goals remain available to explore; no target relationship or impact is inferred.";
      emptyMessage = "No reviewed targets for this role.";
    }
    write("hudCoverageNote", note);
    targetList(targets, emptyMessage);
  }

  function schedule() {
    if (destroyed || suspended || document.hidden || queuedFrame) return;
    queuedFrame = requestFrame(update);
  }

  function cancelPending() {
    if (queuedFrame) cancelFrame(queuedFrame);
    queuedFrame = 0;
  }

  function updateVisibility() {
    root.dataset.hudMotion = document.hidden || suspended ? "paused" : "running";
    if (document.hidden || suspended) cancelPending();
    else schedule();
  }

  function observe() {
    if (typeof window.MutationObserver !== "function") return;
    observer?.disconnect();
    observer = new MutationObserver(schedule);
    // Do not observe the HUD itself: writing its labels cannot trigger a loop.
    observer.observe(goalGrid, { childList: true, subtree: true, attributes: true, attributeFilter: ["class"] });
    observer.observe(mappingList, { childList: true, subtree: true, characterData: true });
    observer.observe(results, { attributes: true, attributeFilter: ["hidden"] });
    if (careerName) observer.observe(careerName, { childList: true, subtree: true, characterData: true });
    if (reviewStatus) observer.observe(reviewStatus, { childList: true, subtree: true, characterData: true });
    if (loading) observer.observe(loading, { attributes: true, attributeFilter: ["hidden"] });
  }

  function onPageHide(event) {
    suspended = true;
    cancelPending();
    observer?.disconnect();
    updateVisibility();
    if (!event.persisted) {
      destroyed = true;
      document.removeEventListener("visibilitychange", updateVisibility);
      window.removeEventListener("pagehide", onPageHide);
      window.removeEventListener("pageshow", onPageShow);
    }
  }

  function onPageShow() {
    if (destroyed) return;
    suspended = false;
    observe();
    updateVisibility();
  }

  observe();
  document.addEventListener("visibilitychange", updateVisibility);
  window.addEventListener("pagehide", onPageHide);
  window.addEventListener("pageshow", onPageShow);
  updateVisibility();
})();
