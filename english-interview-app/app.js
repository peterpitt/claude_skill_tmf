/* ============================================================
 * 30 天 Google 面試英語衝刺 — 前端邏輯
 * 進度存於 localStorage，發音用 Web Speech API (SpeechSynthesis)，
 * 口說練習用 SpeechRecognition。純前端、離線可用。
 * ============================================================ */

const STORAGE_KEY = "eng_interview_sprint_v1";
const WEEK_THEMES = {
  1: "打底 — 開口說 + 自我介紹",
  2: "職場英語 + STAR 行為面試",
  3: "Google 技術 / 情境面試",
  4: "模擬面試 + 流利度衝刺",
};

// ---------- 狀態管理 ----------
function loadState() {
  try {
    const s = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (s && Array.isArray(s.done)) return s;
  } catch (e) {}
  return { done: [], currentDay: 1, lastStudy: null };
}
function saveState(s) { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }
let state = loadState();

// ---------- 語音合成（發音） ----------
let voices = [];
function loadVoices() { voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : []; }
if (window.speechSynthesis) {
  loadVoices();
  window.speechSynthesis.onvoiceschanged = loadVoices;
}
function speak(text, lang = "en-US") {
  if (!window.speechSynthesis) { toast("此瀏覽器不支援語音，建議用 Chrome / Edge"); return; }
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang;
  u.rate = 0.92;
  const v = voices.find(v => v.lang && v.lang.startsWith(lang.slice(0, 2)));
  if (v) u.voice = v;
  window.speechSynthesis.speak(u);
}

// ---------- 小工具 ----------
function $(id) { return document.getElementById(id); }
function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._t);
  t._t = setTimeout(() => t.classList.remove("show"), 2200);
}
function todayStr() { return new Date().toISOString().slice(0, 10); }

// ---------- 分頁切換 ----------
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => switchView(tab.dataset.view));
});
function switchView(view) {
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.view === view));
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  $("view-" + view).classList.add("active");
  if (view === "flashcards") initFlashcards();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ============================================================
// 總覽 Dashboard
// ============================================================
function computeStreak() {
  // 連續學習：以完成天數的數量近似（簡化版：已完成的最長連續 day 序列）
  if (state.done.length === 0) return 0;
  const set = new Set(state.done);
  let best = 0, cur = 0;
  for (let d = 1; d <= 30; d++) {
    if (set.has(d)) { cur++; best = Math.max(best, cur); }
    else cur = 0;
  }
  return best;
}
function renderDashboard() {
  const doneCount = state.done.length;
  const pct = doneCount / 30;
  $("statDone").textContent = doneCount;
  $("statStreak").textContent = computeStreak();
  const learnedDays = state.done.length ? Math.max(...state.done) : 0;
  const wordsLearned = CURRICULUM.filter(d => state.done.includes(d.day)).reduce((n, d) => n + d.vocab.length, 0);
  $("statWords").textContent = wordsLearned;
  $("statWeek").textContent = Math.min(4, Math.ceil((state.currentDay) / 7)) || 1;

  // 進度環
  const circ = 2 * Math.PI * 52; // ~327
  $("ringFg").style.strokeDashoffset = circ * (1 - pct);
  $("ringNum").textContent = doneCount;

  // 週地圖
  const map = $("weekMap");
  map.innerHTML = "";
  for (let w = 1; w <= 4; w++) {
    const days = CURRICULUM.filter(d => d.week === w);
    const wDone = days.filter(d => state.done.includes(d.day)).length;
    const row = document.createElement("div");
    row.className = "week-row";
    row.innerHTML = `
      <div class="week-head">
        <div><span class="week-name">Week ${w}</span> <span class="week-theme">· ${WEEK_THEMES[w]}</span></div>
        <div class="week-theme">${wDone}/${days.length} 完成</div>
      </div>
      <div class="day-grid">
        ${days.map(d => `
          <div class="day-cell ${state.done.includes(d.day) ? "done" : ""} ${d.day === state.currentDay ? "today" : ""}" data-day="${d.day}" title="${d.titleZh}">
            <span class="dn">${d.day}</span>
          </div>`).join("")}
      </div>`;
    map.appendChild(row);
  }
  map.querySelectorAll(".day-cell").forEach(c => {
    c.addEventListener("click", () => { openDay(parseInt(c.dataset.day)); switchView("lesson"); });
  });
}

$("continueBtn").addEventListener("click", () => {
  // 找第一個未完成的天數
  let next = 1;
  for (let d = 1; d <= 30; d++) { if (!state.done.includes(d)) { next = d; break; } if (d === 30) next = 30; }
  openDay(next);
  switchView("lesson");
});
$("resetBtn").addEventListener("click", () => {
  if (confirm("確定要重設所有學習進度嗎？此動作無法復原。")) {
    state = { done: [], currentDay: 1, lastStudy: null };
    saveState(state);
    renderDashboard();
    openDay(1);
    toast("進度已重設");
  }
});

