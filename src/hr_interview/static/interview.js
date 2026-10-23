const $ = (id) => document.getElementById(id);
let sessionId = null;
let mediaRecorder = null;
let mediaStream = null;
let chunks = [];
let recording = false;
let currentQuestion = "";
let answerMode = "text";
function updateAnswerCount() {
  const t = $("answer").value;
  const words = t.trim() ? t.trim().split(/\s+/).length : 0;
  $("answerCount").textContent = `${words} words · ${t.length}/7000 characters`;
}
function setAnswerMode(mode) {
  if (recording) { error("Stop recording before switching answer methods."); return; }
  answerMode = mode;
  $("textMode").setAttribute("aria-pressed", String(mode === "text"));
  $("voiceMode").setAttribute("aria-pressed", String(mode === "voice"));
  $("textPanel").classList.toggle("hidden", mode !== "text");
  $("voicePanel").classList.toggle("hidden", mode !== "voice");
  $("answer").placeholder = mode === "text"
    ? "Type your answer here. Describe your reasoning and include relevant examples..."
    : "Your voice transcript will appear here. You can correct it before submitting...";
}
$("textMode").addEventListener("click", () => setAnswerMode("text"));
$("voiceMode").addEventListener("click", () => setAnswerMode("voice"));
$("answer").addEventListener("input", updateAnswerCount);


