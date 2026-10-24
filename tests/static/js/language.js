/* FutureSkill AI trilingual UI module: requires explicit integration in website templates.
   HTML example: <span data-i18n="discover_title">Discover Your Future Career</span>
   Settings control: <select id="language-select" aria-label="Language">
     <option value="en">English</option><option value="zh">简体中文</option>
     <option value="ms">Bahasa Melayu</option></select>
   Add <script src="{{ url_for('static', filename='js/language.js') }}" defer></script>
*/
(() => {
  "use strict";
  const supported = ["en", "zh", "ms"];
  const key = "futureskill_language";
  let dictionary = {};
  const getLang = () => supported.includes(localStorage.getItem(key))
    ? localStorage.getItem(key) : "en";
  let lang = getLang();
  function translate(k, fallback = k) {
    return Object.prototype.hasOwnProperty.call(dictionary, k)
      ? dictionary[k] : fallback;
  }
  async function setLanguage(requested) {
    if (!supported.includes(requested)) throw new Error("Unsupported language");
    const response = await fetch("/static/i18n/" + requested + ".json", {cache:"no-cache"});
    if (!response.ok) throw new Error("Could not load " + requested + " translations");
    const next = await response.json();
    dictionary = next;
    lang = requested;
    localStorage.setItem(key, lang);
    document.documentElement.lang = lang === "zh" ? "zh-CN" : lang;
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const k = el.getAttribute("data-i18n");
      if (Object.prototype.hasOwnProperty.call(next, k)) el.textContent = next[k];
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      const k = el.getAttribute("data-i18n-placeholder");
      if (Object.prototype.hasOwnProperty.call(next, k)) el.setAttribute("placeholder", next[k]);
    });
    document.querySelectorAll("[data-i18n-title]").forEach(el => {
      const k = el.getAttribute("data-i18n-title");
      if (Object.prototype.hasOwnProperty.call(next, k)) el.setAttribute("title", next[k]);
    });
    const select = document.getElementById("language-select");
    if (select) select.value = lang;
    document.dispatchEvent(new CustomEvent("futureskill:languagechange", {detail:{lang}}));
  }
  window.FutureSkillI18n = {setLanguage, t:translate, getLanguage:()=>lang};
  document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("language-select");
    if (select) select.addEventListener("change", e => setLanguage(e.target.value).catch(console.error));
    setLanguage(lang).catch(console.error);
  });
})();