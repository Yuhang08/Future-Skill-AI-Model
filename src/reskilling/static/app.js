/* FutureSkill AI: zero-library frontend for the Python stdlib backend. */
const DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (s) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
const pageParams = new URLSearchParams(window.location.search);
const demoMode = pageParams.get('demo') === '1';
let appState = null;
let csrf = '';
let step = 0;
let selectedWeek = 'auto';
let toastTimer;
const THEME_STORAGE_KEY = 'futureskill-theme-preference';
let themeChoice = 'system';
let themeMediaQuery = null;

function toast(message, isError=false) {
  const node = $('toast');
  node.textContent = message;
  node.classList.toggle('error', isError);
  node.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove('visible'), 4200);
}
async function api(path, method='GET', data) {
  if (demoMode) {
    const separator = path.includes('?') ? '&' : '?';
    path += `${separator}demo=1&demo_scenario=${encodeURIComponent(pageParams.get('demo_scenario') || 'default')}`;
  }
  const options = {method, credentials:'same-origin', headers:{}};
  if (method !== 'GET') options.headers['X-CSRF-Token'] = csrf;
  if (data instanceof FormData) options.body = data;
  else if (data !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(data);
  }
  const response = await fetch(path, options);
  let payload;
  try { payload = await response.json(); }
  catch { throw new Error('The server returned an unexpected response.'); }
  if (!response.ok) throw new Error(payload.error || 'Something went wrong.');
  return payload;
}
function applyThemePreference(choice, persist=true) {
  themeChoice = ['light','dark','system'].includes(choice) ? choice : 'system';
  if (window.FutureSkillTheme) {
    window.FutureSkillTheme.setPreference(themeChoice, persist);
    return;
  }
  const prefersDark = window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)').matches
    : false;
  const resolvedTheme = themeChoice === 'system'
    ? (prefersDark ? 'dark' : 'light')
    : themeChoice;
  document.documentElement.dataset.theme = resolvedTheme;
  document.documentElement.dataset.themePreference = themeChoice;
  document.querySelectorAll('#themePreference input[name="themePreference"]').forEach(input => {
    input.checked = input.value === themeChoice;
  });
  if (persist) {
    try { localStorage.setItem(THEME_STORAGE_KEY, themeChoice); }
    catch { /* Theme still applies for this visit when storage is unavailable. */ }
  }
}
function initThemePreference() {
  if (window.FutureSkillTheme) {
    themeChoice = window.FutureSkillTheme.getState().preference;
    window.addEventListener('futureskill:themechange', event => {
      themeChoice = event.detail.preference;
    });
    window.FutureSkillTheme.setPreference(themeChoice, false);
    return;
  }
  let saved = 'system';
  try { saved = localStorage.getItem(THEME_STORAGE_KEY) || 'system'; }
  catch { /* Use the system appearance when browser storage is unavailable. */ }
  applyThemePreference(saved, false);
  if (!window.matchMedia) return;
  themeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const updateSystemTheme = () => {
    if (themeChoice === 'system') applyThemePreference('system', false);
  };
  if (themeMediaQuery.addEventListener) themeMediaQuery.addEventListener('change', updateSystemTheme);
  else if (themeMediaQuery.addListener) themeMediaQuery.addListener(updateSystemTheme);
}
function setWorkspaceNotice(message) {
  const notice = $('workspaceNotice');
  if (!notice) return;
  notice.textContent = message;
  notice.hidden = !message;
}
function setWorkspaceActive(action) {
  if (action === 'settings' || action === 'edit-profile') return;
  const items = document.querySelectorAll('#workspaceNav [data-workspace-action]');
  items.forEach(item => {
    const active = item.dataset.workspaceAction === action;
    item.classList.toggle('active', active);
    if (active) item.setAttribute('aria-current', 'location');
    else item.removeAttribute('aria-current');
  });
}
function updateSdgNavLink() {
  const link = $('sdgNavLink');
  if (!link) return;
  const career = appState?.profile?.target_career || $('targetCareer')?.value;
  link.href = career ? `/sdg-impact?career=${encodeURIComponent(career)}` : '/sdg-impact';
}
function closeWorkspaceSidebar() {
  const toggle = $('workspaceToggle');
  const sidebar = $('workspaceSidebar');
  document.body.classList.remove('workspace-nav-open');
  sidebar?.classList.remove('is-open');
  toggle?.setAttribute('aria-expanded', 'false');
  toggle?.setAttribute('aria-label', 'Open workspace navigation');
}
function openWorkspaceSettings() {
  const dialog = $('settingsDialog');
  if (!dialog) return;
  if (typeof dialog.showModal === 'function') dialog.showModal();
  else dialog.setAttribute('open', '');
}
function closeWorkspaceSettings() {
  const dialog = $('settingsDialog');
  if (!dialog) return;
  if (typeof dialog.close === 'function' && dialog.open) dialog.close();
  else dialog.removeAttribute('open');
}
function handleWorkspaceAction(action) {
  closeWorkspaceSidebar();
  if (action === 'settings') {
    openWorkspaceSettings();
    return;
  }
  if (action === 'edit-profile') {
    closeWorkspaceSettings();
    if (appState?.profile) {
      $('editProfile').click();
    } else {
      setWorkspaceActive('plan');
      setWorkspaceNotice('Create your learning profile to begin. You can enter your skills manually in setup.');
      $('workspaceNotice')?.scrollIntoView({behavior:'smooth', block:'start'});
    }
    return;
  }
  if (action === 'overview') {
    setWorkspaceActive('overview');
    setWorkspaceNotice('');
    $(appState?.profile ? 'dashboard' : 'hero')?.scrollIntoView({behavior:'smooth', block:'start'});
    return;
  }
  if (action === 'begin-setup') {
    setWorkspaceActive('plan');
    setWorkspaceNotice('');
    $('questionnaire').hidden = false;
    setSteps(0);
    $('questionnaire').scrollIntoView({behavior:'smooth', block:'start'});
    $('userType').focus({preventScroll:true});
    return;
  }
  if (action === 'plan') {
    setWorkspaceActive('plan');
    if (appState?.profile) {
      setWorkspaceNotice('');
      $('pathwaySection')?.scrollIntoView({behavior:'smooth', block:'start'});
    } else {
      setWorkspaceNotice('Generate a learning profile first to unlock your saved reskilling plan.');
      $('workspaceNotice')?.scrollIntoView({behavior:'smooth', block:'start'});
    }
    return;
  }
  if (action === 'progress') {
    setWorkspaceActive('progress');
    if (appState?.profile) {
      setWorkspaceNotice('');
      $('gapsSection')?.scrollIntoView({behavior:'smooth', block:'start'});
    } else {
      setWorkspaceNotice('Progress tracking will be available after you create a learning profile and plan.');
      $('workspaceNotice')?.scrollIntoView({behavior:'smooth', block:'start'});
    }
  }
}
function initWorkspaceNavigation() {
  const toggle = $('workspaceToggle');
  const sidebar = $('workspaceSidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      const isOpen = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(isOpen));
      toggle.setAttribute('aria-label', isOpen ? 'Close workspace navigation' : 'Open workspace navigation');
      sidebar.classList.toggle('is-open', isOpen);
      document.body.classList.toggle('workspace-nav-open', isOpen);
    });
    document.addEventListener('click', event => {
      if (!document.body.classList.contains('workspace-nav-open')) return;
      if (event.target.closest('#workspaceSidebar, #workspaceToggle')) return;
      closeWorkspaceSidebar();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') closeWorkspaceSidebar();
    });
  }
  document.querySelectorAll('[data-workspace-action]').forEach(item => {
    item.addEventListener('click', () => handleWorkspaceAction(item.dataset.workspaceAction));
  });
  $('workspaceNav')?.addEventListener('click', event => {
    if (event.target.closest('a.workspace-nav-item')) closeWorkspaceSidebar();
  });
  $('settingsClose')?.addEventListener('click', closeWorkspaceSettings);
  $('settingsDialog')?.addEventListener('click', event => {
    if (event.target === $('settingsDialog')) closeWorkspaceSettings();
  });
  $('themePreference')?.addEventListener('change', event => {
    if (event.target.matches('input[name="themePreference"]')) {
      applyThemePreference(event.target.value);
    }
  });
  setWorkspaceActive('overview');
  updateSdgNavLink();
}
function showDemoBanner() {
  if (!demoMode) return;
  const banner = document.createElement('div');
  banner.className = 'dev-demo-banner';
  banner.setAttribute('role', 'note');
  const label = document.createElement('strong');
  label.textContent = 'DEVELOPMENT DEMO — isolated sample data';
  const detail = document.createElement('span');
  detail.textContent = 'Changes here do not alter a normal learner session.';
  const link = document.createElement('a');
  link.href = '/__dev/screens';
  link.textContent = 'Screen inventory';
  banner.append(label, detail, link);
  document.body.prepend(banner);
}
function dayPills(container, name, checked=['Tuesday','Thursday','Saturday']) {
  $(container).innerHTML = DAYS.map(day =>
    `<label><input type="checkbox" name="${name}" value="${day}" ${checked.includes(day)?'checked':''}>${day.slice(0,3)}</label>`
  ).join('');
}
function selectedDays(container) {
  return [...$(container).querySelectorAll('input:checked')].map(node => node.value);
}
function setSteps(next) {
  step = Math.max(0, Math.min(next, 2));
  document.querySelectorAll('.step-panel').forEach(p => { p.hidden = Number(p.dataset.step) !== step; });
  document.querySelectorAll('[data-go-step]').forEach(b => b.classList.toggle('active', Number(b.dataset.goStep) === step));
  $('prevStep').hidden = step === 0;
  $('nextStep').hidden = step === 2;
  $('submitPlan').hidden = step !== 2;
  $('formError').textContent = '';
}
function drawSkillInputs(saved={}) {
  const career = $('targetCareer').value;
  const role = appState.catalog[career];
  if (!role) return;
  $('skillsForm').innerHTML = Object.entries(role.skills).map(([name, details], idx) => {
    const level = saved[name] !== undefined ? Number(saved[name]) : 0;
    return `<div class="skill-rating">
      <div class="rating-head"><strong>${escapeHtml(name)}</strong><span id="skillVal${idx}">${level}/5</span></div>
      <input type="range" data-skill="${escapeHtml(name)}" data-label="skillVal${idx}" min="0" max="5" step="1" value="${level}" aria-label="My ${escapeHtml(name)} skill level">
      <div class="rating-foot"><span>0 · Not learned yet</span><span>5 · Very confident</span></div>
    </div>`;
  }).join('');
  $('skillsForm').querySelectorAll('input[type=range]').forEach(input => input.addEventListener('input', () => $(input.dataset.label).textContent = `${input.value}/5`));
}
function fillForm(profile) {
  $('userType').value = profile?.user_type || 'student';
  $('industry').value = profile?.current_industry || '';
  $('experience').value = profile?.experience || 'beginner';
  $('targetCareer').value = profile?.target_career || Object.keys(appState.catalog)[0];
  $('personalGoal').value = profile?.personal_goal || '';
  $('weeklyHours').value = profile?.weekly_hours || 6;
  $('weeklyHoursOutput').textContent = `${$('weeklyHours').value} hours`;
  $('targetWeeks').value = profile?.target_weeks || 8;
  $('learningStyle').value = profile?.learning_style || 'project';
  dayPills('preferredDays','preferredDays', profile?.preferred_days || ['Tuesday','Thursday','Saturday']);
  drawSkillInputs(profile?.skills || {});
}
function readForm() {
  const skills = {};
  $('skillsForm').querySelectorAll('input[data-skill]').forEach(input => { skills[input.dataset.skill] = Number(input.value); });
  const days = selectedDays('preferredDays');
  if (!days.length) throw new Error('Please choose at least one study day.');
  const weeks = Number($('targetWeeks').value);
  if (!Number.isInteger(weeks) || weeks < 1 || weeks > 52) throw new Error('Choose between 1 and 52 weeks.');
  return {
    user_type: $('userType').value,
    current_industry: $('industry').value,
    experience: $('experience').value,
    target_career: $('targetCareer').value,
    personal_goal: $('personalGoal').value,
    skills, weekly_hours: Number($('weeklyHours').value),
    target_weeks: weeks,
    preferred_days: days,
    learning_style: $('learningStyle').value
  };
}
function renderTree(tree, animate=false) {
  $('treeEmoji').textContent = tree.emoji;
  $('treeEmoji').setAttribute('aria-label', `Learning tree stage: ${tree.name}`);
  $('treeName').textContent = tree.name;
  $('treePoints').textContent = `${tree.points} XP`;
  $('pointsStat').textContent = `${tree.points} XP`;
  $('treeMessage').textContent = tree.message;
  // Show progress since current threshold to the next tree stage.
  const stages = [0,10,35,80,150,250];
  const current = [...stages].reverse().find(v => v <= tree.points) || 0;
  const fraction = tree.next_points ? Math.max(0, Math.min(1, (tree.points-current)/(tree.next_points-current))) : 1;
  $('treeProgress').style.width = `${fraction*100}%`;
  $('treeNext').textContent = tree.next_points ? `${tree.next_points-tree.points} XP until ${tree.next_name}` : 'Your forest is thriving. Keep exploring and creating!';
  if (animate) {
    $('treeEmoji').classList.remove('pulse-grow');
    void $('treeEmoji').offsetWidth;
    $('treeEmoji').classList.add('pulse-grow');
  }
}
function completedPracticeLevels(name, gap, tasks) {
  // Baseline self-ratings must not be displayed as earned progress.
  // Only fully completed learning-task practice milestones fill the bar.
  // The milestones are estimates, never automatic proof of mastery.
  const plannedLevels = Math.max(0, Number(gap.gap) || 0);
  const estimatedHours = Number(gap.estimated_hours) || 0;
  if (!plannedLevels || !estimatedHours) return {completed:0, planned:plannedLevels};
  const completedHours = (Array.isArray(tasks) ? tasks : [])
    .filter(task => task.skill === name && task.kind === 'learning' && task.completed)
    .reduce((total, task) => total + (Number(task.hours) || 0), 0);
  const hoursPerLevel = estimatedHours / plannedLevels;
  const completed = Math.min(plannedLevels,
    Math.floor((completedHours + 0.001) / hoursPerLevel));
  return {completed, planned:plannedLevels};
}
function renderGaps(gaps, tasks=[]) {
  const sorted = Object.entries(gaps).sort((a,b) => b[1].priority-a[1].priority);
  $('gapList').innerHTML = sorted.map(([name, g]) => {
    const hasGap = Number(g.gap) > 0;
    const progress = completedPracticeLevels(name, g, tasks);
    const percent = progress.planned
      ? Math.max(0, Math.min(100, progress.completed / progress.planned * 100))
      : 0;
    const milestoneText = progress.planned
      ? progress.completed + ' of ' + progress.planned + ' practice levels completed'
      : 'No additional practice levels scheduled';
    return '<div class="gap-item">' +
      '<div class="gap-top"><strong>' + escapeHtml(name) + '</strong><span>Starting self-rating: ' +
      g.current + '/5 · target: ' + g.required + '/5</span></div>' +
      '<div class="gap-bar" role="progressbar" aria-label="' + escapeHtml(name) +
      ' completed practice milestones" aria-valuemin="0" aria-valuemax="' +
      progress.planned + '" aria-valuenow="' + progress.completed + '">' +
      '<div class="gap-current" style="width:' + percent + '%"></div></div>' +
      '<div class="gap-footer"><span>' + milestoneText +
      (hasGap ? ' · Gap: ' + g.gap + ' level(s)' : ' · Self-rating meets example target') +
      '</span><b>' + g.remaining_hours + ' h estimated practice left</b></div>' +
      '</div>';
  }).join('');
}

