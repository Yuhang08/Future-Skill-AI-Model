/* Compatibility entry point for the homepage language selector.
 * The shared runtime owns translation, persistence and both language controls.
 * Reusing it avoids overwriting FutureSkillI18n or flattening the hero markup.
 */
(() => {
  "use strict";
  function loadSharedRuntime() {
    if (window.FutureSkillI18n || document.querySelector('script[src^="/static/future-i18n.js"]')) return;
    const script = document.createElement("script");
    script.src = "/static/future-i18n.js?v=6";
    script.async = true;
    document.head.appendChild(script);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", loadSharedRuntime, { once: true });
  else loadSharedRuntime();
})();