function show(which) {
  for (const id of ["setup", "interview", "report", "historyPage"]) $(id).classList.toggle("hidden", id !== which);
}
function error(message="") { $("error").textContent = message; }
function loading(btn, yes) { btn.disabled = yes; }
async function api(path, options={}) {
  const response = await fetch("/hr-interview" + path, options);
  let body;
  try { body = await response.json(); } catch { throw new Error("Server returned an unexpected response."); }
  if (!response.ok) throw new Error(body.error || "Something went wrong.");
  return body;
}
function jsonPost(path, obj) { return api(path, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(obj)}); }
function setQuestion(data) {
  currentQuestion = data.question;
  $("questionText").textContent = data.question;
  $("focusText").textContent = "Focus: " + (data.focus || "Interview practice");
  $("counter").textContent = `Question ${data.question_number} of ${data.max_questions || 5}`;
  $("answer").value = "";
  updateAnswerCount();
  $("feedbackBox").classList.add("hidden");
  $("submit").disabled = false;
  $("record").disabled = false;
}
function bars(scores, mount) {
  mount.replaceChildren();
  for (const [name, value] of Object.entries(scores)) {
    const row = document.createElement("div"); row.className = "barrow";
    const label = document.createElement("span"); label.textContent = name[0].toUpperCase() + name.slice(1);
    const bar = document.createElement("div"); bar.className = "bar";
    const fill = document.createElement("div"); fill.className = "fill"; fill.style.width = `${Math.max(0,Math.min(100,value))}%`;
    const num = document.createElement("span"); num.textContent = Math.round(value) + "%";
    bar.append(fill); row.append(label,bar,num);mount.append(row);
  }
}
function fillList(id, values) { $(id).replaceChildren(); for (const v of values) { const li=document.createElement("li");li.textContent=v;$(id).append(li); } }
$("start").addEventListener("click", async () => {
  error(); loading($("start"),true);
  try {
    const role=$("role").value, mode=$("mode").value, language=$("language").value;
    if (!role) throw new Error("Please select a career from the list.");
    const data=await jsonPost("/api/interview/start",{role,mode,language,question_count:Number($("questionCount").value)});
    sessionId=data.session_id;$("careerLabel").textContent=`${role} · ${mode}`;
    setQuestion(data);show("interview");
  } catch(e){error(e.message);} finally {loading($("start"),false);}
});
$("speak").addEventListener("click", () => {
  if (!("speechSynthesis" in window)) { error("Browser speech playback is unavailable."); return; }
  window.speechSynthesis.cancel();const msg=new SpeechSynthesisUtterance(currentQuestion);
  msg.lang=$("language").value==="中文"?"zh-CN":$("language").value==="Bahasa Melayu"?"ms-MY":"en-US";msg.rate=.95;window.speechSynthesis.speak(msg);
});
$("record").addEventListener("click", async () => {
  error();
  if (recording) {mediaRecorder.stop();return;}
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {error("Microphone recording not supported by this browser. You can type your answer.");return;}
  try {
    mediaStream=await navigator.mediaDevices.getUserMedia({audio:true});
    const candidates=["audio/webm;codecs=opus","audio/webm","audio/mp4","audio/ogg"];
    const mime=candidates.find(t=>MediaRecorder.isTypeSupported(t));
    if(!mime) throw new Error("No supported recording format. Please type your answer.");
    mediaRecorder=new MediaRecorder(mediaStream,{mimeType:mime});chunks=[];
    mediaRecorder.ondataavailable=(e)=>{if(e.data.size)chunks.push(e.data);};
    mediaRecorder.onstop=async()=>{
      recording=false;$("record").textContent="🎙 Start Recording";$("recordStatus").textContent="Transcribing...";
      mediaStream?.getTracks().forEach(t=>t.stop());
      const blob=new Blob(chunks,{type:mime});
      if(!blob.size){error("No audio captured.");$("recordStatus").textContent="";return;}
      if(blob.size>10*1024*1024){error("Audio too large (10 MB limit). Record a shorter answer.");$("recordStatus").textContent="";return;}
      $("record").disabled=true;
      try {
        const form=new FormData();form.append("session_id",sessionId);form.append("audio",blob,"answer."+(mime.includes("mp4")?"mp4":mime.includes("ogg")?"ogg":"webm"));
        const data=await api("/api/interview/transcribe",{method:"POST",body:form});
        $("answer").value=($("answer").value.trim()+" "+data.transcript).trim();
        updateAnswerCount();
      } catch(e){error(e.message);}finally{$("record").disabled=false;$("recordStatus").textContent="";}
    };
    mediaRecorder.start(); recording=true; $("record").textContent="⏹ Stop Recording";$("recordStatus").textContent="Recording...";
  } catch(e){mediaStream?.getTracks().forEach(t=>t.stop());error(e.message);}
});
$("submit").addEventListener("click",async()=>{
  error();if(recording){error("Stop recording first.");return;}
  const answer=$("answer").value.trim();if(answer.length<3){error("Please enter a longer answer.");return;}
  loading($("submit"),true);
  try {
    const data=await jsonPost("/api/interview/feedback",{session_id:sessionId,answer});
    const f=data.feedback;$("totalScore").textContent=f.total+" / 100 · Practice score";
    $("summary").textContent=f.summary;bars(f.scores,$("dimensions"));
    fillList("strengths",f.strengths);fillList("improvements",f.improvements);
    $("example").textContent=f.example_answer;
    $("next").textContent=data.finished?"View final report →":"Next question →";
    $("feedbackBox").classList.remove("hidden");
  }catch(e){error(e.message);loading($("submit"),false);}
});
function presentReport(rep) {
  $("reportIntro").textContent=`${rep.role} · ${rep.questions_completed} question(s) completed`;
  $("finalScore").textContent=`${rep.overall} / 100 · Average practice score`;
  const readinessTitles={
    insufficient_evidence:"More answers needed", try_real_interviews:"Consider a real interview",
    practice_and_apply:"Practice and apply in parallel", focus_practice_first:"Focus on practice first"
  };
  $("readinessTitle").textContent=readinessTitles[rep.readiness.status] || "Practice assessment";
  $("readinessMessage").textContent=rep.readiness.message;
  $("evidenceInfo").textContent=`Based on ${rep.readiness.evidence_count} practice answer(s).`;
  $("proficiency").replaceChildren();
  rep.proficiency.forEach(p=>{
    const group=document.createElement("div");group.className="proficiencyItem";
    const line=document.createElement("div");line.className="proficiencyHeading";
    const label=document.createElement("strong");label.textContent=p.label;
    const level=document.createElement("span");level.textContent=`${p.level} · ${p.score}/100`;
    line.append(label,level);
    const bar=document.createElement("div");bar.className="bar";
    const fill=document.createElement("div");fill.className="fill";fill.style.width=`${Math.max(0,Math.min(100,p.score))}%`;
    bar.append(fill);group.append(line,bar);$("proficiency").append(group);
  });
  fillList("reportStrengths",rep.strengths_summary.map(s=>`${s.dimension} (${s.score}/100)${s.example?": "+s.example:""}`));
  fillList("reportWeaknesses",rep.weaknesses_summary.map(s=>`${s.dimension} (${s.score}/100): ${s.action}`));
  fillList("priorities",rep.practice_priorities.map(x=>`Focus your next practice on ${x}.`));
  $("reportDisclaimer").textContent=rep.disclaimer;
  $("history").replaceChildren();
  rep.history.forEach((item,i)=>{
    const div=document.createElement("div");div.className="historyItem";
    const title=document.createElement("strong");title.textContent=`Q${i+1}: ${item.question}`;
    const ans=document.createElement("p");ans.textContent=`Your answer: ${item.answer}`;
    const sc=document.createElement("p");sc.textContent=`Practice score: ${item.feedback.total}/100`;
    const improvement=document.createElement("p");improvement.textContent=`Improve: ${item.feedback.improvements.join(" · ")}`;
    div.append(title,ans,sc,improvement);$("history").append(div);
  });
  saveReportLocally(rep);
  sessionId=null;show("report");
}
$("next").addEventListener("click",async()=>{
  error();loading($("next"),true);
  try {const data=await jsonPost("/api/interview/next",{session_id:sessionId});
    if(data.finished)presentReport(data.report);else setQuestion(data);
  }catch(e){error(e.message);}finally{loading($("next"),false);}
});
$("finishEarly").addEventListener("click",async()=>{
  error();loading($("finishEarly"),true);
  try {const data=await jsonPost("/api/interview/end",{session_id:sessionId});presentReport(data.report);}
  catch(e){error(e.message);}finally{loading($("finishEarly"),false);}
});
$("restart").addEventListener("click",()=>{sessionId=null;error();show("setup");});

