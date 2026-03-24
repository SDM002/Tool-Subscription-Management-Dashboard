/**
 * static/app.js
 * Full frontend — mirrors your original index.html JS pattern.
 * Chat uses EventSource (SSE) exactly like your /chat-stream endpoint.
 */
"use strict";

// ── State ─────────────────────────────────────────────────────
const state = {
  token:      localStorage.getItem("token") || null,
  user:       JSON.parse(localStorage.getItem("user") || "null"),
  page:       "dashboard",
  sessionId:  null,
  subs:       [],
};

// ── API helpers ───────────────────────────────────────────────
async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch("/api" + path, { ...opts, headers });
  if (res.status === 401) { logout(); return null; }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.detail || `Error ${res.status}`);
  return data;
}

// ── Auth ──────────────────────────────────────────────────────
async function register(email, name, password) {
  const d = await api("/auth/register", { method: "POST", body: JSON.stringify({ email, full_name: name, password }) });
  if (d) storeAuth(d);
  return d;
}
async function login(email, password) {
  const d = await api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
  if (d) storeAuth(d);
  return d;
}
function storeAuth(d) {
  state.token = d.access_token;
  state.user  = d.user;
  localStorage.setItem("token", d.access_token);
  localStorage.setItem("user",  JSON.stringify(d.user));
}
function logout() {
  state.token = null; state.user = null; state.sessionId = null;
  localStorage.removeItem("token"); localStorage.removeItem("user");
  showAuth();
}

// ── Router ────────────────────────────────────────────────────
function nav(page) {
  state.page = page;
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  const pel = document.getElementById(`page-${page}`);
  const nel = document.querySelector(`[data-page="${page}"]`);
  if (pel) pel.classList.add("active");
  if (nel) nel.classList.add("active");
  const loaders = { dashboard: loadDashboard, subscriptions: loadSubs, renewals: loadRenewals, insights: loadInsights, chat: initChat };
  loaders[page]?.();
}
function showAuth() {
  document.getElementById("auth-page").style.display = "flex";
  document.getElementById("app").classList.remove("visible");
}
function showApp() {
  document.getElementById("auth-page").style.display = "none";
  document.getElementById("app").classList.add("visible");
  const u = state.user;
  document.getElementById("sb-avatar").textContent = (u?.full_name || "U")[0].toUpperCase();
  document.getElementById("sb-name").textContent   = u?.full_name || "";
  document.getElementById("sb-email").textContent  = u?.email || "";
  nav("dashboard");
}

// ── Toast ─────────────────────────────────────────────────────
function toast(msg, type = "info", ms = 3500) {
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.getElementById("toast-box").appendChild(el);
  setTimeout(() => el.remove(), ms);
}

// ── Dashboard ─────────────────────────────────────────────────
async function loadDashboard() {
  const pg = document.getElementById("page-dashboard");
  pg.innerHTML = `<div class="loading"><span class="spinner spinner-accent"></span> Loading…</div>`;
  try {
    const d = await api("/dashboard/summary");
    if (!d) return;
    pg.innerHTML = `
      <div class="page-header">
        <div><div class="page-title">Dashboard</div>
          <div class="page-sub">Welcome back, ${esc(state.user?.full_name?.split(" ")[0] || "there")}!</div></div>
        <button class="btn btn-primary" style="width:auto" onclick="openAdd()">＋ Add Subscription</button>
      </div>
      <div class="stats-grid">
        <div class="stat-card"><span class="stat-icon">📦</span>
          <div class="stat-label">Active Subs</div>
          <div class="stat-value">${d.active_subscriptions}</div>
          <div class="stat-note">${d.total_subscriptions} total</div></div>
        <div class="stat-card"><span class="stat-icon">💳</span>
          <div class="stat-label">Monthly</div>
          <div class="stat-value">$${d.total_monthly_spend.toFixed(2)}</div>
          <div class="stat-note">per month</div></div>
        <div class="stat-card"><span class="stat-icon">📅</span>
          <div class="stat-label">Yearly</div>
          <div class="stat-value">$${d.total_yearly_spend.toFixed(2)}</div>
          <div class="stat-note">per year</div></div>
        <div class="stat-card"><span class="stat-icon">🔔</span>
          <div class="stat-label">Due This Week</div>
          <div class="stat-value" style="color:${d.due_this_week.length > 0 ? 'var(--danger)' : 'var(--success)'}">${d.due_this_week.length}</div>
          <div class="stat-note">${d.due_this_month.length} this month</div></div>
      </div>
      ${d.due_this_week.length ? `
        <div class="section-header"><div class="section-title">🚨 Due This Week</div>
          <button class="btn btn-secondary btn-sm" onclick="nav('renewals')">View all</button></div>
        <div class="renewal-list">${d.due_this_week.map(renewalHTML).join("")}</div>` : ""}
      <div class="section-header"><div class="section-title">📊 Spend by Category</div></div>
      ${d.spend_by_category.length === 0
        ? `<div class="empty"><span class="empty-icon">🗂️</span><p>No data yet — add some subscriptions!</p></div>`
        : `<div class="cat-grid">${d.spend_by_category.map(c => {
            const pct = d.total_monthly_spend > 0 ? (c.monthly_cost / d.total_monthly_spend * 100).toFixed(0) : 0;
            return `<div class="cat-card">
              <div class="cat-name">${esc(c.category)} <span class="badge badge-gray">${c.count}</span></div>
              <div class="cat-bar-bg"><div class="cat-bar" style="width:${pct}%"></div></div>
              <div class="cat-spend">$${c.monthly_cost.toFixed(2)}/mo · $${c.yearly_cost.toFixed(2)}/yr</div>
            </div>`;
          }).join("")}</div>`}`;
  } catch(e) {
    pg.innerHTML = `<div class="empty"><span class="empty-icon">⚠️</span><h3>Error</h3><p>${e.message}</p></div>`;
  }
}

