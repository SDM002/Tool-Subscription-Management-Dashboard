/**
 * static/app.js  [NEW]
 * Tool Subscription Dashboard — complete frontend logic
 *
 * Architecture:
 *   - State object holds auth token, user, current page, chat session
 *   - API module wraps all fetch() calls to the FastAPI backend
 *   - Page modules handle rendering for each section
 *   - Router switches between pages
 */

"use strict";

// ── Constants ────────────────────────────────────────────────
const BASE_URL = "";   // same origin — served by FastAPI
const API      = BASE_URL + "/api";

// ── Global state ─────────────────────────────────────────────
const state = {
  token:     localStorage.getItem("token") || null,
  user:      JSON.parse(localStorage.getItem("user") || "null"),
  page:      "dashboard",
  chatSession: null,
  subscriptions: [],
  dashboard: null,
};

// ── API helpers ───────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;

  const res = await fetch(API + path, { ...options, headers });

  if (res.status === 401) {
    logout();
    return null;
  }
  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const msg = data?.detail || data?.message || `Error ${res.status}`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}

// ── Auth ──────────────────────────────────────────────────────
async function register(email, fullName, password) {
  const data = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, full_name: fullName, password }),
  });
  if (data) saveAuth(data);
  return data;
}

async function login(email, password) {
  const data = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (data) saveAuth(data);
  return data;
}

function saveAuth(data) {
  state.token = data.access_token;
  state.user  = data.user;
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));
}

function logout() {
  state.token = null;
  state.user  = null;
  state.chatSession = null;
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  showAuthPage();
}

// ── Page routing ──────────────────────────────────────────────
function navigate(page) {
  state.page = page;
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  const pageEl = document.getElementById(`page-${page}`);
  if (pageEl) pageEl.classList.add("active");

  const navEl = document.querySelector(`[data-page="${page}"]`);
  if (navEl) navEl.classList.add("active");

  // Load page data
  switch (page) {
    case "dashboard":     loadDashboard(); break;
    case "subscriptions": loadSubscriptions(); break;
    case "renewals":      loadRenewals(); break;
    case "insights":      loadInsights(); break;
    case "chat":          initChat(); break;
  }
}

function showAuthPage() {
  document.getElementById("auth-page").style.display = "flex";
  document.getElementById("app").classList.remove("visible");
}

function showAppPage() {
  document.getElementById("auth-page").style.display = "none";
  document.getElementById("app").classList.add("visible");
  renderUserInfo();
  navigate("dashboard");
}

function renderUserInfo() {
  if (!state.user) return;
  const initial = (state.user.full_name || "U")[0].toUpperCase();
  document.getElementById("sidebar-avatar").textContent = initial;
  document.getElementById("sidebar-name").textContent = state.user.full_name;
  document.getElementById("sidebar-email").textContent = state.user.email;
}

