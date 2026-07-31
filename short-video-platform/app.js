/* ============================================================
 *  一站式短影音變現平台 — 應用邏輯
 * ============================================================ */

const STORE_KEY = "svp_projects_v1";

/* ---------- 狀態 ---------- */
let projects = load();
let activeStudioStage = "idea";

function load() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return JSON.parse(JSON.stringify(SEED_PROJECTS));
}
function save() {
  localStorage.setItem(STORE_KEY, JSON.stringify(projects));
}

/* ---------- 工具函式 ---------- */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const stageById = (id) => STAGES.find((s) => s.id === id);
const stageIndex = (id) => STAGES.findIndex((s) => s.id === id);
const uid = () => "p" + Math.random().toString(36).slice(2, 9);

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove("show"), 1900);
}

/* ---------- 導覽 ---------- */
function navTo(page) {
  $$(".nav-item").forEach((n) => n.classList.toggle("active", n.dataset.page === page));
  $$(".page").forEach((p) => p.classList.toggle("active", p.id === "page-" + page));
  $("#sidebar").classList.remove("open");
  if (page === "dashboard") renderDashboard();
  if (page === "pipeline") renderPipeline();
  if (page === "money") renderMoney();
}

/* ---------- 儀表板 ---------- */
function renderDashboard() {
  const total = projects.length;
  const published = projects.filter((p) => p.stage === "publish").length;
  const inprog = total - published;
  const revenue = projects.reduce((s, p) => s + (+p.revenue || 0), 0);
  const monthlyCost = Object.values(TOOLS).reduce((s, t) => s + t.price, 0);

  $("#stat-total").textContent = total;
  $("#stat-progress").textContent = inprog;
  $("#stat-published").textContent = published;
  $("#stat-revenue").textContent = "$" + revenue.toLocaleString();
  $("#stat-cost").textContent = "$" + monthlyCost.toFixed(2);

  const roi = monthlyCost ? (((revenue - monthlyCost) / monthlyCost) * 100) : 0;
  const roiEl = $("#dash-roi");
  roiEl.textContent = (roi >= 0 ? "+" : "") + roi.toFixed(0) + "%";
  roiEl.className = "value " + (roi >= 0 ? "green" : "amber");
  $("#dash-net").textContent =
    "本月淨利 = 收益 $" + revenue.toLocaleString() + " − 工具成本 $" + monthlyCost.toFixed(2) +
    " = $" + (revenue - monthlyCost).toFixed(2);

  // 流水線分布
  const dist = $("#dash-dist");
  dist.innerHTML = "";
  STAGES.forEach((st) => {
    const n = projects.filter((p) => p.stage === st.id).length;
    const pct = total ? (n / total) * 100 : 0;
    const row = document.createElement("div");
    row.style.marginBottom = "12px";
    row.innerHTML = `
      <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:2px;">
        <span>${st.icon} ${st.name}</span><span style="color:var(--muted)">${n} 支</span>
      </div>
      <div class="bar"><span style="width:${pct}%"></span></div>`;
    dist.appendChild(row);
  });
}

/* ---------- 流水線 Kanban ---------- */
function renderPipeline() {
  const board = $("#kanban");
  board.innerHTML = "";
  STAGES.forEach((st) => {
    const col = document.createElement("div");
    col.className = "col";
    col.dataset.stage = st.id;
    const items = projects.filter((p) => p.stage === st.id);
    col.innerHTML = `
      <div class="col-head">
        <div class="t">${st.icon} ${st.name}</div>
        <div class="count">${items.length}</div>
      </div>
      <div class="col-desc">${st.desc}</div>
      <div class="col-body"></div>`;
    const body = $(".col-body", col);
    items.forEach((p) => body.appendChild(projectCard(p)));

    // drag & drop 接收
    col.addEventListener("dragover", (e) => { e.preventDefault(); col.classList.add("drag-over"); });
    col.addEventListener("dragleave", () => col.classList.remove("drag-over"));
    col.addEventListener("drop", (e) => {
      e.preventDefault();
      col.classList.remove("drag-over");
      const id = e.dataTransfer.getData("id");
      const proj = projects.find((x) => x.id === id);
      if (proj && proj.stage !== st.id) {
        proj.stage = st.id;
        save();
        renderPipeline();
        toast(`「${proj.title}」→ ${st.icon} ${st.name}`);
      }
    });
    board.appendChild(col);
  });
}

