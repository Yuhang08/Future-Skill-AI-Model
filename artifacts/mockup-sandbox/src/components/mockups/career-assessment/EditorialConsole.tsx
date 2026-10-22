import { useState } from "react";

const stages = [
  { number: "01", title: "RIASEC interests", detail: "24 questions", short: "Interests" },
  { number: "02", title: "Subject preferences", detail: "12 questions", short: "Subjects" },
  { number: "03", title: "Skills self-assessment", detail: "6 questions", short: "Skills" },
];

const features = [
  {
    index: "A",
    title: "RIASEC assessment",
    body: "Explore six occupational interest dimensions, from practical work to creative ideas.",
  },
  {
    index: "B",
    title: "Subject preferences",
    body: "Find the academic fields that hold your attention and curiosity.",
  },
  {
    index: "C",
    title: "Career recommendations",
    body: "See career directions matched to your interests, subjects and current skills.",
  },
];

const sampleQuestions = [
  "Build or repair a simple electronic device.",
  "Use tools to assemble a physical product.",
  "Test or troubleshoot a piece of equipment.",
];

export function EditorialConsole() {
  const [started, setStarted] = useState(false);
  const [stage, setStage] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const answeredCount = Object.keys(answers).length;

  const begin = () => {
    setStarted(true);
    setStage(0);
  };

  return (
    <div className="min-h-screen bg-[#f1efe7] text-[#1b3531] font-['DM_Sans',sans-serif]">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
        * { box-sizing: border-box; }
        .ec-shell { min-height: 100vh; background: #f1efe7; }
        .ec-topbar { height: 78px; display:flex; align-items:center; justify-content:space-between; padding:0 clamp(22px,5vw,76px); border-bottom:1px solid #dcded3; }
        .ec-brand { display:flex; align-items:center; gap:12px; font-size:16px; font-weight:700; letter-spacing:-.5px; }
        .ec-mark { width:34px; height:34px; display:grid; place-items:center; background:#193e37; color:#e7c982; border-radius:50% 50% 50% 7px; font:20px 'DM Serif Display',serif; }
        .ec-brand em { color:#b36345; font-style:normal; }
        .ec-top-meta { display:flex; align-items:center; gap:22px; color:#64746d; font-size:11px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; }
        .ec-live { display:flex; align-items:center; gap:8px; letter-spacing:.4px; text-transform:none; font-size:12px; }
        .ec-live i { width:7px;height:7px;border-radius:50%;background:#9d9c5b;display:block; }
        .ec-layout { max-width:1540px; margin:auto; display:grid; grid-template-columns:230px minmax(0,1fr); padding:0 clamp(18px,4.3vw,68px); }
        .ec-rail { border-right:1px solid #dcded3; padding:46px 26px 34px 0; display:flex; flex-direction:column; min-height:calc(100vh - 78px); }
        .ec-overline { color:#9a654e; font-size:10px; letter-spacing:1.7px; line-height:1.5; font-weight:700; text-transform:uppercase; }
        .ec-rail h2 { font:24px/1.08 'DM Serif Display',serif; margin:13px 0 28px; letter-spacing:-.4px; }
        .ec-stage { position:relative; display:grid; grid-template-columns:31px 1fr; gap:14px; padding:0 0 26px; color:#8b9690; }
        .ec-stage:not(:last-of-type):after { content:""; position:absolute; left:14px; top:31px; width:1px; height:calc(100% - 22px); background:#d1d8ce; }
        .ec-stage.active { color:#193e37; }
        .ec-stage-num { z-index:1; width:29px;height:29px;display:grid;place-items:center;border:1px solid #cbd2c7;border-radius:50%;background:#f1efe7;font-size:10px;font-weight:700; }
        .ec-stage.active .ec-stage-num { background:#193e37; color:#f1e3bd; border-color:#193e37; }
        .ec-stage strong { display:block; font-size:12px; line-height:1.35; margin:1px 0 4px; }
        .ec-stage small { font-size:10px; color:#89938c; }
        .ec-rail-bottom { margin-top:auto; border-top:1px solid #dcded3; padding-top:18px; }
        .ec-rail-bottom p { margin:9px 0 0; color:#76827a; font-size:11px; line-height:1.65; }
        .ec-main { min-width:0; padding:45px 0 36px clamp(26px,5vw,76px); }
        .ec-intro { display:flex; justify-content:space-between; gap:42px; align-items:center; }
        .ec-copy { max-width:735px; }
        .ec-kicker { display:flex; align-items:center; gap:10px; color:#9a654e; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1.7px; }
        .ec-kicker:before { content:""; width:27px; height:1px; background:#b36345; }
        .ec-title { max-width:780px; font:clamp(48px,6.1vw,82px)/.97 'DM Serif Display',Georgia,serif; letter-spacing:-2.9px; margin:21px 0 18px; color:#193e37; }
        .ec-title span { color:#b36345; font-style:italic; }
        .ec-description { max-width:560px; color:#63736c; font-size:14px; line-height:1.8; margin:0; }
        .ec-visual { width:220px; height:220px; flex:0 0 220px; position:relative; display:grid; place-items:center; }
        .ec-visual:before,.ec-visual:after { content:""; position:absolute; inset:12px; border:1px solid #cbd2c3; border-radius:50%; transform:rotate(-24deg) scaleX(.72); }
        .ec-visual:after { inset:32px; transform:rotate(30deg) scaleX(.72); border-color:#d9c99b; }
        .ec-compass { width:110px;height:110px;border:1px solid #c9d1c3; border-radius:50%;display:grid;place-items:center; background:#e6e5d9; color:#193e37;position:relative; }
        .ec-compass:before,.ec-compass:after { content:""; position:absolute; background:#bb7453; }
        .ec-compass:before { width:1px;height:76px; }
        .ec-compass:after { height:1px;width:76px; }
        .ec-compass b { z-index:1; background:#e6e5d9; font:30px 'DM Serif Display',serif; }
        .ec-orbit-label { position:absolute; font-size:9px; font-weight:700; letter-spacing:1px; color:#7f8c7c; }
        .ec-orbit-label.n { top:1px; left:50%; transform:translateX(-50%); }
        .ec-orbit-label.e { right:2px; top:50%; }
        .ec-orbit-label.s { bottom:0; left:50%; transform:translateX(-50%); }
        .ec-orbit-label.w { left:0; top:50%; }
        .ec-lower { display:grid; grid-template-columns:minmax(0,1fr) 294px; gap:36px; margin-top:40px; padding-top:24px; border-top:1px solid #d4d8ce; align-items:start; }
        .ec-section-head { display:flex; align-items:baseline; justify-content:space-between; gap:12px; margin-bottom:11px; }
        .ec-section-head h2 { font:21px 'DM Serif Display',serif; margin:0; color:#193e37; }
        .ec-section-head span { color:#8e9990; font-size:10px; letter-spacing:1.1px; text-transform:uppercase; }
        .ec-feature-list { border-top:1px solid #d4d8ce; }
        .ec-feature { display:grid; grid-template-columns:32px minmax(130px,.76fr) 1fr; align-items:center; gap:12px; padding:14px 0; border-bottom:1px solid #d4d8ce; }
        .ec-feature-index { color:#b36345; font:16px 'DM Serif Display',serif; }
        .ec-feature strong { font-size:12px; }
        .ec-feature p { color:#718079; font-size:11px; line-height:1.55; margin:0; }
        .ec-cta { padding:21px 21px 20px; background:#193e37; color:#f2f0e7; border-radius:3px 28px 3px 3px; position:relative; overflow:hidden; }
        .ec-cta:after { content:""; position:absolute; right:-55px; top:-75px; width:155px; height:155px; border:1px solid #577468; border-radius:50%; box-shadow:0 0 0 18px #193e37,0 0 0 19px #4c6c5f; opacity:.7; }
        .ec-cta-label { position:relative; z-index:1; color:#d4c28d; font-size:9px; font-weight:700; letter-spacing:1.6px; text-transform:uppercase; }
        .ec-cta h3 { position:relative; z-index:1; font:25px/1.08 'DM Serif Display',serif; margin:14px 0 7px; max-width:205px; }
        .ec-cta p { position:relative; z-index:1; margin:0; color:#c0cec5; font-size:11px; line-height:1.6; }
        .ec-button { position:relative; z-index:1; width:100%; margin-top:20px; padding:13px 14px; border:0; border-radius:2px; background:#e3c77d; color:#193e37; font-size:12px; font-weight:700; cursor:pointer; text-align:left; display:flex; justify-content:space-between; align-items:center; }
        .ec-button:hover { background:#efd998; }
        .ec-cta-foot { margin-top:12px!important; color:#91aa9c!important; font-size:9px!important; letter-spacing:.3px; text-align:center; }
        .ec-assessment { max-width:980px; }
        .ec-back { border:0; background:none; padding:0; color:#8f5e49; font-size:11px; font-weight:700; cursor:pointer; margin-bottom:22px; }
        .ec-assessment-heading { display:flex; align-items:flex-end; justify-content:space-between; gap:20px; border-bottom:1px solid #d4d8ce; padding-bottom:18px; }
        .ec-assessment-heading h1 { font:clamp(34px,4vw,54px)/1 'DM Serif Display',serif; letter-spacing:-1px; margin:10px 0 0; }
        .ec-count { color:#75847b; font-size:11px; white-space:nowrap; }
        .ec-progress { height:3px; margin:18px 0 26px; background:#dce0d6; }
        .ec-progress i { display:block; height:100%; background:#b36345; transition:width .3s ease; }
        .ec-question-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:13px; }
        .ec-question { min-height:190px; padding:17px 16px; background:#f8f7f1; border:1px solid #d9ded4; display:flex; flex-direction:column; justify-content:space-between; }
        .ec-question small { color:#a26b51; font-size:10px; letter-spacing:1px; font-weight:700; }
        .ec-question strong { display:block; margin:15px 0; font:19px/1.15 'DM Serif Display',serif; font-weight:400; }
        .ec-rating { display:flex; gap:5px; }
        .ec-rating button { width:34px;height:31px; border:1px solid #d5d9ce; background:transparent; color:#66756c; font-size:11px; cursor:pointer; }
        .ec-rating button.selected { background:#193e37; border-color:#193e37; color:#f5e7c3; }
        .ec-scale { display:flex; justify-content:space-between; color:#89958c; font-size:9px; margin-top:7px; }
        .ec-controls { display:flex; justify-content:space-between; align-items:center; margin-top:22px; }
        .ec-quiet { color:#89958c; font-size:10px; }
        .ec-next { border:0; background:#193e37; color:#f2f0e7; padding:12px 17px; font-size:11px; font-weight:700; cursor:pointer; }
        .ec-next:disabled { opacity:.45; cursor:not-allowed; }
        @media (max-width:900px) {
          .ec-layout { grid-template-columns:185px minmax(0,1fr); }
          .ec-main { padding-left:30px; }
          .ec-visual { width:165px;height:165px;flex-basis:165px; }
          .ec-lower { grid-template-columns:minmax(0,1fr) 250px; gap:20px; }
          .ec-feature { grid-template-columns:25px 1fr; }
          .ec-feature p { grid-column:2; }
        }
        @media (max-width:650px) {
          .ec-topbar { height:64px; padding:0 18px; }
          .ec-top-meta { gap:0; }
          .ec-top-meta > span:first-child { display:none; }
          .ec-layout { display:block; padding:0 18px; }
          .ec-rail { display:none; }
          .ec-main { padding:35px 0 24px; }
          .ec-intro { display:block; }
          .ec-title { font-size:54px; letter-spacing:-1.8px; }
          .ec-visual { display:none; }
          .ec-lower { grid-template-columns:1fr; gap:20px; margin-top:30px; }
          .ec-cta { order:-1; }
          .ec-feature { grid-template-columns:27px minmax(0,1fr); padding:13px 0; }
          .ec-feature p { grid-column:2; }
          .ec-question-grid { grid-template-columns:1fr; }
          .ec-question { min-height:154px; }
          .ec-assessment-heading { align-items:flex-start; flex-direction:column; gap:8px; }
          .ec-assessment-heading h1 { font-size:39px; }
          .ec-controls { gap:12px; }
        }
        @media (prefers-reduced-motion: reduce) { *, *:before, *:after { scroll-behavior:auto!important; transition:none!important; } }
      `}</style>
      <div className="ec-shell">
        <header className="ec-topbar">
          <div className="ec-brand"><span className="ec-mark">✳</span><span>FutureSkill<em>AI</em></span></div>
          <div className="ec-top-meta"><span>Career discovery, made personal</span><span className="ec-live"><i />Ready when you are</span></div>
        </header>

        <div className="ec-layout">
          <aside className="ec-rail">
            <span className="ec-overline">A considered first step</span>
            <h2>Your assessment,<br />at a glance.</h2>
            {stages.map((item, i) => (
              <div className={`ec-stage ${stage === i ? "active" : ""}`} key={item.number}>
                <span className="ec-stage-num">{item.number}</span>
                <div><strong>{item.title}</strong><small>{item.detail}</small></div>
              </div>
            ))}
            <div className="ec-rail-bottom">
              <span className="ec-overline">A little context</span>
              <p>There are no right or wrong answers. Follow what feels genuinely interesting.</p>
            </div>
          </aside>

          <main className="ec-main">
            {!started ? (
              <>
                <section className="ec-intro">
                  <div className="ec-copy">
                    <div className="ec-kicker">A clearer sense of direction</div>
                    <h1 className="ec-title">Discover your<br /><span>future career.</span></h1>
                    <p className="ec-description">Notice what draws you in. Map your strengths. Explore career opportunities that fit the person you are becoming.</p>
                  </div>
                  <div className="ec-visual" aria-hidden="true">
                    <span className="ec-orbit-label n">N</span><span className="ec-orbit-label e">E</span>
                    <span className="ec-orbit-label s">S</span><span className="ec-orbit-label w">W</span>
                    <div className="ec-compass"><b>✳</b></div>
                  </div>
                </section>

                <section className="ec-lower">
                  <div>
                    <div className="ec-section-head"><h2>What you’ll explore</h2><span>One profile · three lenses</span></div>
                    <div className="ec-feature-list">
                      {features.map((feature) => (
                        <article className="ec-feature" key={feature.index}>
                          <span className="ec-feature-index">{feature.index}</span>
                          <strong>{feature.title}</strong>
                          <p>{feature.body}</p>
                        </article>
                      ))}
                    </div>
                  </div>
                  <aside className="ec-cta">
                    <span className="ec-cta-label">42 questions · about 8 minutes</span>
                    <h3>Start with what interests you.</h3>
                    <p>Three short parts bring your interests, subjects and skills into focus.</p>
                    <button className="ec-button" onClick={begin}>Begin your assessment <span>↗</span></button>
                    <p className="ec-cta-foot">Your answers stay yours. Take it at your pace.</p>
                  </aside>
                </section>
              </>
            ) : (
              <section className="ec-assessment">
                <button className="ec-back" onClick={() => setStarted(false)}>← Back to overview</button>
                <div className="ec-assessment-heading">
                  <div><div className="ec-kicker">Part {stage + 1} of 3 · {stages[stage].short}</div><h1>{stage === 0 ? "What feels like you?" : stage === 1 ? "Follow your curiosity." : "What can you do today?"}</h1></div>
                  <span className="ec-count">{answeredCount} answered · 42 total</span>
                </div>
                <div className="ec-progress"><i style={{ width: `${Math.max(7, (answeredCount / 42) * 100)}%` }} /></div>
                <div className="ec-question-grid">
                  {sampleQuestions.map((question, index) => (
                    <article className="ec-question" key={question}>
                      <div><small>QUESTION {String(index + 1).padStart(2, "0")}</small><strong>{question}</strong></div>
                      <div>
                        <div className="ec-rating" aria-label="Rate your interest from 1 to 5">
                          {[1, 2, 3, 4, 5].map((rating) => (
                            <button type="button" key={rating} aria-label={`Rate ${rating}`} className={answers[index] === rating ? "selected" : ""} onClick={() => setAnswers((current) => ({ ...current, [index]: rating }))}>{rating}</button>
                          ))}
                        </div>
                        <div className="ec-scale"><span>Strongly dislike</span><span>Strongly like</span></div>
                      </div>
                    </article>
                  ))}
                </div>
                <div className="ec-controls">
                  <span className="ec-quiet">Your instinct is enough. Choose what feels true.</span>
                  <button className="ec-next" disabled={answeredCount < 3} onClick={() => { setStage((current) => (current + 1) % 3); setAnswers({}); }}>
                    {stage === 2 ? "See your direction" : "Continue"} →
                  </button>
                </div>
              </section>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
