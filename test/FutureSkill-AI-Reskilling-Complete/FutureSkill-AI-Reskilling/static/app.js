/* FutureSkill AI: zero-library frontend for the Python stdlib backend. */
const DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (s) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
let appState = null;
let csrf = '';
let step = 0;
let selectedWeek = 'auto';
let toastTimer;

function toast(message, isError=false) {
  const node = $('toast');
  node.textContent = message;
  node.classList.toggle('error', isError);
  node.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove('visible'), 4200);
}
async function api(path, method='GET', data) {
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
function renderGaps(gaps) {
  const sorted = Object.entries(gaps).sort((a,b) => b[1].priority-a[1].priority);
  $('gapList').innerHTML = sorted.map(([name, g]) => {
    const hasGap = g.gap > 0;
    return `<div class="gap-item">
      <div class="gap-top"><strong>${escapeHtml(name)}</strong><span>${g.current}/5 current · ${g.required}/5 goal</span></div>
      <div class="gap-bar"><div class="gap-current" style="width:${g.current/5*100}%"></div><div class="gap-require" style="width:${Math.max(0,g.required-g.current)/5*100}%;left:${g.current/5*100}%;right:auto"></div></div>
      <div class="gap-footer"><span>${hasGap ? `Gap: ${g.gap.toFixed(0)} level${g.gap===1?'':'s'}` : '✓ Currently meets example target'}</span><b>${g.remaining_hours} h estimated practice left</b></div>
    </div>`;
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
  renderGaps(state.gaps);
  renderPlan(state.tasks);
  renderTree(state.tree, animateTree);
  $('replanHours').value = p.weekly_hours;
  $('replanWeeks').value = p.target_weeks;
  dayPills('replanDays','replanDays',p.preferred_days);
}
function showApp(state) {
  appState = state;
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
  $('weeklyHours').addEventListener('input',()=>{$('weeklyHoursOutput').textContent=`${$('weeklyHours').value} hours`;});
  $('targetCareer').addEventListener('change',()=>drawSkillInputs());
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
async function init() {
  initListeners();
  try {
    const response=await api('/api/state');
    csrf = response.csrf;
    const targetSelect=$('targetCareer');
    targetSelect.innerHTML = Object.entries(response.catalog).map(([name,career])=>
      `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('');
    showApp(response);
  } catch(error) {
    $('questionnaire').hidden=false;
    toast(`Cannot reach the Python server: ${error.message}`,true);
  }
}
init();