function projectCard(p) {
  const el = document.createElement("div");
  el.className = "pcard";
  el.draggable = true;
  const st = stageById(p.stage);
  const dots = st.tools
    .map((tid) => `<span class="dot" title="${TOOLS[tid].name}" style="background:${TOOLS[tid].color}"></span>`)
    .join("");
  el.innerHTML = `
    <div class="pt">${p.title}</div>
    <div class="pmeta">
      <span class="tag">${p.topic}</span>
      <span class="tag">${p.platform}</span>
      ${+p.revenue > 0 ? `<span class="tag rev">$${p.revenue}</span>` : ""}
    </div>
    <div class="pcard-tools">${dots}</div>`;
  el.addEventListener("dragstart", (e) => {
    e.dataTransfer.setData("id", p.id);
    el.classList.add("dragging");
  });
  el.addEventListener("dragend", () => el.classList.remove("dragging"));
  el.addEventListener("click", () => openEdit(p));
  return el;
}

/* ---------- 工具箱 ---------- */
function renderTools() {
  const grid = $("#tools-grid");
  grid.innerHTML = "";
  let total = 0;
  Object.entries(TOOLS).forEach(([id, t]) => {
    total += t.price;
    const a = document.createElement("a");
    a.className = "tool";
    a.href = t.url;
    a.target = "_blank";
    a.rel = "noopener";
    a.innerHTML = `
      <div class="thead">
        <div class="tname"><span class="swatch" style="background:${t.color}">${t.name[0]}</span>${t.name}</div>
        <div class="price">$${t.price}<small>/月</small></div>
      </div>
      <div class="role">${t.role}</div>
      <div class="tnote">${t.note}</div>`;
    grid.appendChild(a);
  });
  $("#tools-total").textContent = "$" + total.toFixed(2);
}

/* ---------- Prompt 工作室 ---------- */
function renderStudio() {
  const list = $("#stage-list");
  list.innerHTML = "";
  STAGES.forEach((st) => {
    if (!PROMPTS[st.id]) return;
    const b = document.createElement("div");
    b.className = "stage-btn" + (st.id === activeStudioStage ? " active" : "");
    b.innerHTML = `<span>${st.icon}</span> ${st.name}`;
    b.addEventListener("click", () => { activeStudioStage = st.id; renderStudio(); });
    list.appendChild(b);
  });
  const pr = PROMPTS[activeStudioStage];
  const tool = TOOLS[pr.tool];
  $("#studio-title").textContent = pr.title;
  $("#studio-tool").innerHTML =
    `建議工具：<b style="color:${tool.color}">${tool.name}</b> · ${tool.role}`;
  $("#prompt-text").value = pr.template;
}

