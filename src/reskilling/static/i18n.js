/* Reskilling translation layer. English source text is retained as stable canonical values.
   UI labels translate; generated narratives and arbitrary career data need separate localized sources. */
(() => {
  "use strict";
  const DICT = {"en":{"Overview":"Overview","My Reskilling Plan":"My Reskilling Plan","Progress Tracking":"Progress Tracking","Edit learning profile":"Edit learning profile","CAREER PREPARATION":"CAREER PREPARATION","Interview practice":"Interview practice","YOUR WORKSPACE":"YOUR WORKSPACE","Choose a target":"Choose a target","Step 1 of 3 · not saved":"Step 1 of 3 · not saved","1 · About you":"1 · About you","2 · Your skills":"2 · Your skills","3 · Your schedule":"3 · Your schedule","About you":"About you","Your skills":"Your skills","Your schedule":"Your schedule","← Career Assessment":"← Career Assessment","PERSONALISED RESKILLING STUDIO":"PERSONALISED RESKILLING STUDIO","01 — GETTING TO KNOW YOU":"01 — GETTING TO KNOW YOU","Build your learning profile":"Build your learning profile","About 2–3 minutes":"About 2–3 minutes","Which best describes you?":"Which best describes you?","Student / fresh graduate":"Student / fresh graduate","Currently employed":"Currently employed","Planning a career change":"Planning a career change","Returning to work or learning":"Returning to work or learning","Your current industry or community":"Your current industry or community","optional":"optional","Your general experience":"Your general experience","Beginner":"Beginner","Some practical experience":"Some practical experience","Experienced learner":"Experienced learner","Your target career":"Your target career","What would you like to achieve?":"What would you like to achieve?","Continue →":"Continue →","← Back":"← Back","✦ Generate my pathway":"✦ Generate my pathway","Rate each skill from":"Rate each skill from","How many hours can you study per week?":"How many hours can you study per week?","How many weeks do you want to plan?":"How many weeks do you want to plan?","Which days work best for you?":"Which days work best for you?","How do you like to learn?":"How do you like to learn?","Hands-on projects":"Hands-on projects","Video tutorials + practice":"Video tutorials + practice","Reading + practice":"Reading + practice","Data Analyst":"Data Analyst","Software Developer":"Software Developer","Cybersecurity Analyst":"Cybersecurity Analyst","UI/UX Designer":"UI/UX Designer","Digital Marketing Specialist":"Digital Marketing Specialist","Set up your learning profile to create a plan.":"Set up your learning profile to create a plan.","← Explore careers":"← Explore careers","MY LEARNING PATHWAY":"MY LEARNING PATHWAY","Make room for your next skill.":"Make room for your next skill.","Get started":"Get started","Next unfinished learning activity":"Next unfinished learning activity","Open my plan":"Open my plan","Study hours completed":"Study hours completed","Tasks completed":"Tasks completed","Your weekly learning time":"Your weekly learning time","Growth points":"Growth points","Saved target":"Saved target","HOW IT WORKS":"HOW IT WORKS","Why these tasks?":"Why these tasks?","Monday":"Monday","Tuesday":"Tuesday","Wednesday":"Wednesday","Thursday":"Thursday","Friday":"Friday","Saturday":"Saturday","Sunday":"Sunday","e.g. Education, Retail, Technology":"e.g. Education, Retail, Technology","e.g. Build my first data analysis portfolio project":"e.g. Build my first data analysis portfolio project"},"zh":{"Overview":"概览","My Reskilling Plan":"我的技能提升计划","Progress Tracking":"学习进度追踪","Edit learning profile":"编辑学习资料","CAREER PREPARATION":"职业准备","Interview practice":"面试练习","YOUR WORKSPACE":"你的工作空间","Choose a target":"选择目标职业","Step 1 of 3 · not saved":"第 1 步，共 3 步 · 尚未保存","1 · About you":"1 · 关于你","2 · Your skills":"2 · 你的技能","3 · Your schedule":"3 · 你的安排","About you":"关于你","Your skills":"你的技能","Your schedule":"你的安排","← Career Assessment":"← 职业测评","PERSONALISED RESKILLING STUDIO":"个性化技能提升空间","01 — GETTING TO KNOW YOU":"01 — 了解你","Build your learning profile":"建立学习档案","About 2–3 minutes":"约需 2–3 分钟","Which best describes you?":"以下哪项最符合你的情况？","Student / fresh graduate":"学生 / 应届毕业生","Currently employed":"目前在职","Planning a career change":"计划转行","Returning to work or learning":"重返工作或学习","Your current industry or community":"你目前的行业或领域","optional":"选填","Your general experience":"你的总体经验","Beginner":"初学者","Some practical experience":"有一些实践经验","Experienced learner":"有经验的学习者","Your target career":"你的目标职业","What would you like to achieve?":"你希望实现什么目标？","Continue →":"继续 →","← Back":"← 返回","✦ Generate my pathway":"✦ 生成我的学习路线","Rate each skill from":"请为每项技能评分，从","How many hours can you study per week?":"你每周能学习多少小时？","How many weeks do you want to plan?":"你想规划多少周？","Which days work best for you?":"哪几天最适合你学习？","How do you like to learn?":"你喜欢怎样学习？","Hands-on projects":"动手实践项目","Video tutorials + practice":"视频教程 + 练习","Reading + practice":"阅读 + 练习","Data Analyst":"数据分析师","Software Developer":"软件开发人员","Cybersecurity Analyst":"网络安全分析师","UI/UX Designer":"UI/UX 设计师","Digital Marketing Specialist":"数字营销专员","Set up your learning profile to create a plan.":"设置你的学习档案以创建计划。","← Explore careers":"← 探索职业","MY LEARNING PATHWAY":"我的学习路线","Make room for your next skill.":"为下一项技能做好准备。","Get started":"开始使用","Next unfinished learning activity":"下一项未完成的学习任务","Open my plan":"打开我的计划","Study hours completed":"已完成学习小时数","Tasks completed":"已完成任务","Your weekly learning time":"每周学习时间","Growth points":"成长积分","Saved target":"已保存的目标","HOW IT WORKS":"运作原理","Why these tasks?":"为什么安排这些任务？","Monday":"星期一","Tuesday":"星期二","Wednesday":"星期三","Thursday":"星期四","Friday":"星期五","Saturday":"星期六","Sunday":"星期日","e.g. Education, Retail, Technology":"例如：教育、零售、科技","e.g. Build my first data analysis portfolio project":"例如：完成我的第一个数据分析作品集项目"},"ms":{"Overview":"Gambaran Keseluruhan","My Reskilling Plan":"Pelan Peningkatan Kemahiran Saya","Progress Tracking":"Penjejakan Kemajuan","Edit learning profile":"Edit Profil Pembelajaran","CAREER PREPARATION":"PERSEDIAAN KERJAYA","Interview practice":"Latihan Temu Duga","YOUR WORKSPACE":"RUANG KERJA ANDA","Choose a target":"Pilih kerjaya sasaran","Step 1 of 3 · not saved":"Langkah 1 daripada 3 · belum disimpan","1 · About you":"1 · Tentang anda","2 · Your skills":"2 · Kemahiran anda","3 · Your schedule":"3 · Jadual anda","About you":"Tentang anda","Your skills":"Kemahiran anda","Your schedule":"Jadual anda","← Career Assessment":"← Penilaian Kerjaya","PERSONALISED RESKILLING STUDIO":"STUDIO PENINGKATAN KEMAHIRAN PERIBADI","01 — GETTING TO KNOW YOU":"01 — MENGENALI ANDA","Build your learning profile":"Bina profil pembelajaran anda","About 2–3 minutes":"Kira-kira 2–3 minit","Which best describes you?":"Yang manakah paling menggambarkan anda?","Student / fresh graduate":"Pelajar / graduan baharu","Currently employed":"Sedang bekerja","Planning a career change":"Merancang pertukaran kerjaya","Returning to work or learning":"Kembali bekerja atau belajar","Your current industry or community":"Industri atau bidang semasa anda","optional":"pilihan","Your general experience":"Pengalaman umum anda","Beginner":"Pemula","Some practical experience":"Sedikit pengalaman praktikal","Experienced learner":"Pelajar berpengalaman","Your target career":"Kerjaya sasaran anda","What would you like to achieve?":"Apakah yang ingin anda capai?","Continue →":"Teruskan →","← Back":"← Kembali","✦ Generate my pathway":"✦ Jana laluan pembelajaran saya","Rate each skill from":"Nilai setiap kemahiran daripada","How many hours can you study per week?":"Berapa jam anda boleh belajar setiap minggu?","How many weeks do you want to plan?":"Berapa minggu anda mahu rancang?","Which days work best for you?":"Hari manakah paling sesuai untuk anda?","How do you like to learn?":"Bagaimanakah anda suka belajar?","Hands-on projects":"Projek praktikal","Video tutorials + practice":"Tutorial video + latihan","Reading + practice":"Membaca + latihan","Data Analyst":"Penganalisis Data","Software Developer":"Pembangun Perisian","Cybersecurity Analyst":"Penganalisis Keselamatan Siber","UI/UX Designer":"Pereka UI/UX","Digital Marketing Specialist":"Pakar Pemasaran Digital","Set up your learning profile to create a plan.":"Sediakan profil pembelajaran anda untuk membuat pelan.","← Explore careers":"← Terokai kerjaya","MY LEARNING PATHWAY":"LALUAN PEMBELAJARAN SAYA","Make room for your next skill.":"Berikan ruang untuk kemahiran seterusnya.","Get started":"Mulakan","Next unfinished learning activity":"Aktiviti pembelajaran seterusnya yang belum selesai","Open my plan":"Buka pelan saya","Study hours completed":"Jam belajar yang diselesaikan","Tasks completed":"Tugasan yang diselesaikan","Your weekly learning time":"Masa belajar mingguan anda","Growth points":"Mata perkembangan","Saved target":"Sasaran disimpan","HOW IT WORKS":"CARA IA BERFUNGSI","Why these tasks?":"Mengapa tugasan ini?","Monday":"Isnin","Tuesday":"Selasa","Wednesday":"Rabu","Thursday":"Khamis","Friday":"Jumaat","Saturday":"Sabtu","Sunday":"Ahad","e.g. Education, Retail, Technology":"cth. Pendidikan, Peruncitan, Teknologi","e.g. Build my first data analysis portfolio project":"cth. Bina projek portfolio analisis data pertama saya"}};
  const storageKey = "futureskill_language";
  const originalText = new WeakMap();
  const originalAttrs = new WeakMap();
  let language = ["en","zh","ms"].includes(localStorage.getItem(storageKey)) ? localStorage.getItem(storageKey) : "en";
  let scheduled = false;
  function localized(source) {
    const trim = source.trim();
    const value = (DICT[language] || {})[trim];
    if (!value) return source;
    return source.replace(trim, value);
  }
  function update() {
    scheduled = false;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      if (!parent || parent.closest("script,style,textarea,[data-i18n-ignore]")) continue;
      const original = originalText.has(node) ? originalText.get(node) : node.nodeValue;
      if (!originalText.has(node)) originalText.set(node, original);
      const desired = localized(original);
      if (node.nodeValue !== desired) node.nodeValue = desired;
    }
    document.querySelectorAll("[placeholder],[title]").forEach(el => {
      const saved = originalAttrs.get(el) || {};
      const current = {...saved};
      for (const attr of ["placeholder","title"]) {
        if (!el.hasAttribute(attr)) continue;
        if (current[attr] === undefined) current[attr] = el.getAttribute(attr);
        const desired = localized(current[attr]);
        if (el.getAttribute(attr) !== desired) el.setAttribute(attr, desired);
      }
      originalAttrs.set(el,current);
    });
    document.documentElement.lang = language === "zh" ? "zh-CN" : language;
    const select = document.getElementById("reskilling-language-select");
    if(select) select.value = language;
  }
  function schedule() {
    if(scheduled) return;
    scheduled = true;
    requestAnimationFrame(update);
  }
  function setLanguage(lang) {
    if(!DICT[lang]) return;
    language = lang;
    localStorage.setItem(storageKey,lang);
    schedule();
  }
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("reskilling-language-select")?.addEventListener("change",e=>setLanguage(e.target.value));
    const observer = new MutationObserver(schedule);
    observer.observe(document.body,{childList:true,subtree:true,characterData:true});
    schedule();
  });
  document.addEventListener("futureskill:languagechange",e=>setLanguage(e.detail.lang));
  window.FutureSkillReskillingI18n = {setLanguage,getLanguage:()=>language};
})();