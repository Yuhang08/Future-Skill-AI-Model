/* Shared, data-safe career recommendation cards for the results and workspace. */
(function (root) {
  "use strict";

  const TYPE_NAMES = {
    R: "Realistic", I: "Investigative", A: "Artistic",
    S: "Social", E: "Enterprising", C: "Conventional"
  };
  const CAREER_ID = /^\d{2}-\d{4}\.\d{2}$/;

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }

  function link(href, label, className) {
    const node = element("a", className, label);
    node.href = href;
    return node;
  }

  function engineExplanation(career) {
    const raw = typeof career.explanation === "string" ? career.explanation : "";
    const match = /^Shared interest strengths:\s*(.*?)\.\s*Detected career fields:\s*(.*)\.$/.exec(raw);
    if (!match) return raw || "No personalized engine explanation is available for this role.";
    const areas = match[1] === "limited overlap"
      ? "limited overlap"
      : match[1].split(",").map(code => TYPE_NAMES[code.trim()] || code.trim()).join(", ");
    return `Reported interest areas above your own average: ${areas}. Title-based subject tags: ${match[2] || "none"}. These tags are a title-matching heuristic, not verified occupational requirements.`;
  }

  function scoreDetails(career) {
    const details = element("details", "career-engine-details");
    details.appendChild(element("summary", "", "How the existing engine ranked this role"));
    details.appendChild(element(
      "p",
      "",
      "These catalogue indices use the engine’s existing 0–100 scale. They are not percentages, employment probabilities, or evidence of occupational proficiency."
    ));
    const list = element("dl", "career-index-list");
    [
      ["Engine order", career.rank ? `${career.rank} of ${career.total || "the returned list"}` : ""],
      ["Interest index", career.interest_index],
      ["Subject index", career.subject_index],
      ["Combined engine index", career.match_index]
    ].forEach(([label, raw]) => {
      if (raw === "" || raw === undefined || raw === null || !Number.isFinite(Number(raw))) return;
      list.append(element("dt", "", label), element("dd", "", String(raw)));
    });
    if (list.childNodes.length) details.appendChild(list);
    return details;
  }

  function renderCard(career, rank, options) {
    const card = element("article", "career-result-card");
    card.dataset.careerId = CAREER_ID.test(String(career.id || "")) ? career.id : "";

    const head = element("div", "career-result-heading");
    head.append(element("p", "career-rank", `Recommendation ${rank}`));
    head.appendChild(element("h3", "career-option-title", career.title || "Career title unavailable"));
    card.appendChild(head);

    const note = element(
      "p",
      "career-evidence-note",
      "The local catalogue does not include sourced work duties for this role. Open the official occupation profile to inspect its details."
    );
    card.appendChild(note);

    const rationale = element("details", "career-why");
    rationale.appendChild(element("summary", "", "Why this appeared"));
    rationale.appendChild(element(
      "p",
      "",
      career.explanation
        ? `${engineExplanation(career)} The ranking uses RIASEC interests and subject preferences; broad confidence ratings are not ranking inputs.`
        : "No personalized engine explanation is available for this role. It was not generated as a personal recommendation."
    ));
    card.appendChild(rationale);

    const status = career.pathway_career
      ? `A supported learning template is available: ${career.pathway_career}. Its skills and requirements are illustrative, not independently validated occupational benchmarks.`
      : "Role-specific readiness has not been assessed; no supported pathway template is linked to this catalogue role.";
    card.appendChild(element("p", "career-pathway-status", status));
    card.appendChild(element(
      "p",
      "career-skill-boundary",
      "Broad self-reported confidence ratings do not establish proficiency or occupational readiness."
    ));
    const activity = element("details", "career-why");
    activity.append(
      element("summary", "", "Try it before choosing"),
      element("p", "", "Open the official profile, choose one listed work activity to investigate, and write down a question about what it involves. This is an exploration exercise, not a proficiency test.")
    );
    card.appendChild(activity);

    const actions = element("div", "career-card-actions");
    if (CAREER_ID.test(String(career.id || ""))) {
      actions.appendChild(link(`/career/${encodeURIComponent(career.id)}`, "Explore this career", "career-action-primary"));
      actions.appendChild(link(
        `/compare?ids=${encodeURIComponent(career.id)}`,
        "Compare",
        "career-action-secondary"
      ));
      actions.appendChild(link(
        `https://www.onetonline.org/link/summary/${encodeURIComponent(career.id)}`,
        "O*NET profile",
        "career-action-text"
      ));
    } else {
      actions.appendChild(element("span", "career-action-unavailable", "Career detail is unavailable"));
    }
    const pathwayQuery = new URLSearchParams();
    if (options.demo) {
      pathwayQuery.set("demo", "1");
      pathwayQuery.set("demo_scenario", "fresh");
    }
    pathwayQuery.set("career", career.title || "");
    actions.appendChild(link(`/reskilling?${pathwayQuery}`, "Review learning pathway options", "career-action-text"));
    card.appendChild(actions);

    if (career.match_index !== undefined) card.appendChild(scoreDetails({ ...career, rank }));
    return card;
  }

  function renderRecommendations(container, recommendations, options = {}) {
    if (!container) return;
    container.replaceChildren();
    if (!Array.isArray(recommendations) || !recommendations.length) {
      container.appendChild(element(
        "p",
        "career-empty-state",
        options.personalized
          ? "No engine recommendations were returned. You can browse the catalogue without treating it as a personalized result."
          : "No personalized recommendations are available here. Browse the catalogue to explore roles."
      ));
      return;
    }

    const ranked = recommendations.map((career, index) => ({
      ...career,
      rank: index + 1,
      total: recommendations.length
    }));
    const primary = ranked.slice(0, options.showAll ? ranked.length : 3);
    primary.forEach((career) => container.appendChild(renderCard(career, career.rank, options)));

    if (!options.showAll && ranked.length > 3) {
      const more = element("details", "career-more-results");
      more.appendChild(element("summary", "", `See all ${ranked.length} engine recommendations`));
      ranked.slice(3).forEach((career) => more.appendChild(renderCard(career, career.rank, options)));
      container.appendChild(more);
    }
  }

  root.FutureSkillCareers = Object.freeze({ renderRecommendations });
})(typeof window !== "undefined" ? window : globalThis);