/* ---------- 變現追蹤 ---------- */
function renderMoney() {
  const revenue = projects.reduce((s, p) => s + (+p.revenue || 0), 0);
  const cost = Object.values(TOOLS).reduce((s, t) => s + t.price, 0);
  const net = revenue - cost;
  $("#m-rev").textContent = "$" + revenue.toLocaleString();
  $("#m-cost").textContent = "$" + cost.toFixed(2);
  const netEl = $("#m-net");
  netEl.textContent = "$" + net.toFixed(2);
  netEl.className = "value " + (net >= 0 ? "green" : "amber");

  // 依平台彙總
  const byPlat = {};
  projects.forEach((p) => {
    byPlat[p.platform] = byPlat[p.platform] || { rev: 0, n: 0 };
    byPlat[p.platform].rev += +p.revenue || 0;
    byPlat[p.platform].n++;
  });
  const max = Math.max(1, ...Object.values(byPlat).map((v) => v.rev));
  const tb = $("#money-body");
  tb.innerHTML = "";
  Object.entries(byPlat)
    .sort((a, b) => b[1].rev - a[1].rev)
    .forEach(([plat, v]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${plat}</td>
        <td>${v.n} 支</td>
        <td><span class="money">$${v.rev.toLocaleString()}</span>
            <div class="bar"><span style="width:${(v.rev / max) * 100}%"></span></div></td>`;
      tb.appendChild(tr);
    });
  if (!Object.keys(byPlat).length) tb.innerHTML = `<tr><td colspan="3" class="empty">尚無資料</td></tr>`;
}

/* ---------- 新增 / 編輯專案 ---------- */
let editingId = null;
function openNew() {
  editingId = null;
  $("#modal-title").textContent = "新增短影音專案";
  $("#f-title").value = "";
  $("#f-topic").value = "";
  $("#f-platform").value = "YouTube Shorts";
  $("#f-revenue").value = 0;
  fillStageSelect("idea");
  $("#btn-delete").style.display = "none";
  $("#overlay").classList.add("show");
}
function openEdit(p) {
  editingId = p.id;
  $("#modal-title").textContent = "編輯專案";
  $("#f-title").value = p.title;
  $("#f-topic").value = p.topic;
  $("#f-platform").value = p.platform;
  $("#f-revenue").value = p.revenue;
  fillStageSelect(p.stage);
  $("#btn-delete").style.display = "inline-block";
  $("#overlay").classList.add("show");
}
function fillStageSelect(sel) {
  const s = $("#f-stage");
  s.innerHTML = STAGES.map((st) => `<option value="${st.id}">${st.icon} ${st.name}</option>`).join("");
  s.value = sel;
}
function closeModal() { $("#overlay").classList.remove("show"); }
function saveProject() {
  const title = $("#f-title").value.trim();
  if (!title) { toast("請輸入標題"); return; }
  const data = {
    title,
    topic: $("#f-topic").value.trim() || "未分類",
    platform: $("#f-platform").value,
    stage: $("#f-stage").value,
    revenue: Math.max(0, +$("#f-revenue").value || 0),
  };
  if (editingId) {
    Object.assign(projects.find((p) => p.id === editingId), data);
    toast("已更新");
  } else {
    projects.unshift({ id: uid(), createdAt: Date.now(), ...data });
    toast("已新增專案");
  }
  save();
  closeModal();
  refreshAll();
}
function deleteProject() {
  projects = projects.filter((p) => p.id !== editingId);
  save();
  closeModal();
  refreshAll();
  toast("已刪除");
}

function refreshAll() {
  const active = $(".page.active")?.id.replace("page-", "") || "dashboard";
  navTo(active);
}

/* ---------- 綁定 ---------- */
function init() {
  $$(".nav-item").forEach((n) => n.addEventListener("click", () => navTo(n.dataset.page)));
  $("#btn-new").addEventListener("click", openNew);
  $("#btn-new-2").addEventListener("click", openNew);
  $("#btn-save").addEventListener("click", saveProject);
  $("#btn-cancel").addEventListener("click", closeModal);
  $("#btn-delete").addEventListener("click", deleteProject);
  $("#overlay").addEventListener("click", (e) => { if (e.target.id === "overlay") closeModal(); });
  $("#menu-toggle").addEventListener("click", () => $("#sidebar").classList.toggle("open"));

  $("#btn-copy").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText($("#prompt-text").value);
      toast("已複製 Prompt，貼到工具即可");
    } catch { toast("複製失敗，請手動選取"); }
  });
  $("#btn-open-tool").addEventListener("click", () => {
    window.open(TOOLS[PROMPTS[activeStudioStage].tool].url, "_blank");
  });
  $("#btn-reset").addEventListener("click", () => {
    if (confirm("確定要清空所有資料並還原示範專案？")) {
      projects = JSON.parse(JSON.stringify(SEED_PROJECTS));
      save(); refreshAll(); toast("已還原示範資料");
    }
  });

  renderTools();
  renderStudio();
  navTo("dashboard");
}

document.addEventListener("DOMContentLoaded", init);