// ============================================================
// 今日課程 Lesson
// ============================================================
function buildDaySelect() {
  const sel = $("daySelect");
  sel.innerHTML = CURRICULUM.map(d => `<option value="${d.day}">${d.day}</option>`).join("");
  sel.addEventListener("change", () => openDay(parseInt(sel.value)));
}

function openDay(day) {
  day = Math.max(1, Math.min(30, day));
  state.currentDay = day;
  saveState(state);
  const d = CURRICULUM.find(x => x.day === day);
  if (!d) return;

  $("daySelect").value = day;
  $("lessonWeek").textContent = `Week ${d.week} · Day ${d.day}`;
  $("lessonTitleZh").textContent = d.titleZh;
  $("lessonTitleEn").textContent = d.titleEn;
  $("lessonGoal").textContent = d.goalZh;

  // 字彙
  $("vocabList").innerHTML = d.vocab.map(v => `
    <div class="vocab-card">
      <div class="vocab-top">
        <span class="vocab-en">${v.en}</span>
        <button class="speak-btn" data-speak="${encodeURIComponent(v.en)}">🔊</button>
      </div>
      <div class="vocab-ipa">${v.ipa}</div>
      <div class="vocab-zh">${v.zh}</div>
      <div class="vocab-ex">“${v.ex}”</div>
    </div>`).join("");

  // 句型
  $("patternList").innerHTML = d.patterns.map(p => `
    <div class="pattern-item">
      <div class="ptext"><div class="pen">${p.en}</div><div class="pzh">${p.zh}</div></div>
      <button class="speak-btn" data-speak="${encodeURIComponent(p.en)}">🔊</button>
    </div>`).join("");

  // 對話
  $("dialogueList").innerHTML = d.dialogue.map(line => `
    <div class="dialogue-line">
      <span class="dialogue-role">${line.role}</span>
      <div>
        <div class="dialogue-en">${line.en}</div>
        <div class="dialogue-zh">${line.zh}</div>
      </div>
      <div class="dialogue-actions">
        <button class="speak-btn" data-speak="${encodeURIComponent(line.en)}">🔊</button>
        <button class="speak-btn" data-shadow="${encodeURIComponent(line.en)}">🎙</button>
      </div>
    </div>`).join("");

  // 面試題
  $("interviewList").innerHTML = d.interview.map(iv => `
    <div class="iv-item">
      <div class="iv-q">🎤 ${iv.q} <button class="speak-btn" data-speak="${encodeURIComponent(iv.q)}">🔊</button></div>
      <div class="iv-tip">💡 ${iv.tip}</div>
      <div class="iv-sample"><span class="iv-sample-label">參考回答：</span>${iv.sample}</div>
    </div>`).join("");

  // 任務
  $("taskText").textContent = d.task;
  const done = state.done.includes(day);
  const btn = $("completeBtn");
  btn.textContent = done ? "已完成 ✓（點此取消）" : "標記今天完成 ✓";
  btn.classList.toggle("ghost", done);
  btn.classList.toggle("primary", !done);

  bindSpeakButtons();
}

function bindSpeakButtons() {
  document.querySelectorAll("[data-speak]").forEach(b => {
    b.onclick = () => speak(decodeURIComponent(b.dataset.speak));
  });
  document.querySelectorAll("[data-shadow]").forEach(b => {
    b.onclick = () => shadowPractice(decodeURIComponent(b.dataset.shadow), b);
  });
}

$("prevDay").addEventListener("click", () => openDay(state.currentDay - 1));
$("nextDay").addEventListener("click", () => openDay(state.currentDay + 1));
$("completeBtn").addEventListener("click", () => {
  const day = state.currentDay;
  const i = state.done.indexOf(day);
  if (i >= 0) { state.done.splice(i, 1); toast("已取消完成標記"); }
  else { state.done.push(day); state.lastStudy = todayStr(); toast(`太棒了！Day ${day} 完成 🎉`); }
  saveState(state);
  openDay(day);
  renderDashboard();
});

// 跟讀練習：先朗讀，再啟動語音辨識比對
function shadowPractice(text, btn) {
  speak(text);
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { toast("此瀏覽器不支援語音辨識，建議用 Chrome"); return; }
  setTimeout(() => {
    const rec = new SR();
    rec.lang = "en-US"; rec.interimResults = false; rec.maxAlternatives = 1;
    btn.textContent = "🔴";
    toast("請跟著唸一次……");
    rec.onresult = (e) => {
      const said = e.results[0][0].transcript;
      const score = similarity(said.toLowerCase(), text.toLowerCase());
      toast(`你說：「${said}」— 相似度 ${Math.round(score * 100)}%`);
    };
    rec.onerror = () => toast("沒聽清楚，再試一次");
    rec.onend = () => { btn.textContent = "🎙"; };
    rec.start();
  }, Math.min(text.length * 55, 3500));
}

