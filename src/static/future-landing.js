/* Decorative, local Canvas2D artwork. The assessment has its own controller. */
(() => {
  "use strict";

  const canvas = document.getElementById("futureGlobe");
  if (!canvas || typeof window.requestAnimationFrame !== "function") return;
  let context;
  try { context = canvas.getContext("2d", { alpha: true }); } catch { return; }
  if (!context) return;

  const container = canvas.closest(".future-visual") || canvas.parentElement;
  if (!container) return;
  const homepage = document.getElementById("homePage");
  const motionPreference = typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  const latitudeCount = 17;
  const longitudeCount = 36;
  const pointCount = latitudeCount * longitudeCount;
  const points = new Float32Array(pointCount * 3);
  const projected = new Float32Array(pointCount * 3);
  const edgeIndices = [];
  const meshBuckets = Array.from({ length: 7 }, () => []);
  const dotBuckets = Array.from({ length: 7 }, () => []);
  let isLight = document.documentElement.dataset.futureTheme === "light";
  const sceneColor = (dark, light, alpha) => `rgba(${isLight ? light : dark},${alpha})`;
  const darkMeshColors = [
    "rgba(49,116,230,.065)", "rgba(52,128,238,.09)",
    "rgba(54,140,246,.12)", "rgba(65,153,252,.16)",
    "rgba(77,166,255,.20)", "rgba(92,185,255,.25)",
    "rgba(120,205,255,.31)",
  ];
  const darkDotColors = [
    "rgba(69,136,244,.19)", "rgba(71,148,250,.27)",
    "rgba(75,161,255,.38)", "rgba(89,181,255,.52)",
    "rgba(109,201,255,.69)", "rgba(143,222,255,.83)",
    "rgba(194,242,255,.96)",
  ];
  const lightMeshColors = [.07, .10, .14, .18, .23, .29, .37].map(alpha => `rgba(24,103,169,${alpha})`);
  const lightDotColors = [.18, .26, .36, .48, .62, .78, .95].map(alpha => `rgba(18,105,172,${alpha})`);
  let meshColors = isLight ? lightMeshColors : darkMeshColors;
  let dotColors = isLight ? lightDotColors : darkDotColors;

  for (let row = 0; row < latitudeCount; row++) {
    const latitude = -Math.PI / 2 + Math.PI * (row + 0.5) / latitudeCount;
    const latitudeRadius = Math.cos(latitude);
    for (let column = 0; column < longitudeCount; column++) {
      const index = row * longitudeCount + column;
      const longitude = column * Math.PI * 2 / longitudeCount;
      points[index * 3] = latitudeRadius * Math.cos(longitude);
      points[index * 3 + 1] = Math.sin(latitude);
      points[index * 3 + 2] = latitudeRadius * Math.sin(longitude);
      edgeIndices.push(index, row * longitudeCount + (column + 1) % longitudeCount);
      if (row + 1 < latitudeCount) edgeIndices.push(index, index + longitudeCount);
    }
  }
  const edges = new Uint16Array(edgeIndices);

  function makeOrbit(radius, tilt, roll, phase, speed) {
    const count = 144;
    const source = new Float32Array(count * 3);
    const screen = new Float32Array(count * 3);
    for (let index = 0; index < count; index++) {
      const angle = index * Math.PI * 2 / count;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius * Math.cos(tilt);
      source[index * 3] = x * Math.cos(roll) - y * Math.sin(roll);
      source[index * 3 + 1] = x * Math.sin(roll) + y * Math.cos(roll);
      source[index * 3 + 2] = Math.sin(angle) * radius * Math.sin(tilt);
    }
    return { count, source, screen, phase, speed };
  }
  const orbits = [
    makeOrbit(1.36, 1.08, -0.35, 0.15, 0.029),
    makeOrbit(1.24, 1.04, 0.86, 0.62, -0.022),
    makeOrbit(1.52, 1.32, -0.12, 0.38, 0.016),
  ];

  // A deterministic star field avoids layout changes and random flicker.
  const stars = Array.from({ length: 46 }, (_, index) => ({
    x: ((index * 137 + 37) % 997) / 997,
    y: ((index * 251 + 89) % 991) / 991,
    radius: index % 7 === 0 ? 1.15 : 0.55,
    phase: index * 0.83,
  }));

  let width = 0;
  let height = 0;
  let pixelRatio = 1;
  let radius = 0;
  let centerX = 0;
  let centerY = 0;
  let dotScale = 1;
  let halo;
  let frame = 0;
  let lastTimestamp = null;
  let sceneTime = 0;
  let inViewport = false;
  let reducedMotion = Boolean(motionPreference?.matches);
  let suspended = false;
  let destroyed = false;
  let resizeObserver;
  let intersectionObserver;
  let mutationObserver;

  function homepageVisible() {
    return !homepage || (!homepage.hidden && homepage.style.display !== "none");
  }

  function visible() {
    return !destroyed && !suspended && !document.hidden && inViewport &&
      width > 0 && height > 0 && homepageVisible();
  }

  function cancelFrame() {
    if (frame) window.cancelAnimationFrame(frame);
    frame = 0;
    lastTimestamp = null;
  }

  function project(source, target, rotation, scale) {
    const cosine = Math.cos(rotation);
    const sine = Math.sin(rotation);
    const tiltCosine = 0.9855847669; // A quiet, fixed axial tilt.
    const tiltSine = -0.1691823491;
    for (let index = 0; index < source.length; index += 3) {
      const x = source[index] * cosine + source[index + 2] * sine;
      const z = -source[index] * sine + source[index + 2] * cosine;
      const y = source[index + 1] * tiltCosine - z * tiltSine;
      const depth = source[index + 1] * tiltSine + z * tiltCosine;
      const perspective = scale / (1 - depth * 0.09);
      target[index] = centerX + x * perspective;
      target[index + 1] = centerY + y * perspective;
      target[index + 2] = depth;
    }
  }

  function drawOrbit(orbit, foreground, time) {
    const { count, screen } = orbit;
    context.beginPath();
    for (let index = 0; index < count; index++) {
      const next = (index + 1) % count;
      if ((screen[index * 3 + 2] + screen[next * 3 + 2] > 0) !== foreground) continue;
      context.moveTo(screen[index * 3], screen[index * 3 + 1]);
      context.lineTo(screen[next * 3], screen[next * 3 + 1]);
    }
    context.strokeStyle = foreground ? sceneColor("82,178,255", "28,113,174", .24) : sceneColor("45,121,235", "39,109,168", .14);
    context.lineWidth = foreground ? 0.85 : 0.65;
    context.stroke();

    const progress = ((time * orbit.speed + orbit.phase) % 1 + 1) % 1;
    const head = Math.floor(progress * count);
    for (let segment = 0; segment < 16; segment++) {
      const index = (head - segment + count) % count;
      const next = (index + 1) % count;
      if ((screen[index * 3 + 2] + screen[next * 3 + 2] > 0) !== foreground) continue;
      const strength = (1 - segment / 16) * (foreground ? 0.83 : 0.30);
      context.beginPath();
      context.moveTo(screen[index * 3], screen[index * 3 + 1]);
      context.lineTo(screen[next * 3], screen[next * 3 + 1]);
      context.strokeStyle = sceneColor("126,224,255", "11,122,180", strength);
      context.lineWidth = (1.15 + (1 - segment / 16) * 0.65) * dotScale;
      context.stroke();
    }
  }

  function render(time) {
    if (!width || !height || destroyed) return;
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    context.clearRect(0, 0, width, height);
    context.fillStyle = halo;
    context.fillRect(0, 0, width, height);

    for (const star of stars) {
      const x = star.x * width;
      const y = star.y * height;
      if (Math.hypot(x - centerX, y - centerY) < radius * 1.02) continue;
      const alpha = 0.15 + (Math.sin(time * 0.34 + star.phase) + 1) * 0.08;
      context.fillStyle = sceneColor("129,199,255", "32,112,174", alpha);
      context.beginPath();
      context.arc(x, y, star.radius * dotScale, 0, Math.PI * 2);
      context.fill();
    }

    const rotation = -0.48 + time * 0.075;
    project(points, projected, rotation, radius);
    for (const orbit of orbits) {
      project(orbit.source, orbit.screen, Math.sin(time * 0.035) * 0.12, radius);
      drawOrbit(orbit, false, time);
    }

    for (let index = 0; index < meshBuckets.length; index++) {
      meshBuckets[index].length = 0;
      dotBuckets[index].length = 0;
    }
    for (let index = 0; index < pointCount; index++) {
      const bucket = Math.max(0, Math.min(6, Math.floor((projected[index * 3 + 2] + 1) * 3.5)));
      dotBuckets[bucket].push(index);
    }
    for (let index = 0; index < edges.length; index += 2) {
      const depth = (projected[edges[index] * 3 + 2] + projected[edges[index + 1] * 3 + 2]) / 2;
      const bucket = Math.max(0, Math.min(6, Math.floor((depth + 1) * 3.5)));
      meshBuckets[bucket].push(index);
    }
    for (let bucket = 0; bucket < meshBuckets.length; bucket++) {
      context.beginPath();
      for (const edge of meshBuckets[bucket]) {
        const start = edges[edge] * 3;
        const end = edges[edge + 1] * 3;
        context.moveTo(projected[start], projected[start + 1]);
        context.lineTo(projected[end], projected[end + 1]);
      }
      context.strokeStyle = meshColors[bucket];
      context.lineWidth = (0.45 + bucket * 0.045) * dotScale;
      context.stroke();

      context.beginPath();
      const pointRadius = (0.65 + bucket * 0.15) * dotScale;
      for (const point of dotBuckets[bucket]) {
        const x = projected[point * 3];
        const y = projected[point * 3 + 1];
        context.moveTo(x + pointRadius, y);
        context.arc(x, y, pointRadius, 0, Math.PI * 2);
      }
      context.fillStyle = dotColors[bucket];
      context.fill();
    }

    // Sparse luminous junctions suggest a network without a noisy particle storm.
    context.save();
    context.globalCompositeOperation = isLight ? "source-over" : "lighter";
    for (let index = 13; index < pointCount; index += 47) {
      const depth = projected[index * 3 + 2];
      if (depth < 0.12) continue;
      const x = projected[index * 3];
      const y = projected[index * 3 + 1];
      const pulse = 0.75 + Math.sin(time * 0.8 + index) * 0.18;
      context.beginPath();
      context.arc(x, y, (5 + depth * 3) * dotScale, 0, Math.PI * 2);
      context.fillStyle = sceneColor("39,161,255", "17,124,193", 0.065 * pulse);
      context.fill();
      context.beginPath();
      context.arc(x, y, (1.5 + depth * 0.5) * dotScale, 0, Math.PI * 2);
      context.fillStyle = sceneColor("188,241,255", "12,111,176", 0.85 * pulse);
      context.shadowColor = sceneColor("68,184,255", "33,141,211", .75);
      context.shadowBlur = 10 * dotScale;
      context.fill();
      context.shadowBlur = 0;
    }
    for (const orbit of orbits) drawOrbit(orbit, true, time);
    context.restore();
  }

  function tick(timestamp) {
    frame = 0;
    if (!canvas.isConnected) { destroy(); return; }
    if (!visible() || reducedMotion) { lastTimestamp = null; return; }
    if (lastTimestamp !== null) sceneTime += Math.min((timestamp - lastTimestamp) / 1000, 0.05);
    lastTimestamp = timestamp;
    render(sceneTime);
    frame = window.requestAnimationFrame(tick);
  }

  function synchronize() {
    if (!visible()) { cancelFrame(); return; }
    if (reducedMotion) {
      cancelFrame();
      render(sceneTime);
    } else if (!frame) {
      frame = window.requestAnimationFrame(tick);
    }
  }

  function makeHalo() {
    if (radius <= 0) return;
    halo = context.createRadialGradient(centerX, centerY, radius * 0.12, centerX, centerY, radius * 1.48);
    halo.addColorStop(0, sceneColor("10,84,193", "62,158,219", .07));
    halo.addColorStop(0.63, sceneColor("16,113,239", "57,157,223", .045));
    halo.addColorStop(0.80, sceneColor("27,127,255", "54,152,218", .065));
    halo.addColorStop(1, sceneColor("12,86,220", "54,152,218", 0));
  }

  function onThemeChange() {
    isLight = document.documentElement.dataset.futureTheme === "light";
    meshColors = isLight ? lightMeshColors : darkMeshColors;
    dotColors = isLight ? lightDotColors : darkDotColors;
    makeHalo();
    if (visible()) render(sceneTime);
  }

  function measure() {
    if (destroyed) return;
    const bounds = container.getBoundingClientRect();
    const nextWidth = Math.max(0, Math.round(bounds.width));
    const nextHeight = Math.max(0, Math.round(bounds.height));
    const nextRatio = Math.min(2, Math.max(1, window.devicePixelRatio || 1));
    inViewport = bounds.bottom > 0 && bounds.right > 0 &&
      bounds.top < window.innerHeight && bounds.left < window.innerWidth;
    if (width !== nextWidth || height !== nextHeight || pixelRatio !== nextRatio) {
      width = nextWidth;
      height = nextHeight;
      pixelRatio = nextRatio;
      canvas.width = Math.round(width * pixelRatio);
      canvas.height = Math.round(height * pixelRatio);
      radius = Math.min(width, height) * 0.325;
      centerX = width * 0.5;
      centerY = height * 0.48;
      dotScale = Math.max(0.76, Math.min(1.15, Math.min(width, height) / 520));
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      if (radius > 0) {
        makeHalo();
        if (visible()) render(sceneTime);
      }
    }
    synchronize();
  }

  function onVisibilityChange() { synchronize(); }
  function onMotionChange(event) {
    reducedMotion = event.matches;
    synchronize();
  }
  function onHomeChange() {
    if (!homepageVisible()) { cancelFrame(); return; }
    measure();
  }
  function onPageHide(event) {
    if (!event.persisted) { destroy(); return; }
    suspended = true;
    cancelFrame();
  }
  function onPageShow() {
    if (destroyed) return;
    suspended = false;
    measure();
  }

  function destroy() {
    if (destroyed) return;
    destroyed = true;
    cancelFrame();
    resizeObserver?.disconnect();
    intersectionObserver?.disconnect();
    mutationObserver?.disconnect();
    document.removeEventListener("visibilitychange", onVisibilityChange);
    window.removeEventListener("resize", measure);
    window.removeEventListener("scroll", measure);
    window.removeEventListener("pagehide", onPageHide);
    window.removeEventListener("pageshow", onPageShow);
    window.removeEventListener("futureskill:themechange", onThemeChange);
    if (motionPreference?.removeEventListener) motionPreference.removeEventListener("change", onMotionChange);
    else if (motionPreference?.removeListener) motionPreference.removeListener(onMotionChange);
  }

  document.addEventListener("visibilitychange", onVisibilityChange);
  window.addEventListener("resize", measure, { passive: true });
  window.addEventListener("pagehide", onPageHide);
  window.addEventListener("pageshow", onPageShow);
  window.addEventListener("futureskill:themechange", onThemeChange);
  if (motionPreference?.addEventListener) motionPreference.addEventListener("change", onMotionChange);
  else if (motionPreference?.addListener) motionPreference.addListener(onMotionChange);
  if (typeof window.ResizeObserver === "function") {
    resizeObserver = new ResizeObserver(measure);
    resizeObserver.observe(container);
  }
  if (typeof window.IntersectionObserver === "function") {
    intersectionObserver = new IntersectionObserver(entries => {
      inViewport = entries.some(entry => entry.isIntersecting);
      synchronize();
    });
    intersectionObserver.observe(container);
  } else {
    window.addEventListener("scroll", measure, { passive: true });
  }
  if (homepage && typeof window.MutationObserver === "function") {
    mutationObserver = new MutationObserver(onHomeChange);
    mutationObserver.observe(homepage, { attributes: true, attributeFilter: ["style", "hidden", "class"] });
  }
  measure();
})();
