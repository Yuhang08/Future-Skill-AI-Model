import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent, ReactNode } from "react";
import "./_group.css";
import "./_shared/report-original.css";
import "./_shared/report-original.js";
import "./_workspace.css";

type Section = "overview" | "interests" | "subjects" | "confidence" | "careers";
type Pattern = "equal-high" | "equal-low" | "differentiated" | "leading-tie" | "mixed";
type ResultData = {
  top3: string;
  riasec_scores: Record<string, number>;
  subject_preferences: Record<string, number>;
  skills: Record<string, number>;
  recommendations: unknown[];
};
type ReportModel = {
  valid: boolean;
  error?: string;
  data?: ResultData;
  ordered: { key: string; name: string; score: number }[];
  interestSummary: string;
  subjectSummary: string;
  confidenceSummary: string;
  allInterestsEqual: boolean;
  allSubjectsEqual: boolean;
  allSkillsEqual: boolean;
  hasInterestTies: boolean;
  leadingInterests: string[];
  interestTieGroups: { score: number; areas: string[] }[];
  cutoffAreas: string[];
  cutoffScore: number;
  subjectLeaders: string[];
  highestConfidenceSkills: string[];
  lowestConfidenceSkills: string[];
  maxConfidence: number;
  minConfidence: number;
  combinedAreas: { key: string; name: string; score: number }[];
};
type ReportApi = { buildModel: (data: ResultData) => ReportModel };

const ORDER = ["R", "I", "A", "S", "E", "C"];
const INTERESTS = [
  { key: "R", title: "Realistic", activity: "Build, repair, or work with tools and materials.", meaning: "Hands-on activities with equipment, materials, and the outdoors.", question: "Would you like to try a small repair, build, or outdoor project?" },
  { key: "I", title: "Investigative", activity: "Research questions and understand how things work.", meaning: "Investigating questions, studying systems, and researching evidence.", question: "What question could you explore through observation, reading, or a small experiment?" },
  { key: "A", title: "Artistic", activity: "Make original art, design, writing, or music.", meaning: "Creating original work and expressing ideas through different media.", question: "What would you enjoy making if you could choose the format and audience?" },
  { key: "S", title: "Social", activity: "Help, teach, advise, or support other people.", meaning: "Activities centered on helping, teaching, advising, or providing a service.", question: "Who might benefit from something you could explain, teach, or help with?" },
  { key: "E", title: "Enterprising", activity: "Organize ideas, lead projects, or persuade.", meaning: "Coordinating with others, leading initiatives, marketing, or negotiation.", question: "What idea or small project would you like to organize people around?" },
  { key: "C", title: "Conventional", activity: "Organize information and follow useful systems.", meaning: "Organizing information, maintaining records, and following procedures.", question: "What information could you organize into a clear, useful system?" },
];
const SUBJECTS = [
  { key: "IT", title: "Computing & technology", note: "Software, digital tools, and computing systems.", question: "What everyday task could a small digital tool make easier?", icon: "computer" },
  { key: "Math", title: "Mathematics & statistics", note: "Reasoning with numbers, measurement, and patterns in data.", question: "What real-world question could you explore with a small dataset?", icon: "calculator" },
  { key: "Education", title: "Teaching & learning", note: "How people learn and how ideas are explained.", question: "What could you explain in a way a younger learner might understand?", icon: "learn" },
  { key: "Health", title: "Health & medicine", note: "Human health, medicine, care, and related research.", question: "Which question about health would you like to learn more about?", icon: "health" },
  { key: "Business", title: "Business & enterprise", note: "How organizations plan, serve people, and manage resources.", question: "What community need could a simple service help address?", icon: "briefcase" },
  { key: "Engineering", title: "Engineering & design", note: "Applying science and design to improve practical systems.", question: "What everyday object or process would you redesign?", icon: "design" },
];
const SKILLS = [
  { key: "MathSkill", title: "Mathematical & logical problem-solving", practice: "Work through a puzzle and explain how you reached an answer.", icon: "logic" },
  { key: "CodingSkill", title: "Coding & debugging", practice: "Build a tiny program or trace and fix a simple bug.", icon: "code" },
  { key: "DataSkill", title: "Data analysis", practice: "Use a small public dataset to describe one pattern.", icon: "data" },
  { key: "CommunicationSkill", title: "Communication", practice: "Explain an idea and ask someone what was clear.", icon: "chat" },
  { key: "LeadershipSkill", title: "Planning & team coordination", practice: "Plan a small shared task, then reflect on the coordination.", icon: "team" },
  { key: "CreativeSkill", title: "Creative problem-solving", practice: "Generate a few approaches to one everyday challenge.", icon: "creative" },
];
const SECTION_LABELS: { id: Section; label: string; icon: string }[] = [
  { id: "overview", label: "Overview", icon: "grid" },
  { id: "interests", label: "Interests", icon: "spark" },
  { id: "subjects", label: "Subjects", icon: "book" },
  { id: "confidence", label: "Confidence", icon: "steps" },
  { id: "careers", label: "Careers", icon: "path" },
];