function dateHuman(iso) {
  // Parse in local time (avoid UTC midnight changing a display date).
  const [y,m,d] = iso.split('-').map(Number);
  return new Intl.DateTimeFormat('en', {month:'short', day:'numeric'}).format(new Date(y, m-1, d));
}
function renderTask(task) {
  const isReview = task.kind === 'review';
  return `<div class="task-row">
    <input class="task-check" type="checkbox" aria-label="Complete ${escapeHtml(task.skill)}" data-task-id="${task.id}" ${task.completed?'checked':''}>
    <div>
      <div class="task-title">${escapeHtml(task.skill)}</div>
      <div class="task-meta"><span class="task-tag ${isReview?'review':''}">${isReview?'Review & catch-up':'Learning task'}</span><span class="muted tiny">${task.hours.toFixed(2)}h · +${task.points} XP</span></div>
      <div class="task-description"><b>Objective:</b> ${escapeHtml(task.objective)}</div>
      <div class="task-description">${escapeHtml(task.activity)}</div>
      <div class="task-meta">
        <label class="task-photo">📷 Upload learning photo<input type="file" data-upload-id="${task.id}" accept="image/jpeg,image/png,image/webp" capture="environment"></label>
        ${task.proof_url ? `<a class="proof-link" href="${task.proof_url}" target="_blank" rel="noopener">View uploaded photo ↗</a>` : ''}
      </div>
    </div>
  </div>`;
}
function renderPlan(tasks) {
  const unfinished = tasks.filter(t => !t.completed);
  const finished = tasks.filter(t => t.completed);
  const weekIndices = [...new Set(unfinished.map(t => t.week_index))].sort((a,b) => a-b);
  const options = [`<option value="all">All upcoming weeks</option>`,...weekIndices.map(week => `<option value="${week}">Week ${week}</option>`)];
  $('weekSelect').innerHTML = options.join('');
  if (selectedWeek === 'auto') selectedWeek = weekIndices.length ? String(weekIndices[0]) : 'all';
  if (selectedWeek !== 'all' && !weekIndices.includes(Number(selectedWeek))) selectedWeek = weekIndices.length ? String(weekIndices[0]) : 'all';
  $('weekSelect').value = selectedWeek;
  const visible = selectedWeek === 'all' ? unfinished : unfinished.filter(t => t.week_index === Number(selectedWeek));
  const grouped = new Map();
  visible.forEach(task => {
    const key = `${task.week_index}_${task.due_date}`;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(task);
  });
  $('todoList').innerHTML = [...grouped].map(([, groupedTasks]) => {
    const item = groupedTasks[0];
    return `<div class="day-group"><div class="day-heading">WEEK ${item.week_index} · ${item.day}, ${dateHuman(item.due_date)}</div>
      ${groupedTasks.map(renderTask).join('')}</div>`;
  }).join('');
  $('emptyTasks').hidden = unfinished.length > 0;
  $('winsCount').textContent = `(${finished.length})`;
  $('completedWins').innerHTML = finished.slice().reverse().slice(0,14).map(task => `<div class="win-item"><span class="win-check">✓</span><div class="win-content"><strong>${escapeHtml(task.skill)}</strong><small>${dateHuman(task.due_date)} · ${task.hours.toFixed(2)} h · +${task.points} XP</small><label class="task-photo">📷 ${task.proof_url?'Replace photo':'Add photo'}<input type="file" data-upload-id="${task.id}" accept="image/jpeg,image/png,image/webp" capture="environment"></label> ${task.proof_url ? `<a class="proof-link" href="${task.proof_url}" target="_blank" rel="noopener">View photo ↗</a>` : ''}</div><input class="task-check" type="checkbox" checked data-task-id="${task.id}" aria-label="Reopen ${escapeHtml(task.skill)} task"></div>`).join('') || '<p class="muted tiny">Your completed tasks will appear here. Every small step counts.</p>';
}
function renderDashboard(state, animateTree=false) {
  if (!state.profile) return;
  const p = state.profile, s = state.stats;
  $('careerName').textContent = p.target_career;
  $('dashboardIntro').textContent = p.personal_goal || 'One achievable objective, one study session, one skill at a time.';
  $('hoursStat').textContent = `${s.learning_hours_completed} / ${s.estimated_learning_hours} h`;
  $('tasksStat').textContent = `${s.completed_tasks} / ${s.total_tasks}`;
  $('weekStat').textContent = `${p.weekly_hours} h`;
  $('planDuration').textContent = `${p.target_weeks} week plan`;
  $('overallProgressText').textContent = `${s.study_progress_pct}%`;
  $('overallProgress').style.width = `${s.study_progress_pct}%`;
  const unfinishedScheduled = state.tasks.filter(t => !t.completed && t.kind==='learning').reduce((sum,t)=>sum+t.hours,0);
  $('planNote').textContent = s.remaining_hours > unfinishedScheduled+0.04
    ? `Estimated practice left: ${s.remaining_hours} h. Your current schedule includes ${unfinishedScheduled.toFixed(1)} h of learning; you may need more weeks to cover the rest. These are planning estimates.`
    : `Estimated practice remaining: ${s.remaining_hours} h. Review time is built into your timetable. Skill mastery should be checked with a project or assessment.`;
  renderGaps(state.gaps, state.tasks);
  renderPlan(state.tasks);
  renderTree(state.tree, animateTree);
  $('replanHours').value = p.weekly_hours;
  $('replanWeeks').value = p.target_weeks;
  dayPills('replanDays','replanDays',p.preferred_days);
}
function showApp(state) {
  appState = state;
  updateSdgNavLink();
  if (state.profile) {
    $('questionnaire').hidden = true;
    $('cancelEdit').hidden = true;
    $('dashboard').hidden = false;
    document.body.classList.add('has-dashboard');
    renderDashboard(state);
  } else {
    $('dashboard').hidden = true;
    document.body.classList.remove('has-dashboard');
    $('questionnaire').hidden = false;
    fillForm(null);
    setSteps(0);
  }
}
async function submitPlan(event) {
  event.preventDefault();
  const submit = $('submitPlan');
  try {
    submit.disabled = true;
    const payload = readForm();
    const result = await api('/api/plan', 'POST', payload);
    showApp(result.state);
    window.scrollTo({top:0,behavior:'smooth'});
    toast('Your personalised learning pathway is ready! 🌱');
  } catch (error) {
    $('formError').textContent = error.message;
    toast(error.message, true);
  } finally { submit.disabled = false; }
}
async function toggleTask(input) {
  const id = input.dataset.taskId;
  const checked = input.checked;
  input.disabled = true;
  try {
    const old = appState.tree.name;
    const response = await api(`/api/tasks/${id}/status`, 'POST', {completed:checked});
    appState = response.state;
    renderDashboard(appState, checked || response.state.tree.name!==old);
    toast(response.message);
  } catch (error) {
    input.checked = !checked;
    toast(error.message, true);
  } finally {input.disabled = false;}
}
async function uploadPhoto(input) {
  const file = input.files?.[0];
  if (!file) return;
  if (!['image/jpeg','image/png','image/webp'].includes(file.type) || file.size > 5*1024*1024) {
    toast('Choose a JPG, PNG or WEBP image smaller than 5 MB.', true);
    input.value = '';
    return;
  }
  const data = new FormData();
  data.append('photo', file);
  input.disabled = true;
  try {
    const response = await api(`/api/tasks/${input.dataset.uploadId}/proof`, 'POST', data);
    appState = response.state;
    renderDashboard(appState);
    toast(response.message);
  } catch (error) {toast(error.message,true);}
  finally {input.disabled = false;}
}
async function submitReplan(event) {
  event.preventDefault();
  const payload = {
    weekly_hours:Number($('replanHours').value),
    target_weeks:Number($('replanWeeks').value),
    preferred_days:selectedDays('replanDays'),
  };
  if (!payload.preferred_days.length) return toast('Please choose one or more study days.',true);
  if (!Number.isInteger(payload.target_weeks) || payload.target_weeks<1 || payload.target_weeks>52) return toast('Plan length must be between 1 and 52 weeks.',true);
  try {
    const response = await api('/api/replan','POST',payload);
    selectedWeek='auto';
    appState = response.state;
    renderDashboard(appState);
    toast('Your unfinished tasks have a fresh schedule. Your completed wins and tree are safe. 🌿');
    $('pathwaySection').scrollIntoView({behavior:'smooth',block:'start'});
  } catch(error) {toast(error.message,true);}
}
function initListeners() {
  initWorkspaceNavigation();
  $('weeklyHours').addEventListener('input',()=>{$('weeklyHoursOutput').textContent=`${$('weeklyHours').value} hours`;});
  $('targetCareer').addEventListener('change',()=>{drawSkillInputs();updateSdgNavLink();});
  $('nextStep').addEventListener('click',()=>setSteps(step+1));
  $('prevStep').addEventListener('click',()=>setSteps(step-1));
  document.querySelectorAll('[data-go-step]').forEach(b=>b.addEventListener('click',()=>setSteps(Number(b.dataset.goStep))));
  $('assessmentForm').addEventListener('submit',submitPlan);
  $('editProfile').addEventListener('click',()=>{
    fillForm(appState.profile);
    setSteps(0);
    $('dashboard').hidden=true;
    document.body.classList.remove('has-dashboard');
    $('questionnaire').hidden=false;
    $('cancelEdit').hidden=false;
    $('questionnaire').scrollIntoView({behavior:'smooth'});
  });
  $('cancelEdit').addEventListener('click',()=>showApp(appState));
  $('replanForm').addEventListener('submit',submitReplan);
  $('weekSelect').addEventListener('change',(event)=>{selectedWeek=event.target.value;renderPlan(appState.tasks);});
  $('todoList').addEventListener('change',(event)=>{
    if(event.target.matches('[data-task-id]')) toggleTask(event.target);
    if(event.target.matches('[data-upload-id]')) uploadPhoto(event.target);
  });
  $('completedWins').addEventListener('change',(event)=>{
    if(event.target.matches('[data-task-id]')) toggleTask(event.target);
    if(event.target.matches('[data-upload-id]')) uploadPhoto(event.target);
  });
}
function showCareerBridge(response, requestedCareer) {
  if (!requestedCareer) return;
  const exact = Object.keys(response.catalog).find(name => name.toLowerCase() === requestedCareer.toLowerCase());
  const known = {
    'Software Developers': 'Software Developer',
    'Information Security Analysts': 'Cybersecurity Analyst'
  };
  const selected = exact || known[requestedCareer] || null;
  const note = $('careerBridgeNote');
  note.replaceChildren();
  note.hidden = false;

  if (!selected) {
    const text = document.createElement('p');
    text.textContent = `Your assessment selected “${requestedCareer}.” There is no matching example skill template yet.`;
    note.append(text);
    if (response.profile) {
      const saved = document.createElement('p');
      saved.textContent = `Your saved ${response.profile.target_career} pathway is unchanged.`;
      note.append(saved);
    } else {
      const guidance = document.createElement('p');
      guidance.textContent = 'Choose from the available example pathways; they are not verified roadmaps for this occupation.';
      note.append(guidance);
    }
    return;
  }

  if (response.profile) {
    if (response.profile.target_career === selected) {
      note.textContent = `Career selected from your assessment: ${requestedCareer}. Your saved pathway already matches ${selected}.`;
      return;
    }
    const message = document.createElement('p');
    message.textContent = `Your assessment selected ${requestedCareer}; your saved pathway is ${response.profile.target_career}. Your current plan stays unchanged unless you choose to review the new career.`;
    const actions = document.createElement('div');
    actions.className = 'dev-bridge-actions';
    const keep = document.createElement('button');
    keep.type = 'button';
    keep.className = 'btn btn-ghost';
    keep.textContent = 'Keep my saved pathway';
    keep.addEventListener('click', () => { note.hidden = true; });
    const review = document.createElement('button');
    review.type = 'button';
    review.className = 'btn btn-primary';
    review.textContent = `Review ${selected} skills`;
    review.addEventListener('click', () => {
      $('editProfile').click();
      $('targetCareer').value = selected;
      drawSkillInputs();
      $('questionnaire').scrollIntoView({behavior:'smooth'});
      note.hidden = true;
    });
    actions.append(keep, review);
    note.append(message, actions);
    return;
  }

  $('targetCareer').value = selected;
  drawSkillInputs();
  note.textContent = `Career selected from your assessment: ${requestedCareer}. Skills use the illustrative ${selected} template; assess your own skills before generating a plan.`;
}

