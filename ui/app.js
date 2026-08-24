"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const toast = (message) => {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  window.setTimeout(() => element.classList.remove("show"), 2200);
};

const fallback = {
  summary: { active_projects: 0, waiting_approvals: 0, open_unknowns: 0, tests_passed: 0 },
  projects: [], connectors: []
};

async function loadConsole() {
  let data = fallback;
  try {
    const response = await fetch("/v1/console/bootstrap", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`bootstrap_${response.status}`);
    data = await response.json();
  } catch (error) {
    toast("اتصال Backend برقرار نشد؛ رابط در حالت Degraded است.");
  }
  $("#metric-projects").textContent = data.summary.active_projects;
  $("#metric-approvals").textContent = data.summary.waiting_approvals;
  $("#metric-unknowns").textContent = data.summary.open_unknowns;
  $("#metric-tests").textContent = data.summary.tests_passed;
  $("#vault-queue").textContent = `${data.vault?.pending ?? 0} pending / ${data.vault?.processing ?? 0} processing`;
  $("#vault-generated").textContent = data.vault?.generated ?? 0;
  $("#project-list").innerHTML = data.projects.map(project => `
    <div class="task"><div class="task-meta"><strong>${escapeHtml(project.name)}</strong><span>${project.progress}%</span></div>
    <span class="status ${project.status === "hold" ? "hold" : ""}">${escapeHtml(project.status)}</span>
    <div class="progress"><i style="width:${Math.max(0, Math.min(100, project.progress))}%"></i></div></div>`).join("") || "<p class='notice'>داده‌ای در دسترس نیست.</p>";
  $("#connector-list").innerHTML = data.connectors.map(item => `
    <div class="connector-item ${item.state === "auth_broken" ? "broken" : ""}"><span><i></i>${escapeHtml(item.name)}</span><small>${escapeHtml(item.state)} · ${escapeHtml(item.scope)}</small></div>`).join("");
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = String(value);
  return node.innerHTML;
}

const started = performance.now();
window.setInterval(() => { $("#elapsed").textContent = `${((performance.now() - started) / 1000).toFixed(1)} ثانیه`; }, 100);

const dialog = $("#search-dialog");
const searchData = [
  ["Hydrostatic Tester", "پروژه · ۵ Unknown فنی"], ["KCl / MOP", "پروژه · بررسی تأمین‌کنندگان"],
  ["Golden Eagle", "شرکت · تأمین‌کننده Can Forming"], ["120 MPa", "Claim · نیازمند Pressure Basis"],
  ["Approval Inbox", "کنترل · ۲ مورد در انتظار"]
];
function openSearch() { dialog.showModal(); $("#global-search").focus(); renderSearch(""); }
function renderSearch(query) {
  const normalized = query.trim().toLowerCase();
  const results = searchData.filter(row => row.join(" ").toLowerCase().includes(normalized));
  $("#search-results").innerHTML = results.map(row => `<div class="search-result"><b>${escapeHtml(row[0])}</b><small>${escapeHtml(row[1])}</small></div>`).join("") || "<p class='notice'>نتیجه‌ای پیدا نشد.</p>";
}
$("#search-open").addEventListener("click", openSearch);
$("#global-search").addEventListener("input", event => renderSearch(event.target.value));
document.addEventListener("keydown", event => { if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) { event.preventDefault(); openSearch(); } });

const scopeCheck = $("#scope-check");
const approveButton = $("[data-demo-decision='approve']");
scopeCheck.addEventListener("change", () => { approveButton.disabled = !scopeCheck.checked; });
$$('[data-demo-decision]').forEach(button => button.addEventListener("click", () => {
  toast(button.dataset.demoDecision === "approve" ? "Preview تأیید شد؛ هیچ اقدامی اجرا نشد." : "Preview رد شد؛ هیچ داده‌ای تغییر نکرد.");
}));

$$('[data-filter]').forEach(button => button.addEventListener("click", () => {
  $$('[data-filter]').forEach(item => item.classList.remove("active"));
  button.classList.add("active");
  const filter = button.dataset.filter;
  $$('[data-status]').forEach(row => { row.hidden = filter !== "all" && row.dataset.status !== filter; });
}));

const streamText = "نتیجه: پیشنهاد Can Forming قابل مقایسه است، اما سرعت پایدار هنوز Claim تأمین‌کننده است و برای تبدیل به Fact باید در FAT اثبات شود.";
let streamTimer;
function playStream() {
  window.clearInterval(streamTimer);
  const output = $("#stream-output"); output.textContent = ""; let index = 0;
  streamTimer = window.setInterval(() => { output.textContent += streamText[index++] || ""; if (index >= streamText.length) window.clearInterval(streamTimer); }, 18);
}
$("#stream-replay").addEventListener("click", playStream); playStream();

$("[data-copy-code]").addEventListener("click", async () => { await navigator.clipboard.writeText($("#code-sample").textContent); toast("کد کپی شد."); });
$("#density").addEventListener("input", event => { document.body.classList.toggle("compact", event.target.value === "0"); document.body.classList.toggle("spacious", event.target.value === "2"); });
$("#radius").addEventListener("input", event => document.documentElement.style.setProperty("--radius", `${event.target.value}px`));
$("#reduce-motion").addEventListener("change", event => document.documentElement.style.setProperty("scroll-behavior", event.target.checked ? "auto" : "smooth"));

$$('[data-select-action]').forEach(button => button.addEventListener("click", () => {
  const selected = window.getSelection().toString().trim();
  $("#selection-result").textContent = selected ? `${button.textContent}: «${selected}» برای پردازش محلی علامت‌گذاری شد.` : "ابتدا بخشی از متن را انتخاب کنید.";
}));

$("#prompt-form").addEventListener("submit", event => {
  event.preventDefault(); const input = $("#prompt-input"); const value = input.value.trim(); if (!value) return;
  $("#messages").insertAdjacentHTML("beforeend", `<div class="message user">${escapeHtml(value)}</div><div class="message agent"><span>UI Lab · پاسخ آزمایشی</span>در نسخه فعلی درخواست ثبت خارجی نمی‌شود. این مسیر پس از Authentication به Orchestrator متصل خواهد شد.</div>`);
  input.value = ""; toast("درخواست فقط در رابط آزمایشی پردازش شد.");
});

$("#checkpoint-time").textContent = new Date().toLocaleString("fa-IR");
$("#copy-checkpoint").addEventListener("click", async () => { await navigator.clipboard.writeText("NEXUS v1.9 Runner Guard | read-only | OpenWorker experimental/disabled | 6 MCP candidates disabled | Vault active"); toast("Checkpoint کپی شد."); });

loadConsole();
