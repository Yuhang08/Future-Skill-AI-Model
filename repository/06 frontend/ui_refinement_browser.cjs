/* Isolated Chromium UI matrix. No real learner records are changed.
 * UI_CAPTURE_PHASE=before node --experimental-websocket tests/ui_refinement_browser.cjs
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const {spawn} = require("node:child_process");
const base = process.env.REPORT_TEST_BASE_URL || `https://${process.env.REPLIT_DEV_DOMAIN}`;
const phase = process.env.UI_CAPTURE_PHASE || "after";
const out = "generated-artifacts/ui-refinement";
fs.mkdirSync(out, {recursive:true});
const profile = fs.mkdtempSync(path.join(os.tmpdir(),"future-ui-"));
const browser = spawn("chromium", ["--headless","--no-sandbox","--disable-dev-shm-usage","--no-first-run","--remote-debugging-port=0",`--user-data-dir=${profile}`,"about:blank"],{stdio:"ignore"});
const pause = ms => new Promise(r=>setTimeout(r,ms));
let socket, sequence=0;
const pending=new Map(), errors=[], missing=[];
function send(method,params={}) {
  const id=++sequence;
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(id);reject(Error(method));},25000);
    pending.set(id,{resolve,reject,timer}); socket.send(JSON.stringify({id,method,params}));
  });
}
async function run(expression) {
  const result=await send("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true,userGesture:true});
  if(result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function wait(expression) {
  for(let n=0;n<180;n++){if(await run(expression))return;await pause(100);}
  throw Error(`Timeout: ${expression}`);
}
async function go(route,ready) {
  await send("Page.navigate",{url:base+route});
  await wait("document.readyState==='complete'");
  if(ready)await wait(ready);
  await pause(150);
}
async function capture(name) {
  await run("window.scrollTo({top:0,behavior:'instant'})");
  const image=await send("Page.captureScreenshot",{format:"jpeg",quality:80});
  fs.writeFileSync(`${out}/${phase}-${name}.jpg`,Buffer.from(image.data,"base64"));
}
async function overflow(label) {
  const sizes=await run("({w:innerWidth,s:document.documentElement.scrollWidth})");
  assert.ok(sizes.s<=sizes.w+2,`${label}: horizontal overflow ${JSON.stringify(sizes)}`);
}
async function contrast(label) {
  const failures = await run(`(() => {
    const luminance = value => {
      const c=value.match(/[\\d.]+/g).slice(0,3).map(Number).map(n=>{n/=255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4;});
      return c[0]*.2126+c[1]*.7152+c[2]*.0722;
    };
    return [...document.querySelectorAll('.career-option-title,.career-page-heading,.career-pathway-status,.career-card-actions a,.career-card-controls summary,.career-rank,.report-structured-summary,#workspaceSummary,#nextActivityCard h2,#nextActivityDetail')]
      .filter(n=>n.getClientRects().length).map(n=>{
        let p=n,bg;
        while(p){bg=getComputedStyle(p).backgroundColor;if(bg!=='rgba(0, 0, 0, 0)'&&bg!=='transparent')break;p=p.parentElement;}
        const a=luminance(getComputedStyle(n).color),b=luminance(bg);
        return {text:n.textContent.slice(0,50),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
      }).filter(item=>item.ratio<4.5);
  })()`);
  assert.deepEqual(failures,[],`${label}: key text contrast >=4.5:1`);
}
const payload={
  answers:Object.fromEntries(["R","I","A","S","E","C"].map((k,i)=>[k,Array(4).fill([2,5,3,4,2,1][i])])),
  subject_answers:Object.fromEntries(["IT","Math","Education","Health","Business","Engineering"].map((k,i)=>[k,Array(2).fill([5,4,3,2,1,4][i])])),
  skill_answers:Object.fromEntries(["MathSkill","CodingSkill","DataSkill","CommunicationSkill","LeadershipSkill","CreativeSkill"].map((k,i)=>[k,[2,5,4,3,1,4][i]]))
};
(async()=>{
  try {
    const active=path.join(profile,"DevToolsActivePort");
    for(let n=0;!fs.existsSync(active);n++){assert.ok(n<150);await pause(100);}
    const port=fs.readFileSync(active,"utf8").split("\n")[0];
    const target=await(await fetch(`http://127.0.0.1:${port}/json/new?about:blank`,{method:"PUT"})).json();
    socket=new WebSocket(target.webSocketDebuggerUrl);
    socket.addEventListener("message",event=>{
      const message=JSON.parse(event.data);
      if(message.method==="Runtime.exceptionThrown")errors.push(message.params.exceptionDetails.text);
      if(message.method==="Network.responseReceived"&&message.params.response.status>=400)missing.push(message.params.response.url);
      if(message.id&&pending.has(message.id)){const p=pending.get(message.id);pending.delete(message.id);clearTimeout(p.timer);message.error?p.reject(Error(JSON.stringify(message.error))):p.resolve(message.result);}
    });
    await new Promise(resolve=>socket.addEventListener("open",resolve,{once:true}));
    await send("Page.enable");await send("Runtime.enable");await send("Network.enable");
    await send("Emulation.setFocusEmulationEnabled",{enabled:true});
    await send("Emulation.setDeviceMetricsOverride",{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
    await go("/career-overview","!!window.FutureSkillReport");
    const seeded=await run(`(async()=>{const answers=${JSON.stringify(payload)};const response=await fetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(answers)});if(!response.ok)throw Error(await response.text());const data=await response.json();sessionStorage.setItem('futureskill-career-context',JSON.stringify({data,answers}));return data.recommendations.map(c=>[c.id,c.match_index]);})()`);
    assert.ok(seeded.length>2);
    const routes=[
      ["overview","/career-overview","!!document.querySelector('.career-result-card')"],
      ["results","/?report-demo=differentiated","!!document.querySelector('#careerResults .career-result-card') && !document.querySelector('#reportDemoScenario').disabled"],
      ["catalogue","/careers","!!document.querySelector('.career-catalog-item')"],
      ["profile","/my-profile","!!document.querySelector('#report-interests')"],
      ["detail","/career/15-1252.00","!!document.querySelector('.career-detail-bars') || document.querySelector('#careerWorkspaceContent').textContent.includes('Software Developers')"],
      ["setup","/reskilling?demo=1&demo_scenario=fresh","!!document.querySelector('#targetCareer option')"],
      ["saved-plan","/__dev/demo/open?demo=1&demo_scenario=dashboard&scenario=dashboard&screen=S10","!!document.querySelector('#dashboard:not([hidden])')"]
    ];
    for(const [name,route,ready]of routes) {
      await go(route,ready);
      await capture(name);
      if(phase==="before")continue;
      for(const theme of ["light","dark"]) {
        await run(`FutureSkillTheme.setPreference('${theme}',false)`);
        for(const width of [390,768,1440]) {
          await send("Emulation.setDeviceMetricsOverride",{width,height:1000,deviceScaleFactor:1,mobile:width<700});
          await pause(100);await overflow(`${name} ${theme} ${width}`);await contrast(`${name} ${theme} ${width}`);
          await capture(`${name}-${theme}-${width}`);
        }
      }
      // A 720 CSS-pixel viewport emulates layout/reflow at 200% browser zoom on a 1440px screen.
      await send("Emulation.setDeviceMetricsOverride",{width:720,height:500,deviceScaleFactor:2,mobile:false});
      await overflow(`${name} 200%-equivalent reflow`);
      await send("Emulation.setDeviceMetricsOverride",{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
      if(name==="overview") {
        assert.ok(await run("document.querySelector('.career-observations strong')!==null"));
        assert.ok(await run("parseFloat(getComputedStyle(document.querySelector('.career-option-title')).fontSize)>=22"));
        assert.equal(await run("[...document.querySelectorAll('.career-result-card')].some(c=>c.querySelector('details[open]'))"),false);
        for(const label of ["Why this match?","Sources","Limitations"]) {
          assert.ok(await run(`(()=>{const s=[...document.querySelectorAll('.career-result-card summary')].find(n=>n.textContent==='${label}');if(!s)return false;s.focus();return document.activeElement===s;})()`));
          await send("Input.dispatchKeyEvent",{type:"keyDown",key:"Enter",code:"Enter",windowsVirtualKeyCode:13,text:"\r"});
          await send("Input.dispatchKeyEvent",{type:"keyUp",key:"Enter",code:"Enter",windowsVirtualKeyCode:13});
          assert.ok(await run(`(()=>{const s=[...document.querySelectorAll('.career-result-card summary')].find(n=>n.textContent==='${label}');return s.parentElement.open;})()`));
          await run(`[...document.querySelectorAll('.career-result-card summary')].find(n=>n.textContent==='${label}').click()`);
        }
        assert.deepEqual(await run("[...document.querySelectorAll('.career-result-card')].map(c=>[c.dataset.careerId,Number(c.querySelector('.career-index-list dd:last-child').textContent)])"),seeded);
      }
      if(name==="profile") {
        assert.equal(await run("document.querySelectorAll('#careerResults').length"),0);
        assert.equal(await run("document.querySelectorAll('[role=meter]').length"),18);
        await run("FutureSkillI18n.setLanguage('zh-CN')");
        await wait("document.documentElement.lang==='zh-CN'");
        assert.ok(await run("document.querySelector('.report-summary strong').textContent!=='Investigative'"));
        await run("FutureSkillI18n.setLanguage('ms')");
        await wait("document.documentElement.lang==='ms'");
        await run("FutureSkillI18n.setLanguage('en')");
        await wait("document.documentElement.lang==='en'");
        assert.equal(await run("document.querySelector('.report-summary strong').textContent"),"Investigative");
      }
      if(name==="setup") {
        assert.ok(await run("!!document.querySelector('#workspaceSetupSteps:not([hidden])')"));
        await run("document.querySelector('#nextStep').click()");
        assert.ok(await run("!document.querySelector('#workspaceSetupSteps [data-go-step=\"0\"] .setup-step-complete').hidden"));
        await run("document.querySelector('#workspaceSetupSteps [data-go-step=\"1\"]').click()");
        assert.equal(await run("document.querySelector('#workspaceSetupSteps [aria-current=step]').dataset.goStep"),"1");
        await run("document.querySelector('#nextStep').click()");
        assert.ok(await run("!document.querySelector('#workspaceSetupSteps [data-go-step=\"1\"] .setup-step-complete').hidden"));
        await run("document.querySelector('#targetCareer').selectedIndex=1;document.querySelector('#targetCareer').dispatchEvent(new Event('change',{bubbles:true}))");
        assert.ok(await run("document.querySelector('#workspaceSetupSteps [data-go-step=\"1\"] .setup-step-complete').hidden"));
      }
      if(name==="saved-plan") {
        assert.ok(await run("document.querySelector('#workspaceTarget').textContent!=='Choose a target'"));
        assert.ok(await run("document.querySelector('#hero').hidden"));
        assert.ok(await run("!document.querySelector('#nextActivityCard').hidden && !!document.querySelector('#nextActivityDetail').textContent"));
      }
      console.log(`PASS ${name}: desktop/tablet/mobile, themes, zoom-equivalent reflow, interactions`);
    }
    if(phase!=="before"){
      const storedContext = await run("sessionStorage.getItem('futureskill-career-context')");
      for(const view of ["overview","profile"]) {
        await go(`/__dev/career-preview?view=${view}&profile=equal-high`,"!!document.querySelector('.career-demo-banner') && !document.querySelector('.career-loading')");
        assert.equal(await run("sessionStorage.getItem('futureskill-career-context')"),storedContext);
        assert.match(await run("document.querySelector('.report-structured-summary').textContent"),/do not identify a clear leading interest area/);
      }
      await go("/__dev/career-preview?view=overview&profile=mixed","!!document.querySelector('.career-match-reasons')");
      assert.match(await run("document.querySelector('.career-match-reasons').textContent"),/No subject tags detected from title/);
      assert.doesNotMatch(await run("document.querySelector('.career-match-reasons').textContent"),/Unclassified/);
      await go("/careers?q=Software","!!document.querySelector('.career-catalog-item')");
      assert.ok(await run("[...document.querySelectorAll('.career-catalog-item')].find(c=>c.querySelector('h3').textContent==='Software Developers').textContent.includes('Example pathway available')"));
      await run("document.querySelector('#careerSearch').value='zzzz-nonexistent-career';document.querySelector('.career-search-form').requestSubmit()");
      await wait("document.querySelector('.career-status').textContent.includes('No catalogue entries')");
      assert.equal(await run("document.querySelectorAll('.career-catalog-item').length"),0);
      await run("document.querySelector('.career-search-suggestions button').click()");
      await wait("document.querySelector('.career-status').textContent.includes('shown.')");
      assert.ok(await run("document.querySelectorAll('.career-catalog-item').length>0"));
      await run("window.realFetch=window.fetch;window.fetch=(url,options)=>String(url).startsWith('/api/careers?')?Promise.resolve(new Response(JSON.stringify({detail:'Temporary catalogue failure'}),{status:503,headers:{'Content-Type':'application/json'}})):window.realFetch(url,options);document.querySelector('.career-search-form').requestSubmit()");
      await wait("document.querySelector('.career-status').classList.contains('career-error')");
      assert.match(await run("document.querySelector('.career-status').textContent"),/Temporary catalogue failure/);
      await run("window.fetch=window.realFetch;document.querySelector('.career-search-form').requestSubmit()");
      await wait("document.querySelector('.career-status').textContent.includes('shown.')");
      assert.equal(await run("document.querySelector('.career-status').classList.contains('career-error')"),false);
      await go("/reskilling?demo=1&demo_scenario=dashboard&career=Software%20Developers","!!document.querySelector('#careerBridgeNote:not([hidden])')");
      assert.equal(await run("document.querySelector('#workspaceTarget').textContent"),"Data Analyst");
      assert.match(await run("document.querySelector('#careerBridgeNote').textContent"),/stays unchanged/);
      assert.equal(await run("appState.profile.target_career"),"Data Analyst");
      await go("/__dev/brand","!!document.querySelector('main')");
      await capture("brand");
      assert.equal(await run("document.querySelectorAll('.brand-direction').length"),3);
      assert.deepEqual(errors,[],"no browser exceptions");
      assert.deepEqual(missing,[],"no failed requests");
    }
    console.log(`${phase}: captures saved to ${out}`);
  } finally {
    socket?.close();browser.kill("SIGTERM");
    await pause(500);fs.rmSync(profile,{recursive:true,force:true,maxRetries:4,retryDelay:200});
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
