import { useEffect, useRef } from "react";
import "./_group.css";
import "./_shared/report-original.css";
import "./_shared/report-original.js";
import { sampleResult } from "./_shared/fixture";

export function Current() {
  const report = useRef<HTMLDivElement>(null);
  useEffect(() => {
    document.documentElement.dataset.futureskillPage = "home";
    document.documentElement.dataset.futureTheme = "light";
    const api = (window as unknown as { FutureSkillReport: { render: (el: HTMLElement, data: unknown, options: unknown) => void } }).FutureSkillReport;
    if (report.current) api.render(report.current, structuredClone(sampleResult), { demo: true });
  }, []);
  return (
    <main style={{ maxWidth: 1180, margin: "0 auto", padding: "24px" }}>
      <p style={{ fontSize: 12, fontWeight: 700 }}>CURRENT DESIGN · ISOLATED SAMPLE · No learner data</p>
      <div ref={report} />
    </main>
  );
}