function renewalHTML(r) {
  const cls   = r.days_until_renewal <= 3 ? "urgent" : r.days_until_renewal <= 7 ? "warning" : "ok";
  const color = cls === "urgent" ? "var(--danger)" : cls === "warning" ? "var(--warning)" : "var(--success)";
  const days  = r.days_until_renewal === 0 ? "Today!" : r.days_until_renewal === 1 ? "Tomorrow" : `${r.days_until_renewal} days`;
  return `<div class="renewal-item ${cls}">
    <div><div class="renewal-name">${esc(r.tool_name)}</div>
      <div class="renewal-meta">${esc(r.category)} · ${r.currency} ${r.price.toFixed(2)} / ${r.billing_cycle}</div></div>
    <div class="renewal-days" style="color:${color}">${days}<br>
      <span style="font-weight:400;font-size:11px;color:var(--muted)">${r.renewal_date}</span></div>
  </div>`;
}

// ── Subscriptions ─────────────────────────────────────────────
async function loadSubs() {
  const tbody = document.getElementById("sub-tbody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="7" class="loading">Loading…</td></tr>`;
  try {
    const d = await api("/subscriptions");
    if (!d) return;
    state.subs = d.subscriptions;
    renderSubTable(d.subscriptions);
  } catch(e) { toast("Failed to load: " + e.message, "error"); }
}

function renderSubTable(subs) {
  const search = document.getElementById("sub-search")?.value?.toLowerCase() || "";
  const cat    = document.getElementById("sub-cat-filter")?.value || "";
  const filt   = subs.filter(s =>
    (!search || s.tool_name.toLowerCase().includes(search) || s.category.toLowerCase().includes(search)) &&
    (!cat || s.category === cat)
  );
  const tbody = document.getElementById("sub-tbody");
  if (!tbody) return;
  if (!filt.length) {
    tbody.innerHTML = `<tr><td colspan="7">
      <div class="empty"><span class="empty-icon">📭</span><h3>No subscriptions</h3>
        <p>Add your first subscription to get started.</p>
        <button class="btn btn-primary" style="width:auto" onclick="openAdd()">＋ Add</button></div>
    </td></tr>`;
    return;
  }
  tbody.innerHTML = filt.map(s => `
    <tr>
      <td><strong>${esc(s.tool_name)}</strong></td>
      <td><span class="badge badge-purple">${esc(s.category)}</span></td>
      <td>${s.currency} ${s.price.toFixed(2)}</td>
      <td><span class="badge badge-gray">${s.billing_cycle}</span></td>
      <td>$${s.monthly_cost.toFixed(2)}</td>
      <td>${s.renewal_date ? renewalBadge(s.renewal_date) : '<span class="badge badge-gray">—</span>'}</td>
      <td><div class="td-actions">
        <button class="btn btn-secondary btn-sm" onclick="openEdit(${s.id})">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="confirmDel(${s.id},'${esc(s.tool_name)}')">🗑️</button>
      </div></td>
    </tr>`).join("");
}

function renewalBadge(ds) {
  const today = new Date(); today.setHours(0,0,0,0);
  const d = new Date(ds), diff = Math.round((d - today) / 86400000);
  if (diff < 0)   return `<span class="badge badge-red">Overdue</span>`;
  if (diff <= 3)  return `<span class="badge badge-red">${diff}d</span>`;
  if (diff <= 7)  return `<span class="badge badge-orange">${diff}d</span>`;
  if (diff <= 30) return `<span class="badge badge-purple">${diff}d</span>`;
  return `<span class="badge badge-green">${ds}</span>`;
}

// ── Subscription modal ────────────────────────────────────────
const CATS   = ["Productivity","Design","Development","Communication","Storage & Cloud","Security","Analytics","Marketing","Finance","AI & ML","Entertainment","Education","Other"];
const CYCLES = ["monthly","quarterly","yearly","lifetime"];

function subForm(s = null) {
  const v = (f, d="") => s ? (s[f] ?? d) : d;
  return `
    <div class="form-row">
      <div class="form-group"><label>Tool Name *</label><input id="f-name" value="${esc(v('tool_name'))}" placeholder="e.g. Figma"></div>
      <div class="form-group"><label>Category</label><select id="f-cat">${CATS.map(c=>`<option value="${c}" ${v('category','Other')===c?'selected':''}>${c}</option>`).join("")}</select></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Price</label><input id="f-price" type="number" step="0.01" min="0" value="${v('price',0)}"></div>
      <div class="form-group"><label>Currency</label><input id="f-cur" value="${v('currency','USD')}" maxlength="10"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Billing Cycle</label><select id="f-cycle">${CYCLES.map(c=>`<option value="${c}" ${v('billing_cycle','monthly')===c?'selected':''}>${c}</option>`).join("")}</select></div>
      <div class="form-group"><label>Start Date</label><input id="f-start" type="date" value="${v('start_date','')}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Renewal Date</label><input id="f-renew" type="date" value="${v('renewal_date','')}"></div>
      <div class="form-group"><label>Website URL</label><input id="f-url" type="url" value="${v('website_url','')}" placeholder="https://…"></div>
    </div>
    <div class="form-group"><label>Notes</label><textarea id="f-notes">${v('notes','')}</textarea></div>`;
}

function formData() {
  return {
    tool_name:    document.getElementById("f-name").value.trim(),
    category:     document.getElementById("f-cat").value,
    price:        parseFloat(document.getElementById("f-price").value)||0,
    currency:     document.getElementById("f-cur").value.trim()||"USD",
    billing_cycle:document.getElementById("f-cycle").value,
    start_date:   document.getElementById("f-start").value||null,
    renewal_date: document.getElementById("f-renew").value||null,
    website_url:  document.getElementById("f-url").value.trim()||null,
    notes:        document.getElementById("f-notes").value.trim()||null,
  };
}

function openAdd() {
  document.getElementById("modal-title").textContent = "Add Subscription";
  document.getElementById("modal-body").innerHTML = subForm();
  document.getElementById("modal-save").onclick = saveAdd;
  document.getElementById("modal").classList.add("open");
}
function openEdit(id) {
  const s = state.subs.find(s=>s.id===id);
  if (!s) return;
  document.getElementById("modal-title").textContent = "Edit Subscription";
  document.getElementById("modal-body").innerHTML = subForm(s);
  document.getElementById("modal-save").onclick = ()=>saveEdit(id);
  document.getElementById("modal").classList.add("open");
}
function closeModal() { document.getElementById("modal").classList.remove("open"); }

async function saveAdd() {
  const p = formData();
  if (!p.tool_name) { toast("Tool name required","error"); return; }
  try {
    btnLoad("modal-save", true);
    await api("/subscriptions", { method:"POST", body:JSON.stringify(p) });
    toast("Subscription added!","success"); closeModal(); loadSubs(); loadDashboard();
  } catch(e) { toast(e.message,"error"); }
  finally { btnLoad("modal-save", false); }
}
async function saveEdit(id) {
  try {
    btnLoad("modal-save", true);
    await api(`/subscriptions/${id}`, { method:"PATCH", body:JSON.stringify(formData()) });
    toast("Updated!","success"); closeModal(); loadSubs(); loadDashboard();
  } catch(e) { toast(e.message,"error"); }
  finally { btnLoad("modal-save", false); }
}
async function confirmDel(id, name) {
  if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
  try {
    await api(`/subscriptions/${id}`, { method:"DELETE" });
    toast(`"${name}" deleted.`,"success"); loadSubs(); loadDashboard();
  } catch(e) { toast(e.message,"error"); }
}

// ── Renewals page ─────────────────────────────────────────────
async function loadRenewals() {
  const c = document.getElementById("renewals-list");
  if (!c) return;
  c.innerHTML = `<div class="loading"><span class="spinner spinner-accent"></span> Loading…</div>`;
  try {
    const d = await api("/dashboard/renewals?days=90");
    if (!d) return;
    c.innerHTML = d.length
      ? `<div class="renewal-list">${d.map(renewalHTML).join("")}</div>`
      : `<div class="empty"><span class="empty-icon">🎉</span><h3>All clear!</h3><p>Nothing renewing in the next 90 days.</p></div>`;
  } catch(e) { c.innerHTML = `<div class="empty"><p>Error: ${e.message}</p></div>`; }
}

// ── Insights page ─────────────────────────────────────────────
async function loadInsights() {
  const c = document.getElementById("insights-list");
  if (!c) return;
  c.innerHTML = `<div class="loading"><span class="spinner spinner-accent"></span> Analysing…</div>`;
  try {
    const d = await api("/dashboard/insights");

    // insights come from the MCP server via /dashboard/insights
    // We call the dashboard route which uses dashboard_service
    // For insights we call the pricing endpoint
    const ins = await api("/dashboard/summary");
    // Rebuild using a dedicated insights endpoint — let's use the summary data
    // to get insights from the agent or from the pricing rules
    const data = d || [];
    if (!data.length) {
      c.innerHTML = `<div class="empty"><span class="empty-icon">💡</span><h3>No insights yet</h3><p>Add more subscriptions to get recommendations.</p></div>`;
      return;
    }
    const icons = { duplicate:"🔁", annual_saving:"💰", high_cost:"⚠️", summary:"📊" };
    c.innerHTML = `<div class="insight-list">${data.map(i => `
      <div class="insight-item ${i.type}">
        <div class="insight-title">${icons[i.type]||"💡"} ${esc(i.title)}</div>
        <div class="insight-detail">${esc(i.detail)}</div>
        ${i.potential_saving > 0 ? `<div class="insight-saving">💰 Save ~$${i.potential_saving.toFixed(2)}/yr</div>` : ""}
      </div>`).join("")}</div>`;
  } catch(e) { c.innerHTML = `<div class="empty"><p>Error: ${e.message}</p></div>`; }
}

// ── Chat — SSE streaming (YOUR exact pattern) ─────────────────
function initChat() {
  const msgs = document.getElementById("chat-msgs");
  if (!msgs || msgs.dataset.init) return;
  msgs.dataset.init = "1";
  appendMsg("ai", `Hi ${state.user?.full_name?.split(" ")[0]||"there"}! 👋 I'm your subscription assistant powered by Groq + LangGraph + MCP. Ask me anything about your subscriptions!`);
}

function sendChat() {
  const input = document.getElementById("chat-input");
  const msg   = input.value.trim();
  if (!msg) return;
  input.value = "";
  input.style.height = "auto";
  appendMsg("user", msg);
  setTyping(true);
  document.getElementById("send-btn").disabled = true;

  // ── SSE streaming — EXACT same pattern as your original ──
  const params = new URLSearchParams({
    message:    msg,
    session_id: state.sessionId || "",
  });

  // We need auth header — EventSource doesn't support headers.
  // Workaround: pass token as query param (acceptable for SSE in local apps)
  params.append("token", state.token || "");

  // Create a bot message div to stream into
  const msgs    = document.getElementById("chat-msgs");
  const botDiv  = document.createElement("div");
  botDiv.className = "msg ai";
  botDiv.innerHTML = `<div class="msg-av">🤖</div><div><div class="msg-bubble" id="streaming-bubble"></div><div class="msg-time">${new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}</div></div>`;
  msgs.appendChild(botDiv);
  msgs.scrollTop = msgs.scrollHeight;

  setTyping(false); // hide typing once we start streaming

  const bubble = document.getElementById("streaming-bubble");
  bubble.id = ""; // remove id so next message can use it

  // Use fetch + ReadableStream for SSE with auth header
  fetch(`/api/chat/stream?${params.toString()}`, {
    headers: { "Authorization": `Bearer ${state.token}` }
  }).then(res => {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    function read() {
      reader.read().then(({ done, value }) => {
        if (done) {
          document.getElementById("send-btn").disabled = false;
          return;
        }
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.text) {
              bubble.textContent += data.text;
              msgs.scrollTop = msgs.scrollHeight;
            }
            if (data.session_id) {
              state.sessionId = data.session_id;
            }
            if (data.end) {
              document.getElementById("send-btn").disabled = false;
            }
            if (data.error) {
              bubble.textContent = "Error: " + data.error;
              document.getElementById("send-btn").disabled = false;
            }
          } catch(_) {}
        }
        read();
      });
    }
    read();
  }).catch(err => {
    bubble.textContent = "Connection error: " + err.message;
    setTyping(false);
    document.getElementById("send-btn").disabled = false;
  });
}

