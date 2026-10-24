/* Career catalogue, recommendation context, details and two-role comparison. */
(function () {
  "use strict";

  const content = document.getElementById("careerWorkspaceContent");
  const ID_PATTERN = /^\d{2}-\d{4}\.\d{2}$/;
  const DIMENSIONS = [
    ["R", "Realistic"], ["I", "Investigative"], ["A", "Artistic"],
    ["S", "Social"], ["E", "Enterprising"], ["C", "Conventional"]
  ];
  const params = new URLSearchParams(window.location.search);
  let previewContext = null;

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }

  function addLink(parent, href, text, className) {
    const link = el("a", className, text);
    link.href = href;
    parent.appendChild(link);
    return link;
  }

  function addButton(parent, text, callback, className = "career-button") {
    const button = el("button", className, text);
    button.type = "button";
    button.addEventListener("click", callback);
    parent.appendChild(button);
    return button;
  }

  async function jsonRequest(url, options = {}) {
    const response = await fetch(url, {
      credentials: "same-origin",
      headers: options.body ? { "Content-Type": "application/json" } : {},
      ...options
    });
    let body;
    try { body = await response.json(); }
    catch { throw new Error("The server returned an unexpected response."); }
    if (!response.ok) {
      const detail = typeof body.detail === "string" ? body.detail :
        typeof body.error === "string" ? body.error : "This information is unavailable right now.";
      throw new Error(detail);
    }
    return body;
  }

  function readSessionContext() {
    if (previewContext) return previewContext;
    try {
      const raw = sessionStorage.getItem("futureskill-career-context");
      if (!raw) return null;
      const context = JSON.parse(raw);
      const model = window.FutureSkillReport?.buildModel(context?.data);
      return model?.valid ? context : null;
    } catch (_) {
      return null;
    }
  }

  function recommendations() {
    return readSessionContext()?.data?.recommendations || [];
  }

  function getRecommendation(id) {
    return recommendations().find(item => item.id === id) || null;
  }

  function setActiveNavigation(pathname) {
    let active = "explore";
    if (pathname === "/career-overview") active = "overview";
    else if (pathname === "/my-profile") active = "profile";
    else if (pathname === "/reskilling") active = "pathway";
    document.querySelectorAll("[data-workspace-nav]").forEach(link => {
      if (link.dataset.workspaceNav === active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }

  function heading(title, description, eyebrow = "Career workspace") {
    const wrap = el("header", "career-page-header");
    wrap.appendChild(el("p", "career-eyebrow", eyebrow));
    wrap.appendChild(el("h1", "career-page-heading", title));
    if (description) wrap.appendChild(el("p", "career-page-lede", description));
    content.appendChild(wrap);
  }

  function section(title, note) {
    const panel = el("section", "career-panel");
    panel.appendChild(el("h2", "", title));
    if (note) panel.appendChild(el("p", "career-muted", note));
    content.appendChild(panel);
    return panel;
  }

  function renderRecommendations(target, list, isPersonalized, showAll = false) {
    window.FutureSkillCareers?.renderRecommendations(target, list, {
      personalized: isPersonalized,
      showAll,
      demo: Boolean(previewContext)
    });
  }

  function renderOverview() {
    const context = readSessionContext();
    heading(
      "My career overview",
      "Use your questionnaire responses as a starting point, then inspect careers and decide what you want to explore."
    );
    if (!context) {
      const panel = section(
        "Start with a direction",
        "There are no assessment results in this browser session. Browse the catalogue or take the optional assessment; no personalized recommendation will be made without results."
      );
      addLink(panel, "/", "Explore careers with the assessment", "career-button");
      addLink(panel, "/careers", "Browse the career catalogue", "career-button-secondary");
      return;
    }

    const data = context.data;
    const model = window.FutureSkillReport.buildModel(data);
    const summary = section("A short reading of your answers", "Three separate questionnaire views—not a competency test or an employment prediction.");
    const observations = el("div", "career-observations");
    [
      ["Interests", model.interestSummary],
      ["Subjects", model.subjectSummary],
      ["Self-reported confidence", model.confidenceSummary]
    ].forEach(([label, copy], index) => {
      const card = el("article", "career-observation");
      const kind = ["interest", "subject", "confidence"][index];
      const headingLabel = kind === "confidence" && !model.allSkillsEqual ? "Highest reported confidence" : label;
      card.append(el("h3", "", headingLabel), window.FutureSkillReport.compactSummary(model, kind));
      observations.appendChild(card);
    });
    summary.appendChild(observations);
    const recs = section(
      "Three careers to explore first",
      "Suggestions to explore, in engine order—not predictions of career success."
    );
    const list = el("div", "career-recommendation-grid");
    recs.appendChild(list);
    renderRecommendations(list, data.recommendations || [], true);
    addLink(recs, "/careers", "Browse the full career catalogue");
    const next = section("Choose your next step");
    addLink(next, "/careers", "Explore careers");
    addLink(next, "/my-profile", "Review interests, subjects and confidence");
    addLink(next, "/reskilling", "Open my learning pathway");
  }

  function renderProfile() {
    const context = readSessionContext();
    heading(
      "My profile & assessment",
      "Review the interests, subject preferences, and confidence ratings you reported. They are distinct from verified occupational requirements."
    );
    if (!context) {
      const panel = section("No assessment report in this session", "Take the assessment to create a report. This page will not create estimated scores.");
      addLink(panel, "/", "Explore careers with the assessment", "career-button");
      addLink(panel, "/careers", "Browse careers without an assessment", "career-button-secondary");
      return;
    }
    const report = el("div", "career-profile-report");
    content.appendChild(report);
    const model = window.FutureSkillReport.render(report, context.data, {
      onReview: () => { window.location.href = previewContext ? `/?report-demo=${encodeURIComponent(params.get("profile") || "mixed")}` : "/?review=1"; },
      profileOnly: true,
      demo: Boolean(previewContext)
    });
    const cards = report.querySelector("#careerResults");
    renderRecommendations(cards, context.data.recommendations || [], true);
    if (!model.valid) return;
  }

  function catalogCard(item, isRecommended = false, rank = 0) {
    const card = el("article", "career-catalog-item");
    const title = el("h3", "career-option-title");
    if (isRecommended) title.textContent = `${rank}. ${item.title}`;
    else title.textContent = item.title;
    card.appendChild(title);
    const metadata = el("details", "career-catalog-meta");
    metadata.append(el("summary", "", "Catalogue information"),
      el("p", "", `O*NET-SOC ${item.id} · catalogue RIASEC code ${item.riasec_top3 || "not supplied"}`));
    card.appendChild(metadata);
    const hasPathway = item.pathway?.available || item.pathway_career;
    card.appendChild(el("p", "career-pathway-status", hasPathway ? "Example pathway available · readiness not assessed" : "No linked pathway · readiness not assessed"));
    const actions = el("div", "career-catalog-actions");
    addLink(actions, `/career/${encodeURIComponent(item.id)}`, "Explore this career", "career-button");
    addLink(actions, `/compare?ids=${encodeURIComponent(item.id)}`, "Compare", "career-button-secondary");
    addLink(actions, `https://www.onetonline.org/link/summary/${encodeURIComponent(item.id)}`, "Role details: O*NET", "career-action-text");
    card.appendChild(actions);
    return card;
  }

  async function renderCatalogue(initialQuery = "") {
    heading(
      params.get("mode") === "target" ? "Choose your target career" : "Explore careers",
      "Browse occupations, not personalized recommendations. Role details are linked to O*NET; learning pathway coverage varies."
    );
    const context = readSessionContext();
    if (params.get("view") === "recommendations" && context) {
      const panel = section("Your engine recommendations", "The existing ranking uses RIASEC interests and subject preferences. Broad confidence ratings do not affect its order.");
      const list = el("div", "career-recommendation-grid");
      panel.appendChild(list);
      renderRecommendations(list, context.data.recommendations || [], true, true);
    }

    const searchPanel = section("Find a role to explore");
    const form = el("form", "career-search-form");
    form.setAttribute("role", "search");
    const input = el("input");
    input.type = "search";
    input.id = "careerSearch";
    input.name = "q";
    input.maxLength = 100;
    input.autocomplete = "off";
    input.placeholder = "Search careers by title";
    input.setAttribute("aria-label", "Search careers by title");
    input.value = initialQuery;
    const searchLabel = el("label", "career-search-label", "Search careers by title");
    searchLabel.htmlFor = input.id;
    searchPanel.appendChild(searchLabel);
    const suggestions = el("div", "career-search-suggestions");
    ["Software", "Nurse", "Teacher"].forEach(term => {
      addButton(suggestions, term, () => { input.value = term; form.requestSubmit(); }, "career-suggestion");
    });
    const submit = el("button", "career-button", "Search");
    submit.type = "submit";
    form.append(input, submit);
    searchPanel.appendChild(form);
    searchPanel.appendChild(suggestions);
    const status = el("p", "career-status");
    status.setAttribute("role", "status");
    searchPanel.appendChild(status);
    const results = el("div", "career-catalog-list");
    searchPanel.appendChild(results);
    const moreButton = el("button", "career-button-secondary", "Show more careers");
    moreButton.type = "button";
    moreButton.hidden = true;
    searchPanel.appendChild(moreButton);

    let offset = 0;
    let currentQuery = initialQuery;
    let total = 0;
    let requestVersion = 0;
    async function loadPage(reset) {
      const version = ++requestVersion;
      submit.disabled = true;
      moreButton.disabled = true;
      if (reset) {
        offset = 0;
        results.replaceChildren();
      }
      status.textContent = "Loading catalogue entries…";
      status.className = "career-status";
      try {
        const qs = new URLSearchParams({ q: currentQuery, offset: String(offset), limit: "24" });
        const payload = await jsonRequest(`/api/careers?${qs}`);
        if (version !== requestVersion) return;
        total = payload.total;
        payload.results.forEach(item => results.appendChild(catalogCard(item)));
        offset += payload.results.length;
        status.textContent = total
          ? `${offset} of ${total} catalogue entries shown.`
          : "No catalogue entries matched that title. Try a broader search.";
        moreButton.hidden = offset >= total;
      } catch (error) {
        if (version !== requestVersion) return;
        status.textContent = error.message;
        status.className = "career-status career-error";
        moreButton.hidden = true;
      } finally {
        if (version === requestVersion) { submit.disabled = false; moreButton.disabled = false; }
      }
    }
    form.addEventListener("submit", event => {
      event.preventDefault();
      currentQuery = input.value.trim();
      const url = new URL(window.location.href);
      url.searchParams.delete("view");
      url.searchParams.set("q", currentQuery);
      window.history.replaceState({}, "", url);
      loadPage(true);
    });
    moreButton.addEventListener("click", () => loadPage(false));
    await loadPage(true);
    if (params.get("mode") === "target") {
      input.focus({ preventScroll: true });
    }
  }

  function appendRiasecBars(parent, career) {
    const group = el("div", "career-riasec-rows");
    DIMENSIONS.forEach(([key, label]) => {
      const value = Number(career.riasec?.[key]);
      const row = el("div", "career-riasec-row");
      row.setAttribute("aria-label", `${label}: ${Number.isFinite(value) ? value : "not available"} on the catalogue scale`);
      row.appendChild(el("span", "", label));
      const track = el("div", "career-riasec-track");
      track.setAttribute("role", "meter");
      track.setAttribute("aria-label", `${label} career profile`);
      track.setAttribute("aria-valuemin", "0");
      track.setAttribute("aria-valuemax", "7");
      if (Number.isFinite(value)) {
        track.setAttribute("aria-valuenow", String(value));
        const fill = el("span", "career-riasec-fill");
        fill.style.width = `${Math.max(0, Math.min(100, value / 7 * 100))}%`;
        track.appendChild(fill);
      }
      row.append(track, el("span", "career-riasec-value", Number.isFinite(value) ? `${value.toFixed(2)}` : "—"));
      group.appendChild(row);
    });
    parent.appendChild(group);
    parent.appendChild(el(
      "p",
      "career-source-note",
      "These are the career dataset’s existing values on a 0–7 scale. Their provenance and validation are not independently established here. They are not learner scores or measures of career success."
    ));
  }

  function appendSdgs(parent, alignment, career, returnTo) {
    const panel = el("section", "career-panel");
    panel.appendChild(el("h2", "", "Potential SDG connections"));
    const mappings = Array.isArray(alignment?.mappings) ? alignment.mappings : [];
    if (mappings.length) {
      mappings.forEach(mapping => {
        const article = el("article", "career-observation");
        article.appendChild(el("h3", "", `SDG ${mapping.sdg_id} · Target ${mapping.target_id}`));
        article.appendChild(el("p", "", mapping.relevance_reason || mapping.target_summary || "No rationale is available in the current reviewed mapping."));
        if (mapping.evidence?.length) {
          const list = el("ul");
          mapping.evidence.forEach(point => list.appendChild(el("li", "", point)));
          article.appendChild(list);
        }
        panel.appendChild(article);
      });
      panel.appendChild(el("p", "career-source-note", alignment.evidence_scope || "Potential relationship only; this mapping does not establish measured impact."));
    } else {
      panel.appendChild(el(
        "p",
        "career-alert",
        alignment?.evidence_scope || "No reviewed role-to-target mapping is available. No connection is inferred."
      ));
    }
    const query = new URLSearchParams({ career_id: career.id, career: career.title });
    if (returnTo) query.set("return_to", returnTo);
    addLink(panel, `/sdg-impact?${query}`, "Open the SDG evidence view");
    parent.appendChild(panel);
  }

  function appendTrend(parent, trendData, career, returnTo) {
    const panel = el("section", "career-panel");
    panel.appendChild(el("h2", "", "AI and work-trend context"));
    const categories = Array.isArray(trendData?.categories) ? trendData.categories : [];
    const match = categories.find(category =>
      Array.isArray(category.careers) &&
      category.careers.some(title => title.toLocaleLowerCase() === career.title.toLocaleLowerCase())
    );
    if (match) {
      panel.appendChild(el("p", "", `${match.category}: ${match.historical_trend} historically; ${match.future_trend} in the scenario.`));
      panel.appendChild(el("p", "career-alert", "This is a qualitative, rule-based category scenario—not a validated occupation-specific forecast."));
    } else {
      panel.appendChild(el("p", "career-muted", "The current trend prototype has no career-specific mapping for this occupation. No trend is inferred from its title."));
    }
    if (trendData?.source) panel.appendChild(el("p", "career-muted", trendData.source));
    if (Array.isArray(trendData?.limitations) && trendData.limitations.length) {
      const details = el("details", "career-engine-details");
      details.appendChild(el("summary", "", "Trend source and limitations"));
      const list = el("ul");
      trendData.limitations.forEach(item => list.appendChild(el("li", "", item)));
      details.appendChild(list);
      panel.appendChild(details);
    }
    const query = new URLSearchParams({ career_id: career.id });
    if (returnTo) query.set("return_to", returnTo);
    addLink(panel, `/ai-trend?${query}`, "Open AI trends");
    parent.appendChild(panel);
  }

  async function renderDetail(id) {
    if (!ID_PATTERN.test(id)) throw new Error("This career ID is not a valid catalogue identifier.");
    const career = await jsonRequest(`/api/careers/${encodeURIComponent(id)}`);
    const recommendation = getRecommendation(id);
    const rank = recommendations().findIndex(item => item.id === id) + 1;
    const returnTo = `/career/${encodeURIComponent(id)}`;
    heading(career.title, "Explore catalogue evidence before deciding whether this role interests you.", "Career details");
    const work = section(recommendation ? "Why this appeared" : "About your selected career");
    if (recommendation) {
      work.appendChild(el("p", "", `This role appeared at position ${rank} in the assessment engine’s returned order. ${recommendation.explanation || "The engine did not return a text explanation for this entry."}`));
      work.appendChild(el("p", "career-muted", "The engine ranks using RIASEC interests and subject preferences. The broad self-reported skill ratings are not ranking inputs."));
    } else {
      work.appendChild(el("p", "", "You opened this catalogue entry directly; it is not presented as a personalized recommendation."));
    }
    work.appendChild(el("p", "career-muted", "Local sourced duties are unavailable. Inspect the official profile for work activities and requirements."));
    addLink(work, career.profile_url, "Open O*NET OnLine occupation profile");

    const interest = section("Catalogue evidence");
    const catalogueDetails = el("details", "career-engine-details");
    catalogueDetails.append(el("summary", "", "Interest profile & catalogue metadata"),
      el("p", "career-occupation-code", `O*NET-SOC ${career.id}`),
      el("p", "", "These imported interest values are not personal results. Local dataset provenance and validation have not been independently established."));
    appendRiasecBars(catalogueDetails, career);
    interest.appendChild(catalogueDetails);

    const startingPoint = section("Your starting point");
    startingPoint.appendChild(el("p", "", "Role-specific readiness is not assessed. Self-reported confidence is not proficiency."));
    if (career.pathway.available) {
      startingPoint.appendChild(el("p", "career-pathway-status", `A supported learning template is available for ${career.pathway.template}. Its skills and requirements are illustrative, not independently validated occupational benchmarks.`));
    } else {
      startingPoint.appendChild(el("p", "career-alert", "No supported role-specific pathway template is available for this catalogue entry. The reskilling studio will explain its available templates; do not treat another template as a verified match."));
    }
    const isDemo = params.get("demo") === "1";
    const savedProfile = await jsonRequest(isDemo ? "/api/state?demo=1&demo_scenario=fresh" : "/api/state").catch(() => null);
    if (savedProfile?.profile) {
      startingPoint.appendChild(el("p", "career-context-note",
        `Your saved learning pathway is ${savedProfile.profile.target_career}. Browsing this career does not change it.`));
      startingPoint.appendChild(el("p", "career-muted", "Any new plan requires explicit review."));
    }
    const targetQuery = new URLSearchParams({ career: career.title });
    if (isDemo) {
      targetQuery.set("demo", "1");
      targetQuery.set("demo_scenario", "fresh");
      startingPoint.appendChild(el("p", "career-context-note", "Demonstration: pathway actions use an isolated sample session."));
    }
    addLink(startingPoint, `/reskilling?${targetQuery}`, "Choose this target and review pathway options", "career-button");
    const interviewQuery = new URLSearchParams({
      career_id: career.id,
      career: career.title,
    });
    startingPoint.appendChild(el(
      "p",
      "career-muted",
      "Interview practice uses the career title for general questions; this catalogue does not provide verified role-specific requirements."
    ));
    addLink(
      startingPoint,
      `/interview-practice/?${interviewQuery}`,
      "Practise for this career",
      "career-button-secondary"
    );

    const tryIt = section("Try it before choosing");
    tryIt.appendChild(el("p", "", "Open the official profile, choose one listed work activity to investigate, and write down a question about what it involves. This is an exploration exercise, not a proficiency test."));
    addLink(tryIt, career.profile_url, "Explore sourced work information");

    const [alignment, trends] = await Promise.all([
      jsonRequest("/api/sdg/mindmap", { method: "POST", body: JSON.stringify({ career_id: career.id }) }).catch(error => ({ error: error.message })),
      jsonRequest("/api/ai-trends").catch(error => ({ error: error.message }))
    ]);
    if (alignment.error) {
      const panel = section("Potential SDG connections");
      panel.appendChild(el("p", "career-alert", `SDG evidence could not be loaded: ${alignment.error}`));
    } else appendSdgs(content, alignment, career, returnTo);
    if (trends.error) {
      const panel = section("AI and work-trend context");
      panel.appendChild(el("p", "career-alert", `Trend information could not be loaded: ${trends.error}`));
    } else appendTrend(content, trends, career, returnTo);

    if (recommendation) {
      const indices = section("Assessment engine indices");
      const box = el("p", "", `This role was returned at position ${rank} of ${recommendations().length}. Existing indices: interest ${recommendation.interest_index}, subject ${recommendation.subject_index}, combined ${recommendation.match_index} on their engine scales. These values do not indicate employment outcomes.`);
      indices.appendChild(box);
      indices.appendChild(el("p", "career-muted", "The recommendation formula is unchanged. Browse or compare other careers without changing the saved learning target."));
    }
  }

  function renderComparePicker(id, label) {
    const panel = section(label, "Search and explicitly select a second catalogue role. Comparisons are limited to two.");
    const form = el("form", "career-compare-search");
    form.setAttribute("role", "search");
    const input = el("input");
    input.type = "search";
    input.maxLength = 100;
    input.placeholder = "Search a second career";
    input.setAttribute("aria-label", "Search a second career");
    const status = el("p", "career-status");
    status.setAttribute("role", "status");
    const list = el("div", "career-catalog-list");
    form.appendChild(input);
    panel.append(form, status, list);
    let request = 0;
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const thisRequest = ++request;
      status.textContent = "Searching…";
      list.replaceChildren();
      try {
        const qs = new URLSearchParams({ q: input.value.trim(), limit: "12" });
        const result = await jsonRequest(`/api/careers?${qs}`);
        if (thisRequest !== request) return;
        const choices = result.results.filter(item => item.id !== id);
        status.textContent = choices.length ? "Choose a role to compare." : "No second role matched. Try another title.";
        choices.forEach(item => {
          const card = catalogCard(item);
          const button = el("button", "career-button-secondary", `Compare with ${item.title}`);
          button.type = "button";
          button.addEventListener("click", () => {
            window.location.href = `/compare?ids=${encodeURIComponent(id)},${encodeURIComponent(item.id)}`;
          });
          card.querySelector(".career-catalog-actions").appendChild(button);
          list.appendChild(card);
        });
      } catch (error) {
        status.textContent = error.message;
        status.classList.add("career-error");
      }
    });
  }

  function addCompareRow(table, label, valueA, valueB) {
    const row = document.createElement("tr");
    const labelCell = el("th", "", label);
    const first = el("td", "", valueA);
    const second = el("td", "", valueB);
    first.dataset.label = "First career";
    second.dataset.label = "Second career";
    row.append(labelCell, first, second);
    table.querySelector("tbody").appendChild(row);
  }

  async function renderComparison(ids) {
    heading("Compare career options", "Review differences using available catalogue and assessment evidence. A comparison is not a prediction of job outcomes.");
    const valid = [...new Set(ids)].filter(id => ID_PATTERN.test(id)).slice(0, 2);
    if (valid.length < 2) {
      if (valid.length === 1) {
        const first = await jsonRequest(`/api/careers/${encodeURIComponent(valid[0])}`);
        const selected = section("First career", "Choose a second role to compare.");
        selected.appendChild(el("h3", "", first.title));
        addLink(selected, `/career/${encodeURIComponent(first.id)}`, "Open career details");
        renderComparePicker(first.id, "Add a second career");
      } else {
        renderComparePicker("", "Choose your first career");
      }
      return;
    }

    const [first, second] = await Promise.all(valid.map(id =>
      jsonRequest(`/api/careers/${encodeURIComponent(id)}`)
    ));
    const tablePanel = section("Side-by-side evidence");
    const table = document.createElement("table");
    table.className = "career-compare-table";
    const head = document.createElement("thead");
    const headRow = document.createElement("tr");
    headRow.append(el("th", "", "Evidence"), el("th", "", first.title), el("th", "", second.title));
    head.appendChild(headRow);
    const body = document.createElement("tbody");
    table.append(head, body);
    tablePanel.appendChild(table);
    addCompareRow(table, "Occupation profile", "Open official O*NET profile for work details", "Open official O*NET profile for work details");
    const profileCells = body.querySelector("tr")?.querySelectorAll("td");
    if (profileCells?.length === 2) {
      profileCells[0].replaceChildren();
      profileCells[1].replaceChildren();
      addLink(profileCells[0], first.profile_url, "Open official O*NET profile for work details");
      addLink(profileCells[1], second.profile_url, "Open official O*NET profile for work details");
    }
    const firstRec = getRecommendation(first.id);
    const secondRec = getRecommendation(second.id);
    addCompareRow(
      table,
      "Assessment engine order",
      firstRec ? `#${recommendations().findIndex(item => item.id === first.id) + 1} · interest ${firstRec.interest_index}, subject ${firstRec.subject_index}` : "No personalized assessment result in this session",
      secondRec ? `#${recommendations().findIndex(item => item.id === second.id) + 1} · interest ${secondRec.interest_index}, subject ${secondRec.subject_index}` : "No personalized assessment result in this session"
    );
    addCompareRow(
      table,
      "Learning pathway",
      first.pathway.available ? `Illustrative template: ${first.pathway.template}` : "No supported role-specific template",
      second.pathway.available ? `Illustrative template: ${second.pathway.template}` : "No supported role-specific template"
    );
    addCompareRow(table, "Skill readiness", "Not assessed by broad confidence ratings", "Not assessed by broad confidence ratings");
    addCompareRow(table, "AI trend evidence", "Only an exact existing prototype mapping is shown on detail", "Only an exact existing prototype mapping is shown on detail");
    addCompareRow(table, "SDG evidence", "Reviewed mappings only; see detail view", "Reviewed mappings only; see detail view");
    table.querySelectorAll("td").forEach((cell, index) => {
      cell.setAttribute("data-label", index % 2 === 0 ? first.title : second.title);
    });
    const interests = section("Catalogue interest profiles");
    const grid = el("div", "career-recommendation-grid");
    [first, second].forEach(item => {
      const card = el("article", "career-observation");
      card.append(el("h3", "", item.title));
      appendRiasecBars(card, item);
      addLink(card, `/career/${encodeURIComponent(item.id)}`, "Open details");
      grid.appendChild(card);
    });
    interests.appendChild(grid);
    const actions = section("Continue exploring");
    addLink(actions, `/career/${encodeURIComponent(first.id)}`, `Explore ${first.title}`);
    addLink(actions, `/career/${encodeURIComponent(second.id)}`, `Explore ${second.title}`);
    addLink(actions, "/careers", "Return to career search");
  }

  function initMobileSidebar() {
    const toggle = document.getElementById("careerWorkspaceToggle");
    const sidebar = document.getElementById("careerWorkspaceSidebar");
    toggle?.addEventListener("click", () => {
      const open = toggle.getAttribute("aria-expanded") !== "true";
      toggle.setAttribute("aria-expanded", String(open));
      sidebar.classList.toggle("is-open", open);
    });
    document.addEventListener("keydown", event => {
      if (event.key !== "Escape" || !sidebar?.classList.contains("is-open")) return;
      sidebar.classList.remove("is-open");
      toggle?.setAttribute("aria-expanded", "false");
      toggle?.focus();
    });
  }

  async function start() {
    initMobileSidebar();
    let path = window.location.pathname;
    try {
      if (window.FutureSkillCareerPreview) {
        const patterns = {
          "equal-high": [5,5,5,5,5,5], "equal-low": [1,1,1,1,1,1],
          differentiated: [5,4,3,2,4,1], "leading-tie": [5,5,3,2,4,1], mixed: [4,2,5,3,1,4]
        };
        const name = params.get("profile") || "mixed";
        const values = patterns[name];
        if (!values) throw new Error("Unknown sample assessment profile.");
        const rating = name === "equal-high" ? 5 : name === "equal-low" ? 1 : 3;
        const answers = {
          answers: Object.fromEntries(["R","I","A","S","E","C"].map((key,index) => [key,Array(4).fill(values[index])])),
          subject_answers: Object.fromEntries(["IT","Math","Education","Health","Business","Engineering"].map(key => [key,[rating,rating]])),
          skill_answers: Object.fromEntries(["MathSkill","CodingSkill","DataSkill","CommunicationSkill","LeadershipSkill","CreativeSkill"].map(key => [key,rating]))
        };
        previewContext = { data: await jsonRequest("/api/recommend", {method:"POST",body:JSON.stringify(answers)}) };
        path = params.get("view") === "profile" ? "/my-profile" : "/career-overview";
        const banner = el("p", "career-demo-banner", "DEVELOPMENT DEMO — isolated sample answers. Your saved assessment and learning plan are unchanged.");
        content.appendChild(banner);
        const pathway = document.querySelector('[data-workspace-nav="pathway"]');
        if (pathway) pathway.href = "/reskilling?demo=1&demo_scenario=fresh";
      }
      setActiveNavigation(path);
      if (previewContext) {
        [["overview","overview"],["profile","profile"]].forEach(([nav,view]) => {
          const link = document.querySelector(`[data-workspace-nav="${nav}"]`);
          if (link) link.href = `/__dev/career-preview?view=${view}&profile=${encodeURIComponent(params.get("profile") || "mixed")}`;
        });
      }
      if (path === "/career-overview") renderOverview();
      else if (path === "/my-profile") renderProfile();
      else if (path === "/compare") await renderComparison((params.get("ids") || "").split(",").filter(Boolean));
      else if (path.startsWith("/career/")) await renderDetail(decodeURIComponent(path.slice("/career/".length)));
      else await renderCatalogue(params.get("q") || "");
    } catch (error) {
      content.replaceChildren();
      const panel = el("section", "career-panel career-error");
      panel.setAttribute("role", "alert");
      panel.append(el("h1", "career-page-heading", "Career information unavailable"), el("p", "", error.message));
      addLink(panel, "/careers", "Return to career search", "career-button-secondary");
      content.appendChild(panel);
    } finally {
      content.querySelector(".career-loading")?.remove();
    }
  }

  start();
})();
