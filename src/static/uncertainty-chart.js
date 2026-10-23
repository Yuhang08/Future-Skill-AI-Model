/* Display the real scenario API output; no model arithmetic or sample fixtures. */
(() => {
  "use strict";
  const container = document.getElementById("employmentChart");
  const status = document.getElementById("employmentChartStatus");
  const details = document.querySelector(".year-values");
  let chart, chartTheme, current, runtimeFailed = false, loadTimer;
  const percent = value => `${Number(value).toFixed(2)}%`;

  function fallback(message) {
    container.hidden = true;
    container.setAttribute("aria-busy", "false");
    status.hidden = false;
    status.textContent = message;
    details.open = true;
  }

  function draw() {
    if (!current) return;
    if (!window.echarts) {
      if (runtimeFailed) fallback("The chart could not be loaded. The same model values are available in the year-by-year table below.");
      return;
    }
    try {
      const { points, name } = current;
      container.hidden = false;
      const styles = getComputedStyle(document.documentElement);
      const mode = document.documentElement.dataset.futureTheme;
      if (!chart || chartTheme !== mode) {
        chart?.dispose();
        // Give the runtime the site's subdued axis theme in both appearances.
        chart = window.echarts.init(container, {
          valueAxis: { splitLine: { lineStyle: { color: styles.getPropertyValue("--fs-line").trim() } } },
          timeAxis: { axisLine: { lineStyle: { color: styles.getPropertyValue("--fs-line").trim() } } },
        }, { renderer: "svg" });
        chartTheme = mode;
      }
      const ink = styles.getPropertyValue("--fs-ink-soft").trim();
      const muted = styles.getPropertyValue("--fs-muted").trim();
      // A single series uses one palette color, rather than implying categories.
      const line = document.documentElement.dataset.futureTheme === "dark" ? "#61A9BD" : "#1F74AD";
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      chart.setOption({
        animation: !reducedMotion,
        animationDuration: 250,
        animationDurationUpdate: 200,
        textStyle: { fontFamily: "DM Sans, system-ui, sans-serif", color: ink },
        grid: { containLabel: true },
        legend: { data: [name], selectedMode: false, textStyle: { color: ink } },
        tooltip: {
          trigger: "axis",
          confine: true,
          renderMode: "richText",
          formatter: function (params) {
            const item = Array.isArray(params) ? params[0] : params;
            if (!item || !Array.isArray(item.value)) return "";
            return `${name}\n${new Date(item.value[0]).getUTCFullYear()}: ${percent(item.value[1])}\nIllustrative formula output`;
          },
        },
        xAxis: {
          type: "time",
          min: points[0][0],
          max: points.at(-1)[0],
          minInterval: 365 * 24 * 60 * 60 * 1000,
          maxInterval: 366 * 24 * 60 * 60 * 1000,
          axisLabel: { formatter: "{yyyy}", color: muted, hideOverlap: true, showMinLabel: true, showMaxLabel: true },
          name: "Year",
          nameLocation: "middle",
          nameTextStyle: { color: muted },
        },
        yAxis: {
          type: "value",
          scale: true,
          min: function (extent) { return Math.max(0, Math.floor((extent.min - .1) * 2) / 2); },
          max: function (extent) { return Math.min(100, Math.ceil((extent.max + .1) * 2) / 2); },
          axisLabel: { color: muted, formatter: percent },
        },
        series: [{
          type: "line",
          name,
          data: points,
          smooth: false,
          symbol: "circle",
          symbolSize: 7,
          itemStyle: { color: line },
          lineStyle: { color: line, width: 3 },
          endLabel: {
            show: true, color: ink, distance: -8, align: "right", verticalAlign: "bottom",
            formatter: function (item) { return percent(item.value[1]); },
          },
          labelLayout: { hideOverlap: true },
          emphasis: { focus: "series" },
        }],
        aria: { enabled: true, label: { description:
          `${name}. Illustrative employment-to-population ratio, not a forecast. ` +
          points.map(point => `${new Date(point[0]).getUTCFullYear()}: ${percent(point[1])}`).join("; ") } },
      }, { notMerge: true });
      chart.resize();
      container.setAttribute("aria-busy", "false");
      status.hidden = true;
      status.textContent = "";
    } catch {
      fallback("The chart could not be displayed. Use the year-by-year table below for the complete model output.");
    }
  }

  window.EmploymentScenarioChart = {
    render(series, name) {
      const entries = Object.entries(series || {}).sort((a, b) => Number(a[0]) - Number(b[0]));
      if (!entries.length || entries.some(([year, value]) =>
        !/^\d{4}$/.test(year) || typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 100)) {
        fallback("No valid series is available to chart. Check the simulation response.");
        return;
      }
      current = { name, points: entries.map(([year, value]) => [Date.UTC(Number(year), 0, 1), value]) };
      document.getElementById("chartScenarioName").textContent = name;
      draw();
    },
    setLoading() {
      container.setAttribute("aria-busy", "true");
      status.hidden = false;
      status.textContent = current
        ? "Calculating… The chart and table still show the last completed run."
        : "Calculating the scenario…";
    },
    setError() {
      container.setAttribute("aria-busy", "false");
      status.hidden = false;
      status.textContent = current
        ? "Calculation failed. The chart and table still show the last successful run."
        : "No model output is available. Try running the scenario again.";
    },
  };
  window.addEventListener("futureskill:themechange", draw);
  if (window.ResizeObserver) new ResizeObserver(() => chart?.resize()).observe(container);
  else window.addEventListener("resize", () => chart?.resize());

  // Load a pinned runtime asynchronously; controls and data tables never depend on it.
  const runtime = document.createElement("script");
  runtime.src = "https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js";
  runtime.integrity = "sha384-pPi0zxBAoDu6+JXW/C68UZLvBUUtU+7zonhif43rqj7pxsGyqyqzcian2Rj37Rss";
  runtime.crossOrigin = "anonymous";
  runtime.async = true;
  runtime.addEventListener("load", () => { clearTimeout(loadTimer); runtimeFailed = false; draw(); });
  runtime.addEventListener("error", () => {
    clearTimeout(loadTimer); runtimeFailed = true;
    fallback("The chart library could not be loaded. The complete model values are available in the year-by-year table below.");
  });
  loadTimer = setTimeout(() => {
    runtimeFailed = true;
    fallback("The chart is taking too long to load. You can read the same model values in the year-by-year table below.");
  }, 12000);
  document.head.appendChild(runtime);
})();