function openInventoryScreen(screen) {
  if (!screen || !/^S(0[1-9]|1[0-9]|2[0-2])$/.test(screen)) return;
  if (screen === 'S18') {
    $('questionnaire').hidden = false;
    toast('Development sample: simulated server failure while loading the learning profile.', true);
    return;
  }
  if (screen === 'S19') {
    const overlay = document.createElement('div');
    overlay.className = 'dev-loading-overlay';
    overlay.setAttribute('role', 'status');
    const panel = document.createElement('div');
    panel.className = 'dev-loading-panel';
    panel.innerHTML = '<span class="dev-spinner" aria-hidden="true"></span><strong>Loading your learning space…</strong><p>This is a simulated loading state for visual review.</p>';
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'btn btn-primary';
    close.textContent = 'Finish loading sample';
    close.addEventListener('click', () => overlay.remove());
    panel.append(close);
    overlay.append(panel);
    document.body.append(overlay);
    return;
  }
  if (screen === 'S07' || screen === 'S08') {
    setSteps(screen === 'S07' ? 1 : 2);
    $('questionnaire').scrollIntoView({block:'start'});
    return;
  }
  if (screen === 'S09') {
    fillForm(appState.profile);
    setSteps(0);
    $('dashboard').hidden = true;
    document.body.classList.remove('has-dashboard');
    $('questionnaire').hidden = false;
    $('cancelEdit').hidden = false;
    $('questionnaire').scrollIntoView({block:'start'});
    return;
  }
  if (['S10','S11','S12','S13','S14','S15','S16','S17'].includes(screen)) {
    const anchors = {
      S10: 'dashboard', S11: 'pathwaySection', S12: 'treeEmoji',
      S13: 'replanForm', S14: 'completedWins', S15: 'careerBridgeNote',
      S16: 'pathwaySection', S17: 'gapsSection'
    };
    $(anchors[screen])?.scrollIntoView({block:'start'});
  }
}
async function init() {
  initThemePreference();
  initListeners();
  showDemoBanner();
  if (pageParams.get('screen') === 'S18') {
    $('questionnaire').hidden = false;
    toast('Development sample: simulated server failure while loading the learning profile.', true);
    return;
  }
  try {
    const response=await api('/api/state');
    csrf = response.csrf;


    const targetSelect = $('targetCareer');
    const searchInput = $('careerSearch');
    const careerCount = $('careerCount');

    // Load and sort all careers A-Z
    const allCareers = Object.keys(response.catalog).sort(
        (a, b) => a.localeCompare(b, 'en', {
            sensitivity: 'base'
        })
    );

    let selectedCareer = "";

    // Render matching career options
    function renderCareerOptions(keyword = "") {
        const matches = allCareers.filter(name =>
            name.toLowerCase().includes(
                keyword.trim().toLowerCase()
            )
        );

        targetSelect.replaceChildren();

        matches.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            targetSelect.appendChild(option);
        });

        // Keep existing selection if it is still visible
        if (selectedCareer && matches.includes(selectedCareer)) {
            targetSelect.value = selectedCareer;
        } else {
            targetSelect.selectedIndex = -1;
        }

        targetSelect.style.display =
            matches.length > 0 ? 'block' : 'none';

        careerCount.textContent =
            `${matches.length} matching / ${allCareers.length} careers`;
    }

    // Confirm the selected career
    function confirmCareer() {
        const career = targetSelect.value;

        if (!career) return;

        selectedCareer = career;
        searchInput.value = career;

        // Restore all options so saved profiles still work
        renderCareerOptions("");
        targetSelect.value = career;

        // Hide the list after selection
        targetSelect.style.display = 'none';

        careerCount.textContent =
            `Selected: ${career} · ${allCareers.length} careers`;
    }

    // Populate options, but hide initially
    renderCareerOptions("");
    targetSelect.style.display = 'none';

    // Show options when user focuses the search field
    searchInput.addEventListener('focus', () => {
        const keyword =
            searchInput.value === selectedCareer
                ? ""
                : searchInput.value;

        renderCareerOptions(keyword);
        searchInput.select();
    });

    // Filter while typing
    searchInput.addEventListener('input', () => {
        renderCareerOptions(searchInput.value);
    });

    // Confirm using mouse or keyboard selection
    targetSelect.addEventListener('change', confirmCareer);

    showApp(response);
    showCareerBridge(response, pageParams.get('career'));

    // Synchronize the selected career
    selectedCareer = targetSelect.value;
    searchInput.value = selectedCareer;
    targetSelect.style.display = 'none';

    updateSdgNavLink();
    openInventoryScreen(pageParams.get('screen'));

  } catch(error) {
    $('questionnaire').hidden=false;
    toast(`Cannot reach the Python server: ${error.message}`,true);
  }
}
init();
