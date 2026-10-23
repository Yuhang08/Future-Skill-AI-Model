(function (root) {
  "use strict";

  const TYPES = [
    {
      key: "R", name: "Realistic", icon: "R",
      activity: "Build or repair equipment; work physically or outdoors.",
      detail: "This area concerns practical, hands-on activities such as working with tools, equipment, materials, or the outdoors.",
      question: "Would you like to try a small repair, build, or outdoor project?",
      source: "onet-interest-types"
    },
    {
      key: "I", name: "Investigative", icon: "I",
      activity: "Study or research objects, organisms, data, or human behavior.",
      detail: "This area concerns investigating questions, studying how things work, and researching evidence about the world or people.",
      question: "What question could you investigate using observation, reading, or a small experiment?",
      source: "onet-interest-types"
    },
    {
      key: "A", name: "Artistic", icon: "A",
      activity: "Make original art, design, writing, or music.",
      detail: "This area concerns creating original work and expressing ideas through visual art, design, writing, music, or other media.",
      question: "What would you enjoy making if you could choose the format and audience?",
      source: "onet-interest-types"
    },
    {
      key: "S", name: "Social", icon: "S",
      activity: "Help, teach, advise, or serve other people.",
      detail: "This area concerns activities centered on helping people, teaching, advising, supporting, or providing a service.",
      question: "Who might benefit from something you could explain, teach, or help with?",
      source: "onet-interest-types"
    },
    {
      key: "E", name: "Enterprising", icon: "E",
      activity: "Manage, negotiate, market, sell, or lead.",
      detail: "This area concerns persuading or coordinating with others, leading initiatives, and activities such as marketing, sales, negotiation, or management.",
      question: "What idea or small project would you like to organize people around?",
      source: "onet-interest-types"
    },
    {
      key: "C", name: "Conventional", icon: "C",
      activity: "Follow procedures to organize information or data.",
      detail: "This area concerns organizing information, maintaining records, and following established procedures to work with data.",
      question: "What information could you organize into a clear, useful system?",
      source: "onet-interest-types"
    }
  ];
  const SUBJECTS = [
    ["IT", "Computing & technology", "This area includes software, digital tools, and computing systems.", "What is one everyday task you would like a small program or digital tool to make easier?"],
    ["Math", "Mathematics & statistics", "This area includes mathematical reasoning, measurement, statistics, and patterns in data.", "What real-world question could you explore with numbers or a small dataset?"],
    ["Education", "Teaching & learning", "This area includes how people learn, how ideas are explained, and how learning activities are designed.", "What is something you know that you could explain in a way a younger learner might understand?"],
    ["Health", "Health & medicine", "This area includes human health, medicine, care, and health-related research.", "Which question about health or the human body would you like to learn more about, and where could you find a reliable source?"],
    ["Business", "Business & enterprise", "This area includes how organizations plan, serve customers, manage resources, and communicate value.", "What small community need could a simple service or organization help address?"],
    ["Engineering", "Engineering & design", "This area includes applying science and design to create or improve systems and practical solutions.", "What everyday object or process would you redesign, and what would you change first?"]
  ];
  const SKILLS = [
    ["MathSkill", "Mathematical & logical problem-solving", "Work through a puzzle or explain how you reached an answer."],
    ["CodingSkill", "Coding & debugging", "Build a tiny program or trace and fix a simple bug."],
    ["DataSkill", "Data analysis", "Use a small public dataset or table to describe one pattern."],
    ["CommunicationSkill", "Communication", "Explain an idea in writing or aloud and ask someone what was clear."],
    ["LeadershipSkill", "Planning & team coordination", "Plan a small shared task, then reflect on how the coordination went."],
    ["CreativeSkill", "Creative problem-solving", "Generate a few different approaches to one everyday challenge."]
  ];
  const SKILL_LABELS = Object.fromEntries(SKILLS.map(item => [item[0], item[1]]));
  const ORDER = ["R", "I", "A", "S", "E", "C"];
  const LABELS = Object.fromEntries(TYPES.map(type => [type.key, type.name]));
  const SOURCES = Object.freeze({
    "onet-interest-types": Object.freeze({
      id: "onet-interest-types",
      title: "Browse by Career Interest Types",
      publisher: "U.S. Department of Labor, Employment and Training Administration / O*NET OnLine",
      url: "https://www.onetonline.org/find/descriptor/browse/1.B.1",
      claims: "Supports the general work-activity interpretations shown beside each RIASEC interest area."
    }),
    "onet-interest-profiler": Object.freeze({
      id: "onet-interest-profiler",
      title: "O*NET Interest Profiler",
      publisher: "U.S. Department of Labor, Employment and Training Administration / O*NET Resource Center",
      url: "https://www.onetcenter.org/IP.html",
      claims: "Supports the six interest-type framework and career exploration only. FutureSkill's custom questionnaire is not the official O*NET instrument and does not inherit its validation, norms, or reliability."
    }),
    "onet-occupation-profiles": Object.freeze({
      id: "onet-occupation-profiles",
      title: "O*NET OnLine occupation profiles",
      publisher: "U.S. Department of Labor, Employment and Training Administration",
      url: "https://www.onetonline.org/",
      claims: "Links to the matching occupation profile for learners to inspect. FutureSkill does not reproduce occupational duties or requirements that are absent from its local catalogue."
    }),
    "futureskill-method": Object.freeze({
      id: "futureskill-method",
      title: "How this report is calculated",
      publisher: "FutureSkill",
      url: "#report-methodology",
      claims: "Describes this site's calculation and limitations; it is not an external validation source."
    })
  });

  const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  const exactKeys = (value, keys) => value && typeof value === "object" &&
    !Array.isArray(value) && keys.length === Object.keys(value).length &&
    keys.every(key => own(value, key));
  const numericRange = (value, min, max) => typeof value === "number" &&
    Number.isFinite(value) && value >= min && value <= max;
  const invalid = error => ({
    valid: false, error, interestSummary: "", subjectSummary: "",
    confidenceSummary: "", allInterestsEqual: false, leadingInterests: [],
    hasInterestTies: false
  });

  function buildModel(data) {
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      return invalid("A results object is needed to prepare this report.");
    }
    if (!exactKeys(data.riasec_scores, ORDER) ||
        !ORDER.every(key => numericRange(data.riasec_scores[key], 20, 100))) {
      return invalid("Interest results are incomplete or outside the expected 20–100 range. No scores have been estimated.");
    }
    const subjectKeys = SUBJECTS.map(item => item[0]);
    if (!exactKeys(data.subject_preferences, subjectKeys) ||
        !subjectKeys.every(key => numericRange(data.subject_preferences[key], 1, 5))) {
      return invalid("Subject results are incomplete or outside the expected 1–5 range. No scores have been estimated.");
    }
    const skillKeys = SKILLS.map(item => item[0]);
    if (!exactKeys(data.skills, skillKeys) ||
        !skillKeys.every(key => numericRange(data.skills[key], 1, 5))) {
      return invalid("Confidence ratings are incomplete or outside the expected 1–5 range. No scores have been estimated.");
    }
    const expectedCode = [...ORDER].sort((a, b) =>
      data.riasec_scores[b] - data.riasec_scores[a]).slice(0, 3).join("");
    if (data.top3 !== expectedCode ||
        !Array.isArray(data.recommendations) ||
        !data.recommendations.every(item => item && typeof item === "object" &&
          typeof item.title === "string" && item.title.trim() &&
          numericRange(item.match_index, 0, 100) &&
          typeof item.riasec === "string" && /^[RIASEC]{3}$/.test(item.riasec) &&
          typeof item.fields === "string" && typeof item.explanation === "string" &&
          numericRange(item.interest_index, 0, 100) &&
          numericRange(item.subject_index, 0, 100))) {
      return invalid("Career recommendation data is incomplete or in an unexpected format. Your profile scores are not being replaced.");
    }

    const highest = Math.max(...ORDER.map(key => data.riasec_scores[key]));
    const leading = ORDER.filter(key => data.riasec_scores[key] === highest);
    const lowest = Math.min(...ORDER.map(key => data.riasec_scores[key]));
    const allInterestsEqual = highest === lowest;
    const interestTieGroups = [...new Set(ORDER.map(key => data.riasec_scores[key]))]
      .filter(score => ORDER.filter(key => data.riasec_scores[key] === score).length > 1)
      .map(score => ({ score, areas: ORDER.filter(key => data.riasec_scores[key] === score) }));
    const subjectMax = Math.max(...subjectKeys.map(key => data.subject_preferences[key]));
    const subjectLeaders = subjectKeys.filter(key => data.subject_preferences[key] === subjectMax);
    const skillValues = skillKeys.map(key => data.skills[key]);
    const allSkillsEqual = skillValues.every(value => value === skillValues[0]);
    const ordered = ORDER.map(key => ({ key, name: LABELS[key], score: data.riasec_scores[key] }))
      .sort((a, b) => b.score - a.score || ORDER.indexOf(a.key) - ORDER.indexOf(b.key));
    const cutoffScore = ordered[Math.min(2, ordered.length - 1)].score;
    const cutoffAreas = ordered.filter(item => item.score === cutoffScore).map(item => item.key);
    const interests = allInterestsEqual
      ? `Your answers do not identify a clear leading interest area. All six interest scores are ${highest} / 100.`
      : leading.length > 1
        ? `Your highest interest areas are tied: ${leading.map(key => LABELS[key]).join(", ")}.`
        : `Your highest interest area is ${LABELS[leading[0]]}. This is a starting point for exploration, not a label.`;
    const subjectSummary = subjectLeaders.length === subjectKeys.length
      ? `Your subject ratings are equal at ${subjectMax} / 5; none is distinguished.`
      : subjectLeaders.length > 1
        ? `Your highest subject ratings are tied across ${subjectLeaders.map(key => SUBJECTS.find(item => item[0] === key)[1]).join(", ")}.`
        : `${SUBJECTS.find(item => item[0] === subjectLeaders[0])[1]} has your highest subject rating.`;
    const maxConfidence = Math.max(...skillValues);
    const minConfidence = Math.min(...skillValues);
    const highestConfidenceSkills = skillKeys.filter(key => data.skills[key] === maxConfidence);
    const lowestConfidenceSkills = skillKeys.filter(key => data.skills[key] === minConfidence);
    const confidenceSummary = allSkillsEqual
      ? `You rated every skill ${maxConfidence} / 5 for confidence.`
      : `Your highest confidence rating is ${maxConfidence} / 5 for ${highestConfidenceSkills.map(key => SKILL_LABELS[key]).join(", ")}; your lowest is ${minConfidence} / 5 for ${lowestConfidenceSkills.map(key => SKILL_LABELS[key]).join(", ")}.`;
    const meanInterest = ORDER.reduce((sum, key) => sum + data.riasec_scores[key], 0) / ORDER.length;
    const aboveMean = ordered.filter(item => item.score > meanInterest);
    const combinedAreas = aboveMean.length >= 2 && aboveMean[0].score !== aboveMean[1].score
      ? [aboveMean[0], aboveMean[1]]
      : [];
    return {
      valid: true, data, ordered, leadingInterests: leading,
      allInterestsEqual, hasInterestTies: interestTieGroups.length > 0,
      interestTieGroups,
      interestSummary: interests, subjectSummary, confidenceSummary,
      subjectLeaders, allSubjectsEqual: subjectLeaders.length === subjectKeys.length,
      allSkillsEqual, cutoffAreas, cutoffScore, maxConfidence, minConfidence,
      highestConfidenceSkills, lowestConfidenceSkills, combinedAreas
    };
  }

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = String(text);
    return element;
  }
  function section(title, intro, id) {
    const element = node("section", "report-section");
    if (id) element.id = id;
    const heading = node("h2", "", title);
    element.appendChild(heading);
    if (intro) element.appendChild(node("p", "report-intro", intro));
    return element;
  }
  function meter(label, value, min, max, suffix) {
    const wrap = node("div", "report-meter");
    const heading = node("div", "report-meter-heading");
    const name = node("span", "report-meter-label", label);
    const exact = node("strong", "report-meter-value", `${value} ${suffix}`);
    heading.append(name, exact);
    const progress = node("div", "report-meter-track");
    progress.setAttribute("role", "meter");
    progress.setAttribute("aria-label", label);
    progress.setAttribute("aria-valuemin", String(min));
    progress.setAttribute("aria-valuemax", String(max));
    progress.setAttribute("aria-valuenow", String(value));
    const fill = node("span", "report-meter-fill");
    fill.style.width = `${Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))}%`;
    progress.appendChild(fill);
    wrap.append(heading, progress);
    return wrap;
  }
  function sourceLink(id, text) {
    const source = SOURCES[id];
    const link = node("a", "report-source-link", text || source.title);
    link.href = source.url;
    if (!source.url.startsWith("#")) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
    return link;
  }
  function interestIcon(type) {
    // Activity cues, not psychological badges. Geometry is local, not user input.
    const paths = {
      R: "M14 6a5 5 0 0 0-6 6L3 17l4 4 5-5a5 5 0 0 0 6-6l-3 3-4-4z",
      I: "M16 16l5 5M18 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0z",
      A: "M4 20l1-5L16 4l4 4L9 19zM14 6l4 4M4 20l5-1",
      S: "M4 21v-3a5 5 0 0 1 10 0v3M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM17 4a4 4 0 0 1 0 7M18 14a5 5 0 0 1 4 5v2",
      E: "M5 22V3M5 4h14l-3 5 3 5H5",
      C: "M3 4h18v16H3zM3 9h18M9 9v11M13 13h4M13 16h4"
    };
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", "22");
    svg.setAttribute("height", "22");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    const path = document.createElementNS(svg.namespaceURI, "path");
    path.setAttribute("d", paths[type.key]);
    path.setAttribute("stroke", "currentColor");
    path.setAttribute("stroke-width", "1.6");
    path.setAttribute("stroke-linecap", "round");
    path.setAttribute("stroke-linejoin", "round");
    path.setAttribute("fill", "none");
    svg.appendChild(path);
    const icon = node("span", "report-type-icon");
    icon.setAttribute("role", "img");
    icon.setAttribute("aria-label", `${type.name} activity illustration`);
    icon.appendChild(svg);
    return icon;
  }
  function render(container, data, options) {
    if (!container) return invalid("The report container is unavailable.");
    const model = buildModel(data);
    container.replaceChildren();
    container.classList.add("assessment-report");
    if (!model.valid) {
      const panel = node("section", "report-error");
      panel.setAttribute("role", "alert");
      panel.append(node("h2", "", "This report could not be prepared"), node("p", "", model.error));
      container.appendChild(panel);
      return model;
    }

    const report = node("div", "report-content");
    const intro = node("div", "report-overview");
    intro.id = "report-overview";
    intro.append(node("p", "report-eyebrow", "A guide for reflection"),
      node("h2", "", "Your results at a glance"),
      node("p", "report-lede", "Three separate views of what you reported—not a verified competency test or a prediction of employment."));
    const summaryGrid = node("div", "report-summary-grid");
    [
      ["Interests", model.interestSummary],
      ["Subjects", model.subjectSummary],
      ["Confidence", model.confidenceSummary]
    ].forEach(([label, text]) => {
      const card = node("article", "report-summary");
      card.append(node("h3", "", label), node("p", "", text));
      summaryGrid.appendChild(card);
    });
    intro.appendChild(summaryGrid);
    const jumpLinks = node("nav", "report-jump-links");
    jumpLinks.setAttribute("aria-label", "Results report sections");
    [["#report-overview", "Overview"], ["#report-interests", "Interests"],
      ["#report-subjects", "Subjects"], ["#report-confidence", "Confidence"],
      ["#report-careers", "Careers"]]
      .forEach(([href, label]) => {
        const link = node("a", "", label);
        link.href = href;
        jumpLinks.appendChild(link);
      });
    if (!options.hideJumpNavigation) intro.appendChild(jumpLinks);
    report.appendChild(intro);

    const careerSection = section(
      "Your career possibilities",
      "These are the first three entries from the existing career engine, shown for easier exploration—not a statistically established shortlist or a prediction of outcomes.",
      "report-careers"
    );
    careerSection.querySelector("h2").id = "careerRecommendationsHeading";
    careerSection.appendChild(node("div", "report-career-list"));
    const careerResults = node("div", "report-career-results");
    careerResults.id = "careerResults";
    careerSection.appendChild(careerResults);
    report.appendChild(careerSection);

    const interestSection = section("Your career interests — RIASEC",
      "You reported how much you enjoy work activities. Scores use the existing 20–100 scale: four answers summed, divided by 20, then multiplied by 100.",
      "report-interests");
    const code = node("div", "report-code");
    code.append(node("span", "", "Calculated interest code"), node("strong", "", data.top3));
    if (!model.hasInterestTies) interestSection.appendChild(code);
    interestSection.appendChild(node("p", "report-intro",
      "These scores are not percentiles, probabilities of career success, or percentages of your personality. The bars share a 20–100 axis; 20 is the minimum possible response score, not an absence of interests."));
    const sourceCaveat = node("p", "report-citation",
      "General activity descriptions are adapted from O*NET. This custom questionnaire is not the official Interest Profiler and does not inherit its validation, norms, or reliability. ");
    sourceCaveat.appendChild(sourceLink("onet-interest-profiler", "About the official instrument"));
    interestSection.appendChild(sourceCaveat);
    const codeNote = model.hasInterestTies
      ? "Equal scores follow the fixed R–I–A–S–E–C ordering in the displayed three-letter code. A letter's position in a tie does not establish a primary, secondary, or tertiary strength."
      : "The code shows the three highest calculated interest scores. It is a shorthand for these responses, not a fixed personal identity.";
    const codeDetails = node("details", "report-details");
    codeDetails.append(node("summary", "", "Why this code?"),
      node("p", "", codeNote));
    if (model.hasInterestTies) codeDetails.appendChild(code);
    interestSection.appendChild(codeDetails);
    if (model.combinedAreas.length >= 2) {
      const first = TYPES.find(type => type.key === model.combinedAreas[0].key);
      const second = TYPES.find(type => type.key === model.combinedAreas[1].key);
      interestSection.appendChild(node("p", "report-pattern",
        `A possible combination to explore: ${first.name} and ${second.name}. Try these two reflection questions together: “${first.question}” and “${second.question}” This is an exploratory prompt, not a role recommendation.`));
    } else if (!model.allInterestsEqual && model.leadingInterests.length === 1) {
      interestSection.appendChild(node("p", "report-pattern",
        `One possible starting point for exploration is ${LABELS[model.leadingInterests[0]]}. This is not a label or prediction.`));
    }
    if (model.interestTieGroups.length && !model.allInterestsEqual) {
      codeDetails.appendChild(node("p", "report-note",
        `Tied interest scores: ${model.interestTieGroups.map(group => `${group.areas.map(key => LABELS[key]).join(", ")} (${group.score})`).join("; ")}. Ties are not ordered as primary, secondary, or tertiary strengths.`));
    }
    if (model.cutoffAreas.length > 1 && !model.allInterestsEqual) {
      codeDetails.appendChild(node("p", "report-note",
        `There is also a tie at the three-area profile-code cutoff: ${model.cutoffAreas.map(key => LABELS[key]).join(", ")} share a score of ${model.cutoffScore}. The code is not used in recommendation ranking.`));
    }
    const interestList = node("div", "report-interest-list");
    model.ordered.forEach(item => {
      const type = TYPES.find(entry => entry.key === item.key);
      const article = node("article", "report-interest");
      const heading = node("div", "report-interest-head");
      const icon = interestIcon(type);
      icon.setAttribute("aria-label", `${type.name} interest icon`);
      const titleWrap = node("div", "");
      titleWrap.append(node("h3", "", type.name), node("p", "report-activity", type.activity));
      heading.append(icon, titleWrap);
      article.appendChild(heading);
      article.appendChild(meter(`${type.name} interest score`, item.score, 20, 100, "/ 100"));
      const details = node("details", "report-details");
      details.appendChild(node("summary", "", "More about this area"));
      details.append(node("p", "", type.detail), node("p", "report-question", `Explore: ${type.question}`));
      const citation = node("p", "report-citation", "General activity interpretation: ");
      citation.append(sourceLink(type.source, "O*NET interest-type descriptions"));
      details.appendChild(citation);
      article.appendChild(details);
      interestList.appendChild(article);
    });
    interestSection.appendChild(interestList);
    report.appendChild(interestSection);

    const subjectSection = section("Your subject preferences",
      "You reported enjoyment of subject activities on a 1–5 scale. Interest does not demonstrate subject ability. The meanings and questions below are FutureSkill reflection prompts, not validated ability interpretations.",
      "report-subjects");
    const subjectList = node("div", "report-list");
    SUBJECTS.forEach(([key, name, meaning, question]) => {
      const article = node("article", "report-row");
      article.append(node("h3", "", name), meter(`${name} interest`, data.subject_preferences[key], 1, 5, "/ 5"));
      const details = node("details", "report-details");
      details.appendChild(node("summary", "", "Explore this subject"));
      details.append(node("p", "report-activity", meaning), node("p", "report-question", `Explore: ${question}`));
      article.appendChild(details);
      subjectList.appendChild(article);
    });
    subjectSection.appendChild(subjectList);
    if (model.allSubjectsEqual) subjectSection.appendChild(node("p", "report-note", "Your subject ratings are equal, so none is distinguished."));
    report.appendChild(subjectSection);

    const skillSection = section("Your self-reported skills",
      "These 1–5 ratings describe reported confidence, not independently assessed proficiency or occupational readiness. A lower rating alone is not a weakness. Practice can help you gather examples, but does not verify proficiency without an assessment and rubric. These broad ratings are separate from role-specific requirements and do not affect career rankings.",
      "report-confidence");
    const skillList = node("div", "report-list");
    SKILLS.forEach(([key, name, activity]) => {
      const article = node("article", "report-row");
      article.append(node("h3", "", name), meter(`${name} confidence`, data.skills[key], 1, 5, "/ 5"));
      const details = node("details", "report-details");
      details.appendChild(node("summary", "", "Build an example"));
      details.appendChild(node("p", "report-evidence", `A possible practice activity: ${activity}`));
      article.appendChild(details);
      skillList.appendChild(article);
    });
    skillSection.appendChild(skillList);
    if (model.allSkillsEqual) skillSection.appendChild(node("p", "report-note", "All six skills have the same confidence rating."));
    report.appendChild(skillSection);

    const next = section("What to explore next",
      data.recommendations.length
        ? `The engine returned ${data.recommendations.length} careers, starting with ${data.recommendations[0].title}. Explore their work activities rather than treating the order as a verdict.`
        : "No engine recommendations were returned. You can still review your answers or explore the explicitly labeled prototype learning templates.");
    const steps = node("ol", "report-next-steps");
    [
      ["Review your answers", "Notice which activities felt easy to choose and which were harder to rate. You can revisit your responses without treating any one answer as a label."],
      ["Try one low-stakes activity", "Choose a short project from an interest or subject above. Afterwards, note what held your attention and what you would change."],
      ["Explore a learning pathway", "Career cards link to reskilling. Only explicitly mapped roles have a supported pathway; other careers offer a choice of five labeled prototype templates, not invented occupational requirements."]
    ].forEach(([title, description], index) => {
      const item = node("li", "");
      item.append(node("span", "report-step-number", `0${index + 1}`),
        node("div", "", ""));
      item.lastChild.append(node("h3", "", title), node("p", "", description));
      steps.appendChild(item);
    });
    next.appendChild(steps);
    const aiNotice = node("p", "report-ai-notice",
      "Assessment review is not available through the current AI service. This deterministic report remains available, and your assessment answers are not sent to an AI service.");
    next.appendChild(aiNotice);
    const actions = node("div", "report-actions");
    const review = node("button", "report-button", "Review my answers");
    review.type = "button";
    review.addEventListener("click", () => {
      if (options && typeof options.onReview === "function") options.onReview();
    });
    const pathway = node("a", "report-pathway", "Explore reskilling options");
    pathway.id = "resultsPathwayLink";
    const careers = node("a", "report-careers-link", "View career recommendations");
    careers.href = "#careerRecommendationsHeading";
    const demo = Boolean(options && options.demo);
    pathway.href = demo
      ? "/reskilling?demo=1&demo_scenario=fresh"
      : "/reskilling";
    actions.append(review, careers, pathway);
    next.appendChild(actions);
    report.appendChild(next);

    const methodology = section("How to read this report", "", "report-methodology");
    const methodDetails = node("details", "report-details report-method-details");
    methodDetails.appendChild(node("summary", "", "Calculation, sources & limitations"));
    const methodText = node("div", "report-method-copy");
    methodText.append(
      node("p", "", "No close-score threshold or statistical significance is inferred. The report compares exact calculated values, discloses ties, and offers reflection questions rather than diagnoses."),
      node("p", "", "FutureSkill’s recommendation engine uses a 65% interest index and 35% subject index. The interest index combines 85% scaled Pearson profile-shape similarity and 15% above-your-own-mean emphasis; a flat profile is neutral at 50. Subject fields use title-matching heuristics, with unclassified fields neutral, and diversity selection can change recommendation order. The three-letter profile code is not an input to ranking. Where there is a tie at the code cutoff, this report names every tied area."),
      node("p", "", "Skills are not ranking inputs. Any “Shared interest strengths” shown on career cards means interests above your own profile mean; it does not verify a skill. Career recommendations are exploratory, not probabilities or evidence of occupational fit."),
      node("p", "", "This FutureSkill questionnaire is custom and is NOT the official O*NET Interest Profiler. It does not inherit the official instrument’s validation, norms, or reliability. The six interest areas are provided here for career exploration only.")
    );
    const sourceList = node("ul", "report-sources");
    Object.values(SOURCES).forEach(source => {
      const item = node("li", "");
      item.append(sourceLink(source.id), node("span", "", ` — ${source.publisher}. ${source.claims}`));
      sourceList.appendChild(item);
    });
    methodText.appendChild(sourceList);
    methodDetails.appendChild(methodText);
    methodology.appendChild(methodDetails);
    report.appendChild(methodology);
    container.appendChild(report);
    return model;
  }

  const api = Object.freeze({ buildModel, render, SOURCES });
  root.FutureSkillReport = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