const patterns: Record<Pattern, Omit<ResultData, "top3">> = {
  "equal-high": {
    riasec_scores: { R: 100, I: 100, A: 100, S: 100, E: 100, C: 100 },
    subject_preferences: { IT: 5, Math: 5, Education: 5, Health: 5, Business: 5, Engineering: 5 },
    skills: { MathSkill: 5, CodingSkill: 5, DataSkill: 5, CommunicationSkill: 5, LeadershipSkill: 5, CreativeSkill: 5 },
    recommendations: [],
  },
  "equal-low": {
    riasec_scores: { R: 20, I: 20, A: 20, S: 20, E: 20, C: 20 },
    subject_preferences: { IT: 1, Math: 1, Education: 1, Health: 1, Business: 1, Engineering: 1 },
    skills: { MathSkill: 1, CodingSkill: 1, DataSkill: 1, CommunicationSkill: 1, LeadershipSkill: 1, CreativeSkill: 1 },
    recommendations: [],
  },
  differentiated: {
    riasec_scores: { R: 85, I: 95, A: 65, S: 75, E: 45, C: 55 },
    subject_preferences: { IT: 4, Math: 5, Education: 3, Health: 2, Business: 3, Engineering: 4 },
    skills: { MathSkill: 3, CodingSkill: 2, DataSkill: 4, CommunicationSkill: 4, LeadershipSkill: 3, CreativeSkill: 5 },
    recommendations: [],
  },
  "leading-tie": {
    riasec_scores: { R: 85, I: 95, A: 95, S: 75, E: 45, C: 55 },
    subject_preferences: { IT: 4, Math: 4, Education: 3, Health: 2, Business: 3, Engineering: 5 },
    skills: { MathSkill: 4, CodingSkill: 3, DataSkill: 4, CommunicationSkill: 3, LeadershipSkill: 2, CreativeSkill: 5 },
    recommendations: [],
  },
  mixed: {
    riasec_scores: { R: 75, I: 55, A: 95, S: 95, E: 40, C: 70 },
    subject_preferences: { IT: 3, Math: 2, Education: 5, Health: 4, Business: 2, Engineering: 3 },
    skills: { MathSkill: 2, CodingSkill: 3, DataSkill: 2, CommunicationSkill: 5, LeadershipSkill: 4, CreativeSkill: 4 },
    recommendations: [],
  },
};