// 簡易字串相似度（詞彙重疊 Jaccard）
function similarity(a, b) {
  const wa = new Set(a.replace(/[^a-z0-9\s]/g, "").split(/\s+/).filter(Boolean));
  const wb = new Set(b.replace(/[^a-z0-9\s]/g, "").split(/\s+/).filter(Boolean));
  if (!wa.size || !wb.size) return 0;
  let inter = 0; wa.forEach(w => { if (wb.has(w)) inter++; });
  return inter / new Set([...wa, ...wb]).size;
}

// ============================================================
// 單字卡 Flashcards
// ============================================================
let fcDeck = [], fcIndex = 0;
function buildDeck(range) {
  const days = range === "all" ? CURRICULUM : CURRICULUM.filter(d => state.done.includes(d.day) || d.day === state.currentDay);
  const src = days.length ? days : CURRICULUM.slice(0, 1);
  const deck = [];
  src.forEach(d => d.vocab.forEach(v => deck.push(v)));
  return deck;
}
function shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
function initFlashcards() {
  fcDeck = shuffle(buildDeck($("fcRange").value));
  fcIndex = 0;
  renderFlashcard();
}
function renderFlashcard() {
  const inner = $("fcInner");
  inner.classList.remove("flipped");
  if (!fcDeck.length) { $("fcEn").textContent = "尚無單字，先去上課吧"; $("fcCounter").textContent = "0 / 0"; return; }
  const v = fcDeck[fcIndex];
  $("fcEn").textContent = v.en;
  $("fcZh").textContent = v.zh;
  $("fcEx").textContent = `“${v.ex}”`;
  $("fcCounter").textContent = `${fcIndex + 1} / ${fcDeck.length}`;
}
$("fcInner").addEventListener("click", (e) => {
  if (e.target.id === "fcSpeak") return;
  $("fcInner").classList.toggle("flipped");
});
$("fcSpeak").addEventListener("click", (e) => { e.stopPropagation(); if (fcDeck[fcIndex]) speak(fcDeck[fcIndex].en); });
$("fcNext").addEventListener("click", () => { if (!fcDeck.length) return; fcIndex = (fcIndex + 1) % fcDeck.length; renderFlashcard(); });
$("fcPrev").addEventListener("click", () => { if (!fcDeck.length) return; fcIndex = (fcIndex - 1 + fcDeck.length) % fcDeck.length; renderFlashcard(); });
$("fcShuffle").addEventListener("click", initFlashcards);
$("fcRange").addEventListener("change", initFlashcards);

// ============================================================
// 面試模擬器 Simulator
// ============================================================
let currentQ = "";
function pickQuestion() {
  const type = $("simType").value;
  let pool;
  if (type === "all") pool = [...MOCK_QUESTIONS.behavioral, ...MOCK_QUESTIONS.technical, ...MOCK_QUESTIONS.motivation];
  else pool = MOCK_QUESTIONS[type];
  currentQ = pool[Math.floor(Math.random() * pool.length)];
  $("simQ").textContent = currentQ;
  $("simTranscript").textContent = "按「開始錄音」後對著麥克風說英文……";
  $("simTimer").textContent = "";
  speak(currentQ);
}
$("simNext").addEventListener("click", pickQuestion);
$("simSpeakQ").addEventListener("click", () => currentQ && speak(currentQ));

let recog = null, listening = false, simTimerId = null, simSeconds = 0;
$("micBtn").addEventListener("click", () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { toast("此瀏覽器不支援語音辨識，建議用 Chrome / Edge"); return; }
  if (listening) { stopRecog(); return; }
  if (!currentQ) { pickQuestion(); }

  recog = new SR();
  recog.lang = "en-US"; recog.interimResults = true; recog.continuous = true;
  let finalText = "";
  const tr = $("simTranscript");
  tr.textContent = ""; tr.classList.add("listening");

  recog.onresult = (e) => {
    let interim = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) finalText += t + " "; else interim += t;
    }
    tr.textContent = finalText + interim;
  };
  recog.onerror = (e) => { toast("辨識錯誤：" + e.error); };
  recog.onend = () => { if (listening) recog.start(); }; // 自動續錄

  recog.start();
  listening = true;
  $("micBtn").textContent = "⏹ 停止錄音";
  $("micBtn").classList.add("mic-on");
  simSeconds = 0;
  simTimerId = setInterval(() => { simSeconds++; $("simTimer").textContent = `作答中… ${simSeconds}s（面試回答建議 60–90 秒）`; }, 1000);
});
function stopRecog() {
  listening = false;
  if (recog) { recog.onend = null; recog.stop(); }
  clearInterval(simTimerId);
  $("micBtn").textContent = "🎙 開始錄音";
  $("micBtn").classList.remove("mic-on");
  $("simTranscript").classList.remove("listening");
  const words = $("simTranscript").textContent.trim().split(/\s+/).filter(Boolean).length;
  if (words > 0) $("simTimer").textContent = `完成：約 ${words} 個字，用時 ${simSeconds} 秒。對照下方清單自評 👇`;
}

// ============================================================
// 初始化
// ============================================================
buildDaySelect();
openDay(state.currentDay);
renderDashboard();