function appendMsg(role, content) {
  const msgs = document.getElementById("chat-msgs");
  if (!msgs) return;
  const time = new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});
  const av   = role === "user" ? (state.user?.full_name?.[0]?.toUpperCase()||"U") : "🤖";
  const el   = document.createElement("div");
  el.className = `msg ${role}`;
  el.innerHTML = `
    <div class="msg-av">${av}</div>
    <div><div class="msg-bubble">${content.replace(/\n/g,"<br>").replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>")}</div>
    <div class="msg-time">${time}</div></div>`;
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
}

function setTyping(on) {
  const el = document.getElementById("typing-ind");
  if (el) el.classList.toggle("on", on);
  document.getElementById("chat-msgs").scrollTop = 9999;
}

function suggest(text) {
  document.getElementById("chat-input").value = text;
  sendChat();
}

function newChat() {
  state.sessionId = null;
  const msgs = document.getElementById("chat-msgs");
  if (msgs) { msgs.innerHTML = `<div id="typing-ind" class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`; delete msgs.dataset.init; }
  initChat();
  toast("New conversation started","info");
}

// ── Auth forms ────────────────────────────────────────────────
function switchTab(tab) {
  document.querySelectorAll(".auth-tab").forEach(t=>t.classList.remove("active"));
  document.querySelector(`[data-tab="${tab}"]`).classList.add("active");
  document.getElementById("login-form").style.display    = tab==="login"    ? "block" : "none";
  document.getElementById("register-form").style.display = tab==="register" ? "block" : "none";
}