function Icon({ name }: { name: string }) {
  const common = { viewBox: "0 0 24 24", "aria-hidden": true as const };
  const paths: Record<string, ReactNode> = {
    grid: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/></>,
    spark: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z"/><path d="m19 16 .8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z"/></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21V5.5Z"/><path d="M4 17a2.5 2.5 0 0 1 2.5-2.5H20M8 7h8"/></>,
    steps: <><path d="M4 19.5h16"/><path d="M6.5 16V11m5 5V5m5 11v-7"/></>,
    path: <><circle cx="6" cy="18" r="2"/><circle cx="18" cy="6" r="2"/><path d="M8 18h4a4 4 0 0 0 4-4V8"/></>,
    gear: <><circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.1.9-1.5 2.6-1.4-.5a7.8 7.8 0 0 1-1.5.9l-.3 1.5h-3l-.3-1.5a7.8 7.8 0 0 1-1.5-.9l-1.4.5-1.5-2.6 1.1-.9a7.5 7.5 0 0 1 0-1.8l-1.1-.9 1.5-2.6 1.4.5a7.8 7.8 0 0 1 1.5-.9l.3-1.5h3l.3 1.5a7.8 7.8 0 0 1 1.5.9l1.4-.5 1.5 2.6-1.1.9a7.5 7.5 0 0 1 0 1.8Z"/></>,
    info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v5m0-8h.01"/></>,
    compass: <><circle cx="12" cy="12" r="9"/><path d="m15.8 8.2-2.2 5.4-5.4 2.2 2.2-5.4 5.4-2.2Z"/></>,
    computer: <><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8m-4-4v4"/></>,
    calculator: <><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2m4 0h2m-8 4h2m4 0h2m-8 3h2m4 0h2"/></>,
    learn: <><path d="m3 8 9-5 9 5-9 5-9-5Z"/><path d="M7 11v5c3 3 7 3 10 0v-5m4-3v7"/></>,
    health: <><path d="M12 21s-8-4.5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 6.5-8 11-8 11Z"/><path d="M8 12h2l1-2 2 4 1-2h2"/></>,
    briefcase: <><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m-13 5h18m-11 0v2h4v-2"/></>,
    design: <><path d="m4 16 9-9 4 4-9 9H4v-4Zm7-7 4 4m2-9 1-2m3 5 2-1M5 5l2 2"/></>,
    logic: <><path d="M4 5h6v6H4zM14 13h6v6h-6z"/><path d="M10 8h4a2 2 0 0 1 2 2v3m-6-2v2a2 2 0 0 1-2 2H6"/></>,
    code: <><path d="m8 8-4 4 4 4m8-8 4 4-4 4m-2-11-4 14"/></>,
    data: <><path d="M4 19V5m0 14h17"/><path d="m7 15 4-4 3 2 5-6"/></>,
    chat: <><path d="M4 5h16v12H9l-5 4V5Z"/><path d="M8 9h8m-8 4h5"/></>,
    team: <><circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 20v-2a6 6 0 0 1 12 0v2m1-5a4 4 0 0 1 5 4v1"/></>,
    creative: <><path d="M12 3a8 8 0 0 0-4.5 14.6c.8.5 1.2 1.2 1.2 2.4h6.6c0-1.2.4-1.9 1.2-2.4A8 8 0 0 0 12 3Z"/><path d="M9 20h6m-5-7 2-4 2 4"/></>,
  };
  return <svg {...common}>{paths[name] ?? paths.info}</svg>;
}

function makeData(pattern: Pattern): ResultData {
  const values = patterns[pattern];
  const top3 = [...ORDER].sort((a, b) => values.riasec_scores[b] - values.riasec_scores[a] || ORDER.indexOf(a) - ORDER.indexOf(b)).slice(0, 3).join("");
  return { ...structuredClone(values), top3 };
}

