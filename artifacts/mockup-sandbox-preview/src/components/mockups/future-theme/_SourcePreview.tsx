import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { Atom, Moon, Sun } from "lucide-react";
import home from "./_source/home.html?raw";
import reskilling from "./_source/reskilling.html?raw";
import trends from "./_source/trends.html?raw";
import uncertainty from "./_source/uncertainty.html?raw";
import sdg from "./_source/sdg.html?raw";
import inventory from "./_source/inventory.html?raw";
import reskillingCss from "./_source/reskilling.css?raw";
import reskillingDevCss from "./_source/reskilling-dev.css?raw";
import reskillingJs from "./_source/reskilling.js?raw";
import fixturesText from "./_source/fixtures.json?raw";
import bridge from "./_bridge.js?raw";
import futureCss from "./_future.css?raw";
import shellCss from "./_shell.css?raw";
import enhance from "./_enhance.js?raw";

type Page = "home" | "reskilling" | "trends" | "uncertainty" | "sdg" | "inventory";
type Mode = "current" | "dark" | "light";
const pages: { id: Page; label: string; route: string }[] = [
  { id: "home", label: "Career assessment", route: "/" },
  { id: "reskilling", label: "Reskilling", route: "/reskilling" },
  { id: "trends", label: "AI trends", route: "/ai-trend" },
  { id: "uncertainty", label: "Uncertainty Lab", route: "/uncertainty" },
  { id: "sdg", label: "SDG connections", route: "/sdg-impact" },
  { id: "inventory", label: "Screen inventory", route: "/__dev/screens" },
];
const sources: Record<Page, string> = { home, reskilling, trends, uncertainty, sdg, inventory };
const fixtures = JSON.parse(fixturesText);
const assets = "/__mockup/images/futureskill/";
const escapeScript = (script: string) => script.replace(/<\/script/gi, "<\\/script");

function documentFor(page: Page, mode: Mode, search: string, channel: string) {
  let source = sources[page]
    .replaceAll("/static/assets/sdg/", `${assets}sdg/`)
    .replaceAll("/favicon.ico", `${assets}favicon.svg`)
    .replaceAll("window.location.search", "window.__previewSearch")
    .replace(/\blocalStorage\b/g, "window.__previewStorage");
  source = source
    .replace(/<link[^>]+href="\/reskill-static\/style\.css[^"]*"[^>]*>/,
      `<style>${reskillingCss}</style>`)
    .replace(/<link[^>]+href="\/reskill-static\/dev\.css[^"]*"[^>]*>/,
      `<style>${reskillingDevCss}</style>`)
    .replace(/<script[^>]+src="\/reskill-static\/app\.js[^"]*"[^>]*><\/script>/,
      `<script defer>document.addEventListener("DOMContentLoaded",()=>{${escapeScript(reskillingJs
        .replaceAll("window.location.search", "window.__previewSearch")
        .replace(/\blocalStorage\b/g, "window.__previewStorage"))}});</script>`);
  const settings = JSON.stringify({ fixtures, channel, mode, search, origin: window.location.origin }).replace(/</g, "\\u003c");
  source = source.replace("<head>", `<head><script>window.__FUTURE_PREVIEW__=${settings};${escapeScript(bridge)}</script>`);
  source = source.replace(/<html([^>]*)>/, `<html$1 data-preview-page="${page}" data-future-theme="${mode}" data-theme="${mode === "current" ? "light" : mode}">`);
  if (mode !== "current") {
    source = source.replace("</head>", `<style>${futureCss}</style></head>`)
      .replace("</body>", `<script>${escapeScript(enhance)}</script></body>`);
  }
  return source;
}

export function SourcePreview({ initialPage = "uncertainty", initialMode = "dark" }: {
  initialPage?: Page; initialMode?: Mode;
}) {
  const [page, setPage] = useState<Page>(initialPage);
  const [search, setSearch] = useState("");
  const [mode, setMode] = useState<Mode>(initialMode);
  const [notice, setNotice] = useState("");
  const frame = useRef<HTMLIFrameElement>(null);
  const channel = useId();
  const current = initialMode === "current";
  // Appearance changes are messaged to the existing document, so entered values
  // and an open SDG drawer survive a light/dark switch.
  const source = useMemo(() => documentFor(page, current ? "current" : mode, search, channel),
    [page, search, channel, current]);
  const sendMode = useCallback(() => {
    if (!current) frame.current?.contentWindow?.postMessage({
      channel, kind: "future-preview-mode", mode,
    }, window.location.origin);
  }, [channel, current, mode]);
  useEffect(sendMode, [sendMode]);
  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      if (event.source !== frame.current?.contentWindow || event.data?.channel !== channel) return;
      if (event.data.kind === "future-preview-theme" && !current &&
          ["dark", "light"].includes(event.data.mode)) {
        setMode(event.data.mode);
      }
      if (event.data.kind === "future-preview-navigate") {
        const url = new URL(event.data.href, window.location.origin);
        const route = url.pathname === "/__dev/demo/open" ? "/reskilling" : url.pathname;
        const match = pages.find(item => item.route === route);
        if (match) {
          setPage(match.id);
          setSearch(url.search);
          setNotice("");
        } else {
          setNotice("This destination is outside the design preview. No data was changed.");
        }
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [channel, current]);
  return (
    <div className="fs-preview" data-mode={mode} data-page={page}>
      <style>{shellCss}</style>
      <header className="fs-preview-bar">
        <div className="fs-preview-brand"><span className="fs-preview-mark"><Atom size={20}/></span><span>FutureSkill AI</span></div>
        <nav className="fs-preview-nav" aria-label="Preview pages">
          {pages.map(item => <button key={item.id} data-active={item.id === page}
            aria-current={item.id === page ? "page" : undefined}
            onClick={() => { setPage(item.id); setSearch(""); setNotice(""); }}>{item.label}</button>)}
        </nav>
        <div className="fs-preview-controls">
          <span className="fs-preview-status">{current ? "Current · source extraction" : "Design preview · sample data · no saves"}</span>
          {!current && <button className="fs-mode-toggle" onClick={() => setMode(mode === "dark" ? "light" : "dark")}
            aria-label={`Switch to ${mode === "dark" ? "light" : "dark"} mode`} title="Toggle appearance">
            {mode === "dark" ? <Sun size={16}/> : <Moon size={16}/>}
            <span>{mode === "dark" ? "Light mode" : "Dark mode"}</span>
          </button>}
        </div>
      </header>
      {notice && <div role="status" style={{ padding: 12 }}>{notice}</div>}
      <div className="fs-preview-stage">
        <iframe ref={frame} className="fs-source-frame" title={`${pages.find(item => item.id === page)?.label} · ${mode} preview`}
          srcDoc={source} onLoad={sendMode}
          sandbox="allow-scripts allow-same-origin allow-forms allow-modals allow-popups"/>
      </div>
    </div>
  );
}