// Career selector: all CSV titles, sorted alphabetically, 7 visible rows, scrollable.
let availableCareers = [];
function renderCareers() {
  const search = $('careerSearch').value.trim().toLocaleLowerCase();
  const matching = availableCareers.filter(x=>x.toLocaleLowerCase().includes(search));
  $('careerCount').textContent = `${matching.length} matching · ${availableCareers.length} careers total`;
  const mount = $('careerOptions'); mount.replaceChildren();
  for (const name of matching) {
    const option = document.createElement('button');
    option.type = 'button'; option.className = 'career-option'; option.setAttribute('role','option');
    option.textContent = name;
    option.setAttribute('aria-selected',String(name === $('role').value));
    option.addEventListener('click',()=>{
      $('role').value=name;$('careerSearch').value=name;renderCareers();
      mount.classList.add('collapsed');$('careerSearch').setAttribute('aria-expanded','false');
    });
    mount.append(option);
  }
}
$('careerSearch').addEventListener('input',()=>{
  $('role').value='';$('careerOptions').classList.remove('collapsed');
  $('careerSearch').setAttribute('aria-expanded','true');renderCareers();
});
$('careerSearch').addEventListener('focus',()=>{
  $('careerOptions').classList.remove('collapsed');renderCareers();
});
(async()=>{
 try {
  const result=await api('/api/careers');
  availableCareers=result.careers.sort((a,b)=>a.localeCompare(b,'en',{sensitivity:'base'}));
  renderCareers();
  if(result.source==='careers_demo.csv')
    $('careerCount').textContent += ' · DEMO DATA: add career_profiles_clean.csv for full list';
 }catch(e){error('Unable to load career database: '+e.message);}
})();

// Browser-only history: reports remain on this device, with delete control.
const REPORT_KEY='futureskill_hr_reports_v2';
function readReports(){try{return JSON.parse(localStorage.getItem(REPORT_KEY)||'[]');}catch{return [];}}
function saveReportLocally(report){
 try {
  const records=readReports();
  records.push({id:crypto.randomUUID(),saved_at:new Date().toISOString(),report});
  localStorage.setItem(REPORT_KEY,JSON.stringify(records));
 }catch(e){console.warn('Could not save personal history',e);}
}
function openSavedHistory(){
 show('historyPage');
 const records=readReports().slice().reverse();
 $('historyCount').textContent=`${records.length} completed interviews saved in this browser`;
 const mount=$('savedInterviews');mount.replaceChildren();
 for(const entry of records){
  const card=document.createElement('article');card.className='historyItem';
  const heading=document.createElement('h3');heading.textContent=`${entry.report.role} · ${entry.report.overall}/100`;
  const date=document.createElement('p');date.textContent=new Date(entry.saved_at).toLocaleString();
  const readiness=document.createElement('p');readiness.textContent=entry.report.readiness?.message||'';
  const details=document.createElement('details');
  const sum=document.createElement('summary');sum.textContent='View questions and answers';details.append(sum);
  for (const [i,q] of (entry.report.history||[]).entries()) {
   const p=document.createElement('p');p.textContent=`Q${i+1}: ${q.question} | Answer: ${q.answer} | Score: ${q.feedback.total}`;
   details.append(p);
  }
  card.append(heading,date,readiness,details);mount.append(card);
 }
}
$('openHistory').addEventListener('click',openSavedHistory);
$('backHome').addEventListener('click',()=>show('setup'));
$('deleteHistory').addEventListener('click',()=>{
 if(confirm('Delete all interview reports saved in this browser?')){
  localStorage.removeItem(REPORT_KEY);openSavedHistory();
 }
});