// ── Toast notifications ───────────────────────────────────────
function toast(message, type = "info", duration = 3500) {
  const container = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ── Dashboard page ────────────────────────────────────────────
async function loadDashboard() {
  const page = document.getElementById("page-dashboard");
  page.innerHTML = `<div class="loading-page"><span class="spinner" style="border-color:rgba(102,126,234,0.3);border-top-color:var(--accent)"></span> Loading dashboard…</div>`;

  try {
    const data = await apiFetch("/dashboard/summary");
    if (!data) return;
    state.dashboard = data;
    renderDashboard(data);
  } catch (e) {
    page.innerHTML = `<div class="empty-state"><span class="empty-icon">⚠️</span><h3>Failed to load</h3><p>${e.message}</p></div>`;
  }
}

function renderDashboard(d) {
  const dueBadge = d.due_this_week.length > 0
    ? `<span class="badge badge-red">${d.due_this_week.length} urgent</span>` : "";

  document.getElementById("page-dashboard").innerHTML = `
    <div class="page-header">
      <div>
        <div class="page-title">Dashboard ${dueBadge}</div>
        <div class="page-subtitle">Welcome back, ${state.user?.full_name?.split(" ")[0] || "there"}!</div>
      </div>
      <button class="btn btn-primary" style="width:auto" onclick="openAddModal()">＋ Add Subscription</button>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-icon">📦</span>
        <div class="stat-label">Active Subscriptions</div>
        <div class="stat-value">${d.active_subscriptions}</div>
        <div class="stat-note">${d.total_subscriptions} total</div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">💳</span>
        <div class="stat-label">Monthly Spend</div>
        <div class="stat-value">$${d.total_monthly_spend.toFixed(2)}</div>
        <div class="stat-note">per month</div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">📅</span>
        <div class="stat-label">Yearly Spend</div>
        <div class="stat-value">$${d.total_yearly_spend.toFixed(2)}</div>
        <div class="stat-note">per year</div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">🔔</span>
        <div class="stat-label">Due This Week</div>
        <div class="stat-value" style="color:${d.due_this_week.length > 0 ? 'var(--danger)' : 'var(--success)'}">
          ${d.due_this_week.length}
        </div>
        <div class="stat-note">${d.due_this_month.length} due this month</div>
      </div>
    </div>

    ${d.due_this_week.length > 0 ? `
      <div class="section-header">
        <div class="section-title">🚨 Due This Week</div>
        <button class="btn btn-secondary btn-sm" onclick="navigate('renewals')">View all</button>
      </div>
      <div class="renewal-list">
        ${d.due_this_week.map(r => renewalItemHTML(r)).join("")}
      </div>
    ` : ""}

    <div class="section-header">
      <div class="section-title">📊 Spend by Category</div>
    </div>
    ${d.spend_by_category.length === 0 ? `
      <div class="empty-state" style="padding:40px">
        <span class="empty-icon">🗂️</span>
        <p>No category data yet — add some subscriptions!</p>
      </div>
    ` : `
      <div class="category-grid">
        ${d.spend_by_category.map(c => {
          const pct = d.total_monthly_spend > 0 ? (c.monthly_cost / d.total_monthly_spend * 100) : 0;
          return `
            <div class="category-card">
              <div class="category-name">${c.category} <span class="badge badge-gray">${c.count}</span></div>
              <div class="category-bar-bg"><div class="category-bar" style="width:${pct.toFixed(0)}%"></div></div>
              <div class="category-spend">$${c.monthly_cost.toFixed(2)}/mo · $${c.yearly_cost.toFixed(2)}/yr</div>
            </div>`;
        }).join("")}
      </div>
    `}
  `;
}

function renewalItemHTML(r) {
  const cls = r.days_until_renewal <= 3 ? "urgent" : r.days_until_renewal <= 7 ? "warning" : "ok";
  const daysText = r.days_until_renewal === 0 ? "Today!" :
                   r.days_until_renewal === 1 ? "Tomorrow" :
                   `${r.days_until_renewal} days`;
  const color = cls === "urgent" ? "var(--danger)" : cls === "warning" ? "var(--warning)" : "var(--success)";
  return `
    <div class="renewal-item ${cls}">
      <div class="renewal-info">
        <div class="renewal-name">${escHtml(r.tool_name)}</div>
        <div class="renewal-meta">${escHtml(r.category)} · ${r.currency} ${r.price.toFixed(2)} / ${r.billing_cycle}</div>
      </div>
      <div class="renewal-days" style="color:${color}">
        ${daysText}<br>
        <span style="font-weight:400;font-size:11px;color:var(--text-muted)">${r.renewal_date}</span>
      </div>
    </div>`;
}

// ── Subscriptions page ────────────────────────────────────────
async function loadSubscriptions() {
  const tbody = document.getElementById("sub-tbody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:40px;color:var(--text-muted)">Loading…</td></tr>`;

  try {
    const data = await apiFetch("/subscriptions");
    if (!data) return;
    state.subscriptions = data.subscriptions;
    renderSubscriptionTable(data.subscriptions);
  } catch (e) {
    toast("Failed to load subscriptions: " + e.message, "error");
  }
}

function renderSubscriptionTable(subs) {
  const searchVal = document.getElementById("sub-search")?.value?.toLowerCase() || "";
  const filterCat = document.getElementById("sub-filter-cat")?.value || "";

  const filtered = subs.filter(s =>
    (!searchVal || s.tool_name.toLowerCase().includes(searchVal) || s.category.toLowerCase().includes(searchVal)) &&
    (!filterCat || s.category === filterCat)
  );

  const tbody = document.getElementById("sub-tbody");
  if (!tbody) return;

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr><td colspan="7">
        <div class="empty-state">
          <span class="empty-icon">📭</span>
          <h3>No subscriptions found</h3>
          <p>Add your first subscription to get started.</p>
          <button class="btn btn-primary" style="width:auto" onclick="openAddModal()">＋ Add Subscription</button>
        </div>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(s => {
    const renewalBadge = s.renewal_date ? renderRenewalBadge(s.renewal_date) : '<span class="badge badge-gray">—</span>';
    return `
      <tr>
        <td><strong>${escHtml(s.tool_name)}</strong></td>
        <td><span class="badge badge-purple">${escHtml(s.category)}</span></td>
        <td>${s.currency} ${s.price.toFixed(2)}</td>
        <td><span class="badge badge-gray">${s.billing_cycle}</span></td>
        <td>$${s.monthly_cost.toFixed(2)}</td>
        <td>${renewalBadge}</td>
        <td>
          <div class="td-actions">
            <button class="btn btn-secondary btn-sm" onclick="openEditModal(${s.id})">✏️ Edit</button>
            <button class="btn btn-danger btn-sm" onclick="confirmDelete(${s.id}, '${escHtml(s.tool_name)}')">🗑️</button>
          </div>
        </td>
      </tr>`;
  }).join("");
}

function renderRenewalBadge(dateStr) {
  const today = new Date(); today.setHours(0,0,0,0);
  const d = new Date(dateStr);
  const diff = Math.round((d - today) / 86400000);
  if (diff < 0)  return `<span class="badge badge-red">Overdue</span>`;
  if (diff <= 3)  return `<span class="badge badge-red">${diff}d</span>`;
  if (diff <= 7)  return `<span class="badge badge-orange">${diff}d</span>`;
  if (diff <= 30) return `<span class="badge badge-purple">${diff}d</span>`;
  return `<span class="badge badge-green">${dateStr}</span>`;
}

// ── Add / Edit modal ──────────────────────────────────────────
const CATEGORIES = [
  "Productivity","Design","Development","Communication",
  "Storage & Cloud","Security","Analytics","Marketing",
  "Finance","AI & ML","Entertainment","Education","Other"
];

const BILLING_CYCLES = ["monthly","quarterly","yearly","lifetime"];

function subFormHTML(sub = null) {
  const v = (f, def="") => sub ? (sub[f] ?? def) : def;
  return `
    <div class="form-row">
      <div class="form-group">
        <label>Tool Name *</label>
        <input id="f-tool-name" type="text" value="${escHtml(v('tool_name'))}" placeholder="e.g. Figma" required>
      </div>
      <div class="form-group">
        <label>Category</label>
        <select id="f-category">
          ${CATEGORIES.map(c => `<option value="${c}" ${v('category','Other')===c?'selected':''}>${c}</option>`).join("")}
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Price *</label>
        <input id="f-price" type="number" step="0.01" min="0" value="${v('price',0)}" placeholder="0.00">
      </div>
      <div class="form-group">
        <label>Currency</label>
        <input id="f-currency" type="text" value="${v('currency','USD')}" maxlength="10" placeholder="USD">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Billing Cycle</label>
        <select id="f-billing-cycle">
          ${BILLING_CYCLES.map(c => `<option value="${c}" ${v('billing_cycle','monthly')===c?'selected':''}>${c}</option>`).join("")}
        </select>
      </div>
      <div class="form-group">
        <label>Start Date</label>
        <input id="f-start-date" type="date" value="${v('start_date','')}">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Renewal Date</label>
        <input id="f-renewal-date" type="date" value="${v('renewal_date','')}">
      </div>
      <div class="form-group">
        <label>Website URL</label>
        <input id="f-website-url" type="url" value="${v('website_url','')}" placeholder="https://…">
      </div>
    </div>
    <div class="form-group">
      <label>Notes</label>
      <textarea id="f-notes" placeholder="Any notes…">${v('notes','')}</textarea>
    </div>
  `;
}

function collectFormData() {
  return {
    tool_name:    document.getElementById("f-tool-name").value.trim(),
    category:     document.getElementById("f-category").value,
    price:        parseFloat(document.getElementById("f-price").value) || 0,
    currency:     document.getElementById("f-currency").value.trim() || "USD",
    billing_cycle:document.getElementById("f-billing-cycle").value,
    start_date:   document.getElementById("f-start-date").value || null,
    renewal_date: document.getElementById("f-renewal-date").value || null,
    website_url:  document.getElementById("f-website-url").value.trim() || null,
    notes:        document.getElementById("f-notes").value.trim() || null,
  };
}

function openAddModal() {
  document.getElementById("modal-title").textContent = "Add Subscription";
  document.getElementById("modal-body").innerHTML = subFormHTML();
  document.getElementById("modal-save-btn").onclick = saveNewSubscription;
  document.getElementById("sub-modal").classList.add("open");
}

async function openEditModal(id) {
  const sub = state.subscriptions.find(s => s.id === id);
  if (!sub) return;
  document.getElementById("modal-title").textContent = "Edit Subscription";
  document.getElementById("modal-body").innerHTML = subFormHTML(sub);
  document.getElementById("modal-save-btn").onclick = () => saveEditSubscription(id);
  document.getElementById("sub-modal").classList.add("open");
}

function closeModal() {
  document.getElementById("sub-modal").classList.remove("open");
}

async function saveNewSubscription() {
  const payload = collectFormData();
  if (!payload.tool_name) { toast("Tool name is required", "error"); return; }
  try {
    setBtnLoading("modal-save-btn", true);
    await apiFetch("/subscriptions", { method: "POST", body: JSON.stringify(payload) });
    toast("Subscription added!", "success");
    closeModal();
    loadSubscriptions();
    loadDashboard();
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setBtnLoading("modal-save-btn", false);
  }
}

async function saveEditSubscription(id) {
  const payload = collectFormData();
  try {
    setBtnLoading("modal-save-btn", true);
    await apiFetch(`/subscriptions/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
    toast("Subscription updated!", "success");
    closeModal();
    loadSubscriptions();
    loadDashboard();
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setBtnLoading("modal-save-btn", false);
  }
}

async function confirmDelete(id, name) {
  if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
  try {
    await apiFetch(`/subscriptions/${id}`, { method: "DELETE" });
    toast(`"${name}" deleted.`, "success");
    loadSubscriptions();
    loadDashboard();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ── Renewals page ─────────────────────────────────────────────
async function loadRenewals() {
  const container = document.getElementById("renewals-list");
  if (!container) return;
  container.innerHTML = `<div class="loading-page"><span>Loading…</span></div>`;

  try {
    const data = await apiFetch("/dashboard/renewals?days=90");
    if (!data) return;
    if (data.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">🎉</span>
          <h3>No upcoming renewals</h3>
          <p>Nothing renewing in the next 90 days.</p>
        </div>`;
      return;
    }
    container.innerHTML = data.map(r => renewalItemHTML(r)).join("");
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><p>Error: ${e.message}</p></div>`;
  }
}

// ── Insights page ─────────────────────────────────────────────
async function loadInsights() {
  const container = document.getElementById("insights-list");
  if (!container) return;
  container.innerHTML = `<div class="loading-page"><span>Loading insights…</span></div>`;

  try {
    const data = await apiFetch("/dashboard/insights");
    if (!data) return;

    if (data.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">💡</span>
          <h3>No insights yet</h3>
          <p>Add more subscriptions to get cost-saving recommendations.</p>
        </div>`;
      return;
    }

    container.innerHTML = `<div class="insight-list">` +
      data.map(ins => `
        <div class="insight-item insight-type-${ins.type}">
          <div class="insight-title">${insightIcon(ins.type)} ${escHtml(ins.title)}</div>
          <div class="insight-detail">${escHtml(ins.detail)}</div>
          ${ins.potential_saving > 0 ? `<div class="insight-saving">💰 Potential saving: $${ins.potential_saving.toFixed(2)}/year</div>` : ""}
        </div>`
      ).join("") + `</div>`;
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><p>Error: ${e.message}</p></div>`;
  }
}

function insightIcon(type) {
  return { duplicate: "🔁", annual_saving: "💰", high_cost: "⚠️", summary: "📊" }[type] || "💡";
}

// ── Chat page ─────────────────────────────────────────────────
function initChat() {
  const msgs = document.getElementById("chat-messages");
  if (!msgs) return;
  if (msgs.children.length <= 1) {
    // Show welcome message
    appendMessage("assistant", `Hi ${state.user?.full_name?.split(" ")[0] || "there"}! 👋 I'm your subscription assistant. I can help you understand your spending, find upcoming renewals, and suggest ways to save money. Try asking me something!`);
  }
}

const SUGGESTIONS = [
  "What's my monthly spend?",
  "What renews this week?",
  "How can I save money?",
  "Show me all subscriptions",
  "Any duplicate tools?",
];

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  input.style.height = "auto";
  appendMessage("user", message);
  showTyping(true);
  document.getElementById("chat-send-btn").disabled = true;

  try {
    const data = await apiFetch("/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: state.chatSession }),
    });
    if (!data) return;
    state.chatSession = data.session_id;
    showTyping(false);
    appendMessage("assistant", data.reply);
  } catch (e) {
    showTyping(false);
    appendMessage("assistant", `Sorry, I encountered an error: ${e.message}`);
  } finally {
    document.getElementById("chat-send-btn").disabled = false;
  }
}

function appendMessage(role, content) {
  const container = document.getElementById("chat-messages");
  if (!container) return;

  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const avatarText = role === "user" ? (state.user?.full_name?.[0]?.toUpperCase() || "U") : "🤖";
  const formattedContent = content.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  const el = document.createElement("div");
  el.className = `message ${role}`;
  el.innerHTML = `
    <div class="msg-avatar">${avatarText}</div>
    <div>
      <div class="msg-bubble">${formattedContent}</div>
      <div class="msg-time">${time}</div>
    </div>`;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

function showTyping(visible) {
  const el = document.getElementById("typing-indicator");
  if (el) el.classList.toggle("visible", visible);
  const container = document.getElementById("chat-messages");
  if (container) container.scrollTop = container.scrollHeight;
}

function sendSuggestion(text) {
  document.getElementById("chat-input").value = text;
  sendChatMessage();
}

function startNewSession() {
  state.chatSession = null;
  const container = document.getElementById("chat-messages");
  if (container) container.innerHTML = `<div id="typing-indicator" class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
  initChat();
  toast("New conversation started", "info");
}

// ── Auth form handling ────────────────────────────────────────
function switchTab(tab) {
  document.querySelectorAll(".auth-tab").forEach(t => t.classList.remove("active"));
  document.querySelector(`[data-tab="${tab}"]`).classList.add("active");
  document.getElementById("login-form").style.display  = tab === "login"    ? "block" : "none";
  document.getElementById("register-form").style.display = tab === "register" ? "block" : "none";
}

async function handleLogin(e) {
  e.preventDefault();
  const email    = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const errEl    = document.getElementById("login-error");
  errEl.textContent = "";

  try {
    setBtnLoading("login-btn", true);
    await login(email, password);
    showAppPage();
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    setBtnLoading("login-btn", false);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const fullName = document.getElementById("reg-name").value;
  const email    = document.getElementById("reg-email").value;
  const password = document.getElementById("reg-password").value;
  const errEl    = document.getElementById("reg-error");
  errEl.textContent = "";

  try {
    setBtnLoading("reg-btn", true);
    await register(email, fullName, password);
    showAppPage();
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    setBtnLoading("reg-btn", false);
  }
}

// ── Utilities ─────────────────────────────────────────────────
function escHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function setBtnLoading(id, loading) {
  const btn = document.getElementById(id);
  if (!btn) return;
  btn.disabled = loading;
  if (loading) {
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> Please wait…`;
  } else {
    btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
  }
}

// ── Bootstrap ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Check if already logged in
  if (state.token && state.user) {
    showAppPage();
  } else {
    showAuthPage();
  }

  // Auth form listeners
  document.getElementById("login-form")?.addEventListener("submit", handleLogin);
  document.getElementById("register-form")?.addEventListener("submit", handleRegister);

  // Chat enter key
  document.getElementById("chat-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  // Auto-resize chat textarea
  document.getElementById("chat-input")?.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
  });

  // Subscription search / filter
  document.getElementById("sub-search")?.addEventListener("input",  () => renderSubscriptionTable(state.subscriptions));
  document.getElementById("sub-filter-cat")?.addEventListener("change", () => renderSubscriptionTable(state.subscriptions));
});