export function Workspace() {
  const [section, setSection] = useState<Section>("overview");
  const [pattern, setPattern] = useState<Pattern>("equal-high");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const data = useMemo(() => makeData(pattern), [pattern]);
  const model = useMemo(() => {
    const api = (window as Window & { FutureSkillReport?: ReportApi }).FutureSkillReport;
    return api?.buildModel(data) ?? null;
  }, [data]);
  const navRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const settingsDialogRef = useRef<HTMLDialogElement>(null);
  const settingsTriggerRef = useRef<HTMLElement | null>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    document.documentElement.dataset.futureskillPage = "home";
    document.documentElement.dataset.futureTheme = theme;
  }, [theme]);

  useEffect(() => {
    const dialog = settingsDialogRef.current;
    if (!settingsOpen || !dialog || dialog.open) return;
    const restoreFocus = () => {
      setSettingsOpen(false);
      settingsTriggerRef.current?.focus();
    };
    dialog.addEventListener("close", restoreFocus);
    dialog.showModal();
    return () => dialog.removeEventListener("close", restoreFocus);
  }, [settingsOpen]);

  function changeSection(id: Section, focus = false) {
    setSection(id);
    if (focus) requestAnimationFrame(() => navRefs.current[SECTION_LABELS.findIndex(item => item.id === id)]?.focus());
  }

  function handleNavKey(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let next = index;
    if (event.key === "ArrowDown" || event.key === "ArrowRight") next = (index + 1) % SECTION_LABELS.length;
    else if (event.key === "ArrowUp" || event.key === "ArrowLeft") next = (index - 1 + SECTION_LABELS.length) % SECTION_LABELS.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = SECTION_LABELS.length - 1;
    else return;
    event.preventDefault();
    changeSection(SECTION_LABELS[next].id, true);
  }

  if (!model) {
    return <main className="results-workspace"><p role="alert">The report model is unavailable in this preview.</p></main>;
  }
  if (!model.valid) {
    return <main className="results-workspace"><div className="rw-main"><div className="rw-info-banner" role="alert"><Icon name="info"/><span>We could not prepare this sample report. {model.error}</span></div></div></main>;
  }

  const labelPattern: Record<Pattern, string> = {
    "equal-high": "Equal high",
    "equal-low": "Equal low",
    differentiated: "Differentiated",
    "leading-tie": "Leading tie",
    mixed: "Mixed",
  };
  const interestSummary = model.allInterestsEqual
    ? `Your answers do not identify a clear leading interest area. All six interest scores are ${data.riasec_scores.R} / 100.`
    : model.interestSummary;

  function scaleMarkers(value: number, label: string) {
    return <div className="rw-scale-markers" role="meter" aria-label={label} aria-valuemin={1} aria-valuemax={5} aria-valuenow={value}>
      {[1, 2, 3, 4, 5].map(mark => <span key={mark} className={`rw-scale-mark${mark <= value ? " is-filled" : ""}`} />)}
    </div>;
  }

  function miniMetrics(items: { label: string; value: number; min: number; max: number; name: string }[]) {
    return <div className="rw-mini-metrics">
      {items.map(item => <div className="rw-mini-metric" key={item.label}>
        <span aria-hidden="true">{item.label}</span>
        <span className="rw-mini-track" role="meter" aria-label={`${item.name}, ${item.value} on a ${item.min} to ${item.max} scale`} aria-valuemin={item.min} aria-valuemax={item.max} aria-valuenow={item.value}>
          <span className="rw-mini-fill" style={{ width: `${((item.value - item.min) / (item.max - item.min)) * 100}%` }}/>
        </span>
        <strong>{item.value}</strong>
      </div>)}
    </div>;
  }

  return (
    <div className="results-workspace">
      <header className="rw-global-nav">
        <a className="rw-brand" href="/" aria-label="FutureSkill home">
          <span className="rw-brand-mark"><Icon name="spark"/></span><span>FutureSkill</span>
        </a>
        <div className="rw-global-right">
          <span className="rw-nav-context">Career exploration</span>
          <button type="button" className="rw-settings" onClick={event => { settingsTriggerRef.current = event.currentTarget; setSettingsOpen(true); }} aria-label="Open settings">
            <Icon name="gear"/><span>Settings</span>
          </button>
        </div>
      </header>

      <div className="rw-layout">
        <aside className="rw-sidebar" aria-label="Your workspace">
          <p className="rw-side-title">YOUR WORKSPACE</p>
          <p className="rw-side-copy">A clearer view<br/>of what you enjoy.</p>
          <nav className="rw-side-nav" role="tablist" aria-label="Results sections" aria-orientation="vertical">
            {SECTION_LABELS.map((item, index) => (
              <button
                key={item.id}
                ref={element => { navRefs.current[index] = element; }}
                className="rw-nav-item"
                type="button"
                role="tab"
                id={`rw-tab-${item.id}`}
                aria-selected={section === item.id}
                aria-controls="rw-current-panel"
                tabIndex={section === item.id ? 0 : -1}
                onClick={() => changeSection(item.id)}
                onKeyDown={event => handleNavKey(event, index)}
              >
                <span className="rw-nav-icon"><Icon name={item.icon}/></span><span>{item.label}</span>
              </button>
            ))}
          </nav>
          <div className="rw-sidebar-note"><span className="rw-note-dot"/><strong>Curiosity is a good start.</strong><br/>Your results are prompts to explore, never a label.</div>
        </aside>

        <main className="rw-main">
          <div className="rw-main-inner">
            <div className="rw-toolbar">
              <span className="rw-preview-tag">DESIGN PREVIEW · SAMPLE DATA</span>
              <label className="rw-sample-control">Sample pattern
                <select aria-label="Choose a sample pattern" value={pattern} onChange={event => setPattern(event.target.value as Pattern)}>
                  {(Object.keys(labelPattern) as Pattern[]).map(key => <option key={key} value={key}>{labelPattern[key]}</option>)}
                </select>
              </label>
            </div>

            <section
              key={section}
              className="rw-content"
              id="rw-current-panel"
              role="tabpanel"
              aria-labelledby={`rw-tab-${section}`}
              tabIndex={0}
            >
              {section === "overview" && (
                <>
                  <div className="rw-heading-row">
                    <div><p className="rw-kicker">Your workspace / overview</p><h1>Your results at a glance</h1><p>Three separate views of what you reported. Use them as starting points for reflection—not a test of ability or a prediction of work.</p></div>
                  </div>
                  <section className="rw-surface rw-glance" aria-labelledby="rw-glance-title">
                    <div className="rw-glance-heading">
                      <p className="rw-kicker">A guide for reflection</p>
                      <h2 id="rw-glance-title">A few clues, not a fixed path.</h2>
                      <p>Interests are what you enjoy, subjects are topics you like, and confidence is how capable you currently feel. Each offers a different kind of clue.</p>
                    </div>
                    <div className="rw-glance-grid">
                      <article className="rw-glance-card">
                        <div className="rw-glance-top"><span className="rw-glance-icon"><Icon name="spark"/></span>Interests · enjoy doing</div>
                        <p>{interestSummary}</p>
                        {miniMetrics(INTERESTS.map(item => ({ label: item.key, value: data.riasec_scores[item.key], min: 20, max: 100, name: `${item.title} interest score` })))}
                      </article>
                      <article className="rw-glance-card">
                        <div className="rw-glance-top"><span className="rw-glance-icon"><Icon name="book"/></span>Subjects · enjoy learning</div>
                        <p>{model.subjectSummary} These ratings show enjoyment, not subject ability.</p>
                        {miniMetrics(SUBJECTS.map((item, index) => ({ label: ["IT", "MA", "ED", "HE", "BU", "EN"][index], value: data.subject_preferences[item.key], min: 1, max: 5, name: `${item.title} enjoyment` })))}
                      </article>
                      <article className="rw-glance-card">
                        <div className="rw-glance-top"><span className="rw-glance-icon"><Icon name="steps"/></span>Confidence · how you feel</div>
                        <p>{model.confidenceSummary} These are self-reported feelings, not verified proficiency.</p>
                        {miniMetrics(SKILLS.map((item, index) => ({ label: ["LOG", "COD", "DAT", "COM", "TEAM", "IDEA"][index], value: data.skills[item.key], min: 1, max: 5, name: `${item.title} confidence` })))}
                      </article>
                    </div>
                  </section>
                  <div className="rw-surface rw-next-strip">
                    <div><strong>Want to explore a little more?</strong><p>Choose one of these views to see the scores, scale, and a small reflection prompt.</p></div>
                    <button type="button" className="rw-next-link" onClick={() => changeSection("interests")}>Explore interests <span aria-hidden="true">→</span></button>
                  </div>
                  <div className="rw-section-foot"><strong>Keep the distinction:</strong> interest and subject enjoyment contribute to career ranking (65% interest, 35% subject). Confidence does not. The three-letter interest code is not used for ranking.</div>
                </>
              )}

              {section === "interests" && (
                <>
                  <div className="rw-heading-row">
                    <div><p className="rw-kicker">Your workspace / interests</p><h1>What kinds of activities appeal?</h1><p>These are reported interests on the original 20–100 score scale. The bars are horizontal and start at 20, the minimum possible score.</p></div>
                  </div>
                  <div className="rw-code-wrap">
                    <span className="rw-code-label">Calculated interest code</span>
                    <strong className="rw-code" aria-label={`Interest code ${data.top3}`}>{data.top3}</strong>
                    <span className="rw-code-caption">A compact shorthand for the three highest calculated scores.</span>
                  </div>
                  <div className="rw-interest-signal"><strong>{interestSummary}</strong></div>
                  <div className="rw-info-banner"><span className="rw-info-icon"><Icon name="info"/></span><span>Scores are not percentiles, probabilities of career success, or personality percentages. Each bar spans the possible 20–100 score range; 20 is not an absence of interest.</span></div>
                  {model.hasInterestTies && <div className="rw-info-banner"><span className="rw-info-icon"><Icon name="info"/></span><span><strong>Code tie order:</strong> equal scores follow fixed R–I–A–S–E–C ordering. A letter's position in a tie does not establish a primary, secondary, or tertiary strength.</span></div>}
                  <details className="rw-read-more"><summary>About the framework and questionnaire</summary><div className="rw-read-more-body"><p>General activity descriptions are adapted from O*NET. This FutureSkill questionnaire is custom—not the official O*NET Interest Profiler—and does not inherit its validation, norms, or reliability.</p><p><a href="https://www.onetcenter.org/IP.html" target="_blank" rel="noreferrer">About the official instrument</a></p></div></details>
                  {model.interestTieGroups.some(group => group.areas.length > 1) && !model.allInterestsEqual && (
                    <details className="rw-read-more"><summary>See how tied scores are handled</summary><div className="rw-read-more-body"><p>{model.interestTieGroups.filter(group => group.areas.length > 1).map(group => `${group.areas.join(", ")} share a score of ${group.score}`).join("; ")}. No tie is ordered as a stronger or weaker personal quality.</p>{model.cutoffAreas.length > 1 && <p>There is also a tie at the three-area code cutoff: {model.cutoffAreas.join(", ")} share {model.cutoffScore}. Code is not used in recommendation ranking.</p>}</div></details>
                  )}
                  <p className="rw-source-caption">General activity descriptions adapted from <a href="https://www.onetonline.org/find/descriptor/browse/1.B.1" target="_blank" rel="noreferrer">O*NET interest-type descriptions</a>.</p>
                  <div className="rw-interest-grid" style={{ marginTop: 15 }}>
                    {model.ordered.map(item => {
                      const entry = INTERESTS.find(interest => interest.key === item.key)!;
                      const fill = ((item.score - 20) / 80) * 100;
                      return <article className="rw-interest-card" key={item.key}>
                        <div className="rw-interest-head"><span className="rw-letter">{item.key}</span><span className="rw-interest-name">{entry.title}</span></div>
                        <p className="rw-interest-activity">{entry.activity}</p>
                        <div className="rw-meter-label"><span>Interest score</span><strong>{item.score} / 100</strong></div>
                        <div className="rw-track" role="meter" aria-label={`${entry.title} interest score`} aria-valuemin={20} aria-valuemax={100} aria-valuenow={item.score}><span className="rw-fill" style={{ width: `${fill}%` }}/></div>
                        <details className="rw-card-details">
                          <summary>Explore this area</summary>
                          <p>{entry.meaning}</p><p><strong>Try asking:</strong> {entry.question}</p>
                        </details>
                      </article>;
                    })}
                  </div>
                  {model.combinedAreas.length >= 2 && <div className="rw-section-foot">A possible combination to explore: {model.combinedAreas.map(item => item.name).join(" and ")}. Consider the reflection questions inside those cards together. This is a prompt, not a role recommendation.</div>}
                  <details className="rw-read-more"><summary>How the scores and code are calculated</summary><div className="rw-read-more-body"><p>Each score uses the existing 20–100 scale: four answers summed, divided by 20, then multiplied by 100. The code shows the three highest calculated scores. It is a shorthand for these responses, not a fixed personal identity.</p><p>No close-score threshold or statistical significance is inferred. Ties are disclosed rather than converted into primary, secondary, or tertiary strengths.</p></div></details>
                </>
              )}

              {section === "subjects" && (
                <>
                  <div className="rw-heading-row">
                    <div><p className="rw-kicker">Your workspace / subjects</p><h1>Topics you enjoy exploring</h1><p>These are your subject-enjoyment ratings on a 1–5 scale. A high rating suggests interest in the topic—not demonstrated ability.</p></div>
                  </div>
                  {model.allSubjectsEqual && <div className="rw-info-banner"><span className="rw-info-icon"><Icon name="info"/></span><span><strong>Your subject ratings are equal.</strong> None is distinguished in this sample. That is a perfectly useful starting point for exploration.</span></div>}
                  <div className="rw-grid-two">
                    {SUBJECTS.map(subject => {
                      const value = data.subject_preferences[subject.key];
                      return <article className="rw-scale-card" key={subject.key}>
                        <span className="rw-activity-icon" role="img" aria-label={`${subject.title} activity icon`}><Icon name={subject.icon}/></span>
                        <div className="rw-scale-head"><h2 className="rw-scale-name">{subject.title}</h2><span className="rw-scale-value">{value} / 5</span></div>
                        {scaleMarkers(value, `${subject.title} enjoyment, ${value} out of 5`)}
                        <div className="rw-scale-labels"><span>Not much</span><span>A lot</span></div>
                        <p className="rw-scale-note">{subject.note}</p>
                        <details className="rw-mini-disclosure"><summary>A small thing to wonder</summary><p>{subject.question}</p></details>
                      </article>;
                    })}
                  </div>
                  <div className="rw-section-foot"><strong>Enjoyment is its own clue.</strong> These ratings do not demonstrate skill or subject ability. Meaning and questions are FutureSkill reflection prompts, not validated ability interpretations.</div>
                </>
              )}

              {section === "confidence" && (
                <>
                  <div className="rw-heading-row">
                    <div><p className="rw-kicker">Your workspace / confidence</p><h1>How confident do you feel today?</h1><p>These are self-reported feelings about broad skills—not a scorecard of what you can or cannot do.</p></div>
                  </div>
                  {model.allSkillsEqual && <div className="rw-info-banner"><span className="rw-info-icon"><Icon name="info"/></span><span>Every skill has the same confidence rating in this sample. There is no ranking hidden in these results.</span></div>}
                  <div className="rw-info-banner"><span className="rw-info-icon"><Icon name="info"/></span><span><strong>Confidence is not verified competence.</strong> A lower rating alone is not a weakness. These ratings are not ranking inputs and do not establish occupational readiness.</span></div>
                  <div className="rw-grid-two">
                    {SKILLS.map(skill => {
                      const value = data.skills[skill.key];
                      return <article className="rw-scale-card" key={skill.key}>
                        <span className="rw-activity-icon" role="img" aria-label={`${skill.title} activity icon`}><Icon name={skill.icon}/></span>
                        <div className="rw-scale-head"><h2 className="rw-scale-name">{skill.title}</h2><span className="rw-scale-value">{value} / 5</span></div>
                        {scaleMarkers(value, `${skill.title} reported confidence, ${value} out of 5`)}
                        <div className="rw-scale-labels"><span>Less confident</span><span>More confident</span></div>
                        <details className="rw-mini-disclosure"><summary>One way to practice</summary><p>{skill.practice} This is an idea to gather experience, not a test or proof of proficiency.</p></details>
                      </article>;
                    })}
                  </div>
                  <div className="rw-section-foot"><strong>Practice can help you gather examples.</strong> It does not verify proficiency without an assessment and rubric. These broad ratings are separate from role-specific requirements and do not affect career rankings.</div>
                </>
              )}

              {section === "careers" && (
                <>
                  <div className="rw-heading-row">
                    <div><p className="rw-kicker">Your workspace / careers</p><h1>Career exploration comes next</h1><p>Recommendations are most useful as invitations to investigate—not as predictions or verdicts.</p></div>
                  </div>
                  <section className="rw-surface rw-career-empty">
                    <div className="rw-empty-symbol"><Icon name="compass"/></div>
                    <h3>Real recommendations appear after completing the assessment.</h3>
                    <p>This design preview contains sample answers only and has no career results. We have not filled the space with invented examples.</p>
                    <div className="rw-preview-message"><span className="rw-glance-icon"><Icon name="info"/></span><div><strong>Answer review is preview-only</strong><p>Reviewing responses and viewing saved results are not available in this isolated sample. No learner answers are stored or changed here.</p></div></div>
                  </section>
                  <details className="rw-read-more"><summary>How to read future recommendations</summary><div className="rw-read-more-body"><p>FutureSkill’s recommendation engine uses a 65% interest index and 35% subject index. The three-letter interest code is not an input to ranking. Confidence ratings are not ranking inputs. Recommendations are exploratory, not probabilities or evidence of occupational fit.</p><p>The custom questionnaire is not the official O*NET Interest Profiler and does not inherit its validation, norms, or reliability.</p><ul><li><a href="https://www.onetonline.org/find/descriptor/browse/1.B.1" target="_blank" rel="noreferrer">O*NET career interest types</a></li><li><a href="https://www.onetcenter.org/IP.html" target="_blank" rel="noreferrer">About the official O*NET Interest Profiler</a></li></ul></div></details>
                </>
              )}
            </section>
            <footer className="rw-footer">FutureSkill · Design preview · Sample answers only · No learner data is read, saved, or sent.</footer>
          </div>
        </main>
      </div>
      {settingsOpen && (
        <dialog ref={settingsDialogRef} className="rw-settings-dialog" aria-labelledby="rw-settings-title">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
            <div><p className="rw-kicker">Workspace preferences</p><h2 id="rw-settings-title" style={{ margin: 0, fontSize: 22 }}>Settings</h2></div>
            <button type="button" className="rw-settings-close" aria-label="Close settings" onClick={() => settingsDialogRef.current?.close()}>×</button>
          </div>
          <p style={{ fontSize: 12 }}>Choose a theme for this design preview. This preference is temporary and is not saved.</p>
          <div style={{ display: "flex", gap: 8 }}>
            {(["light", "dark"] as const).map(value => <button key={value} type="button" className="rw-settings-option" aria-pressed={theme === value} onClick={() => setTheme(value)}>{value} theme</button>)}
          </div>
          <p role="status" aria-live="polite" style={{ fontSize: 11, minHeight: 18 }}>{notice}</p>
          <button type="button" onClick={() => { setNotice("This prototype uses isolated sample data only."); window.setTimeout(() => setNotice(""), 2500); }} style={{ background: "var(--fs-mint)", color: "var(--fs-on-accent)" }}>About this preview</button>
        </dialog>
      )}
    </div>
  );
}