async function handleLogin(e) {
  e.preventDefault();
  const err = document.getElementById("login-err");
  err.textContent = "";
  try {
    btnLoad("login-btn", true);
    await login(document.getElementById("l-email").value, document.getElementById("l-pass").value);
    showApp();
  } catch(ex) { err.textContent = ex.message; }
  finally { btnLoad("login-btn", false); }
}

async function handleRegister(e) {
  e.preventDefault();
  const err = document.getElementById("reg-err");
  err.textContent = "";
  try {
    btnLoad("reg-btn", true);
    await register(document.getElementById("r-email").value, document.getElementById("r-name").value, document.getElementById("r-pass").value);
    showApp();
  } catch(ex) { err.textContent = ex.message; }
  finally { btnLoad("reg-btn", false); }
}

// ── Utilities ─────────────────────────────────────────────────
function esc(s) {
  if (!s) return "";
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function btnLoad(id, on) {
  const b = document.getElementById(id);
  if (!b) return;
  b.disabled = on;
  if (on) { b.dataset.orig = b.innerHTML; b.innerHTML = `<span class="spinner"></span> Wait…`; }
  else    { b.innerHTML = b.dataset.orig || b.innerHTML; }
}

// ── Boot ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  state.token && state.user ? showApp() : showAuth();

  document.getElementById("login-form")?.addEventListener("submit", handleLogin);
  document.getElementById("register-form")?.addEventListener("submit", handleRegister);

  document.getElementById("chat-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); }
  });
  document.getElementById("chat-input")?.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
  });

  document.getElementById("sub-search")?.addEventListener("input",  () => renderSubTable(state.subs));
  document.getElementById("sub-cat-filter")?.addEventListener("change", () => renderSubTable(state.subs));
});
