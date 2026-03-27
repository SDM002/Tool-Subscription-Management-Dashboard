/**
 * static/app.js — Tool Subscription Management Dashboard
 * Rewritten with maximum compatibility (no arrow functions, no template literals
 * in critical paths) to ensure it works on all browsers without transpilation.
 */
"use strict";

var state = {
  token:     localStorage.getItem("token") || null,
  user:      JSON.parse(localStorage.getItem("user") || "null"),
  page:      "dashboard",
  sessionId: null,
  subs:      []
};

function api(path, opts) {
  opts = opts || {};
  var headers = { "Content-Type": "application/json" };
  if (opts.headers) Object.assign(headers, opts.headers);
  if (state.token) headers["Authorization"] = "Bearer " + state.token;
  return fetch("/api" + path, Object.assign({}, opts, { headers: headers }))
    .then(function(res) {
      if (res.status === 401) { logout(); return null; }
      if (res.status === 204) return null;
      return res.json().catch(function() { return null; }).then(function(data) {
        if (!res.ok) throw new Error((data && data.detail) ? data.detail : "Error " + res.status);
        return data;
      });
    });
}

function doLogin(email, password) {
  return api("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email: email, password: password })
  }).then(function(d) { if (d) saveAuth(d); return d; });
}

function doRegister(email, name, password) {
  return api("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email: email, full_name: name, password: password })
  }).then(function(d) { if (d) saveAuth(d); return d; });
}

function saveAuth(d) {
  state.token = d.access_token;
  state.user  = d.user;
  localStorage.setItem("token", d.access_token);
  localStorage.setItem("user", JSON.stringify(d.user));
}

function logout() {
  state.token = null; state.user = null; state.sessionId = null;
  localStorage.removeItem("token"); localStorage.removeItem("user");
  showAuth();
}

function showAuth() {
  document.getElementById("auth-page").style.display = "flex";
  document.getElementById("app").classList.remove("visible");
}

function showApp() {
  document.getElementById("auth-page").style.display = "none";
  document.getElementById("app").classList.add("visible");
  if (state.user) {
    document.getElementById("sb-avatar").textContent = (state.user.full_name || "U")[0].toUpperCase();
    document.getElementById("sb-name").textContent   = state.user.full_name || "";
    document.getElementById("sb-email").textContent  = state.user.email || "";
  }
  nav("dashboard");
}

function switchTab(tab) {
  document.querySelectorAll(".auth-tab").forEach(function(t) { t.classList.remove("active"); });
  var el = document.querySelector("[data-tab='" + tab + "']");
  if (el) el.classList.add("active");
  document.getElementById("login-form").style.display    = tab === "login"    ? "block" : "none";
  document.getElementById("register-form").style.display = tab === "register" ? "block" : "none";
}

function handleLogin(e) {
  e.preventDefault();
  var email    = document.getElementById("l-email").value.trim();
  var password = document.getElementById("l-pass").value;
  var errEl    = document.getElementById("login-err");
  errEl.textContent = "";
  if (!email || !password) { errEl.textContent = "Please enter email and password."; return; }
  btnLoad("login-btn", true);
  doLogin(email, password)
    .then(function(d) { if (d) showApp(); })
    .catch(function(err) { errEl.textContent = err.message || "Login failed"; })
    .finally(function() { btnLoad("login-btn", false); });
}

function handleRegister(e) {
  e.preventDefault();
  var name     = document.getElementById("r-name").value.trim();
  var email    = document.getElementById("r-email").value.trim();
  var password = document.getElementById("r-pass").value;
  var errEl    = document.getElementById("reg-err");
  errEl.textContent = "";
  if (!name || !email || !password) { errEl.textContent = "All fields are required."; return; }
  btnLoad("reg-btn", true);
  doRegister(email, name, password)
    .then(function(d) { if (d) showApp(); })
    .catch(function(err) { errEl.textContent = err.message || "Registration failed"; })
    .finally(function() { btnLoad("reg-btn", false); });
}

function nav(page) {
  state.page = page;
  document.querySelectorAll(".page").forEach(function(p) { p.classList.remove("active"); });
  document.querySelectorAll(".nav-item").forEach(function(n) { n.classList.remove("active"); });
  var pel = document.getElementById("page-" + page);
  var nel = document.querySelector("[data-page='" + page + "']");
  if (pel) pel.classList.add("active");
  if (nel) nel.classList.add("active");
  if (page === "dashboard")     loadDashboard();
  if (page === "subscriptions") loadSubs();
  if (page === "renewals")      loadRenewals();
  if (page === "insights")      loadInsights();
  if (page === "chat")          initChat();
}

function toast(msg, type, ms) {
  var el = document.createElement("div");
  el.className = "toast toast-" + (type || "info");
  el.textContent = msg;
  document.getElementById("toast-box").appendChild(el);
  setTimeout(function() { if (el.parentNode) el.parentNode.removeChild(el); }, ms || 3500);
}

function esc(s) {
  if (s === null || s === undefined) return "";
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function btnLoad(id, on) {
  var b = document.getElementById(id);
  if (!b) return;
  b.disabled = on;
  if (on) { b.dataset.orig = b.innerHTML; b.innerHTML = "Please wait..."; }
  else    { b.innerHTML = b.dataset.orig || b.innerHTML; }
}

function renewalHTML(r) {
  var cls   = r.days_until_renewal <= 3 ? "urgent" : r.days_until_renewal <= 7 ? "warning" : "ok";
  var color = cls === "urgent" ? "var(--danger)" : cls === "warning" ? "var(--warning)" : "var(--success)";
  var days  = r.days_until_renewal === 0 ? "Today!" : r.days_until_renewal === 1 ? "Tomorrow" : r.days_until_renewal + " days";
  return "<div class='renewal-item " + cls + "'><div>" +
    "<div class='renewal-name'>" + esc(r.tool_name) + "</div>" +
    "<div class='renewal-meta'>" + esc(r.category) + " &middot; " + r.currency + " " + r.price.toFixed(2) + " / " + r.billing_cycle + "</div></div>" +
    "<div class='renewal-days' style='color:" + color + "'>" + days + "<br>" +
    "<span style='font-weight:400;font-size:11px;color:var(--muted)'>" + r.renewal_date + "</span></div></div>";
}

function loadDashboard() {
  var pg = document.getElementById("page-dashboard");
  pg.innerHTML = "<div class='loading'>Loading...</div>";
  api("/dashboard/summary").then(function(d) {
    if (!d) return;
    var weekHTML = "";
    if (d.due_this_week && d.due_this_week.length) {
      weekHTML = "<div class='section-header'><div class='section-title'>🚨 Due This Week</div>" +
        "<button class='btn btn-secondary btn-sm' onclick=\"nav('renewals')\">View all</button></div>" +
        "<div class='renewal-list'>" + d.due_this_week.map(renewalHTML).join("") + "</div>";
    }
    var catHTML = "";
    if (d.spend_by_category && d.spend_by_category.length) {
      catHTML = "<div class='cat-grid'>" + d.spend_by_category.map(function(c) {
        var pct = d.total_monthly_spend > 0 ? (c.monthly_cost / d.total_monthly_spend * 100).toFixed(0) : 0;
        return "<div class='cat-card'><div class='cat-name'>" + esc(c.category) +
          " <span class='badge badge-gray'>" + c.count + "</span></div>" +
          "<div class='cat-bar-bg'><div class='cat-bar' style='width:" + pct + "%'></div></div>" +
          "<div class='cat-spend'>$" + c.monthly_cost.toFixed(2) + "/mo &middot; $" + c.yearly_cost.toFixed(2) + "/yr</div></div>";
      }).join("") + "</div>";
    }
    var name = state.user && state.user.full_name ? state.user.full_name.split(" ")[0] : "there";
    pg.innerHTML =
      "<div class='page-header'><div><div class='page-title'>Dashboard</div>" +
      "<div class='page-sub'>Welcome back, " + esc(name) + "!</div></div>" +
      "<button class='btn btn-primary' style='width:auto' onclick='openAdd()'>+ Add Subscription</button></div>" +
      "<div class='stats-grid'>" +
      "<div class='stat-card'><span class='stat-icon'>📦</span><div class='stat-label'>Active Subs</div>" +
      "<div class='stat-value'>" + d.active_subscriptions + "</div><div class='stat-note'>" + d.total_subscriptions + " total</div></div>" +
      "<div class='stat-card'><span class='stat-icon'>💳</span><div class='stat-label'>Monthly</div>" +
      "<div class='stat-value'>$" + d.total_monthly_spend.toFixed(2) + "</div><div class='stat-note'>per month</div></div>" +
      "<div class='stat-card'><span class='stat-icon'>📅</span><div class='stat-label'>Yearly</div>" +
      "<div class='stat-value'>$" + d.total_yearly_spend.toFixed(2) + "</div><div class='stat-note'>per year</div></div>" +
      "<div class='stat-card'><span class='stat-icon'>🔔</span><div class='stat-label'>Due This Week</div>" +
      "<div class='stat-value' style='color:" + (d.due_this_week.length > 0 ? "var(--danger)" : "var(--success)") + "'>" +
      d.due_this_week.length + "</div><div class='stat-note'>" + d.due_this_month.length + " this month</div></div></div>" +
      weekHTML +
      "<div class='section-header'><div class='section-title'>📊 Spend by Category</div></div>" + catHTML;
  }).catch(function(e) {
    pg.innerHTML = "<div class='empty'><span class='empty-icon'>⚠️</span><h3>Error loading dashboard</h3><p>" + esc(e.message) + "</p></div>";
  });
}

function loadSubs() {
  var tbody = document.getElementById("sub-tbody");
  if (!tbody) return;
  tbody.innerHTML = "<tr><td colspan='7'>Loading...</td></tr>";
  api("/subscriptions").then(function(d) {
    if (!d) return;
    state.subs = d.subscriptions;
    renderSubTable(d.subscriptions);
  }).catch(function(e) { toast("Error: " + e.message, "error"); });
}

function renewalBadge(ds) {
  var today = new Date(); today.setHours(0,0,0,0);
  var diff  = Math.round((new Date(ds) - today) / 86400000);
  if (diff < 0)  return "<span class='badge badge-red'>Overdue</span>";
  if (diff <= 3)  return "<span class='badge badge-red'>" + diff + "d</span>";
  if (diff <= 7)  return "<span class='badge badge-orange'>" + diff + "d</span>";
  if (diff <= 30) return "<span class='badge badge-purple'>" + diff + "d</span>";
  return "<span class='badge badge-green'>" + ds + "</span>";
}

function renderSubTable(subs) {
  var search = ((document.getElementById("sub-search") || {}).value || "").toLowerCase();
  var cat    = (document.getElementById("sub-cat-filter") || {}).value || "";
  var filt   = subs.filter(function(s) {
    return (!search || s.tool_name.toLowerCase().indexOf(search) >= 0 || s.category.toLowerCase().indexOf(search) >= 0) &&
           (!cat || s.category === cat);
  });
  var tbody = document.getElementById("sub-tbody");
  if (!tbody) return;
  if (!filt.length) {
    tbody.innerHTML = "<tr><td colspan='7'><div class='empty'><span class='empty-icon'>📭</span><h3>No subscriptions</h3><p>Add your first subscription.</p>" +
      "<button class='btn btn-primary' style='width:auto' onclick='openAdd()'>+ Add</button></div></td></tr>";
    return;
  }
  tbody.innerHTML = filt.map(function(s) {
    return "<tr><td><strong>" + esc(s.tool_name) + "</strong></td>" +
      "<td><span class='badge badge-purple'>" + esc(s.category) + "</span></td>" +
      "<td>" + s.currency + " " + s.price.toFixed(2) + "</td>" +
      "<td><span class='badge badge-gray'>" + s.billing_cycle + "</span></td>" +
      "<td>$" + s.monthly_cost.toFixed(2) + "</td>" +
      "<td>" + (s.renewal_date ? renewalBadge(s.renewal_date) : "<span class='badge badge-gray'>-</span>") + "</td>" +
      "<td><div class='td-actions'>" +
      "<button class='btn btn-secondary btn-sm' onclick='openEdit(" + s.id + ")'>Edit</button>" +
      "<button class='btn btn-danger btn-sm' onclick=\"confirmDel(" + s.id + ",'" + esc(s.tool_name) + "')\">Del</button>" +
      "</div></td></tr>";
  }).join("");
}

var CATS   = ["Productivity","Design","Development","Communication","Storage & Cloud","Security","Analytics","Marketing","Finance","AI & ML","Entertainment","Education","Other"];
var CYCLES = ["monthly","quarterly","yearly","lifetime"];

function subForm(s) {
  function v(f, def) { return (s && s[f] !== null && s[f] !== undefined) ? s[f] : (def !== undefined ? def : ""); }
  return "<div class='form-row'>" +
    "<div class='form-group'><label>Tool Name *</label><input id='f-name' type='text' value='" + esc(v("tool_name")) + "' placeholder='e.g. Figma'></div>" +
    "<div class='form-group'><label>Category</label><select id='f-cat'>" +
    CATS.map(function(c) { return "<option value='" + c + "'" + (v("category","Other") === c ? " selected" : "") + ">" + c + "</option>"; }).join("") +
    "</select></div></div><div class='form-row'>" +
    "<div class='form-group'><label>Price</label><input id='f-price' type='number' step='0.01' min='0' value='" + v("price",0) + "'></div>" +
    "<div class='form-group'><label>Currency</label><input id='f-cur' value='" + esc(v("currency","USD")) + "' maxlength='10'></div></div>" +
    "<div class='form-row'><div class='form-group'><label>Billing Cycle</label><select id='f-cycle'>" +
    CYCLES.map(function(c) { return "<option value='" + c + "'" + (v("billing_cycle","monthly") === c ? " selected" : "") + ">" + c + "</option>"; }).join("") +
    "</select></div><div class='form-group'><label>Start Date</label><input id='f-start' type='date' value='" + v("start_date","") + "'></div></div>" +
    "<div class='form-row'><div class='form-group'><label>Renewal Date</label><input id='f-renew' type='date' value='" + v("renewal_date","") + "'></div>" +
    "<div class='form-group'><label>Website URL</label><input id='f-url' type='url' value='" + esc(v("website_url","")) + "' placeholder='https://...'></div></div>" +
    "<div class='form-group'><label>Notes</label><textarea id='f-notes'>" + esc(v("notes","")) + "</textarea></div>";
}

function formData() {
  return {
    tool_name:     document.getElementById("f-name").value.trim(),
    category:      document.getElementById("f-cat").value,
    price:         parseFloat(document.getElementById("f-price").value) || 0,
    currency:      document.getElementById("f-cur").value.trim() || "USD",
    billing_cycle: document.getElementById("f-cycle").value,
    start_date:    document.getElementById("f-start").value || null,
    renewal_date:  document.getElementById("f-renew").value || null,
    website_url:   document.getElementById("f-url").value.trim() || null,
    notes:         document.getElementById("f-notes").value.trim() || null
  };
}

function openAdd() {
  document.getElementById("modal-title").textContent = "Add Subscription";
  document.getElementById("modal-body").innerHTML = subForm(null);
  document.getElementById("modal-save").onclick = saveAdd;
  document.getElementById("modal").classList.add("open");
}

function openEdit(id) {
  var s = null;
  for (var i = 0; i < state.subs.length; i++) { if (state.subs[i].id === id) { s = state.subs[i]; break; } }
  if (!s) return;
  document.getElementById("modal-title").textContent = "Edit Subscription";
  document.getElementById("modal-body").innerHTML = subForm(s);
  (function(sid) { document.getElementById("modal-save").onclick = function() { saveEdit(sid); }; })(id);
  document.getElementById("modal").classList.add("open");
}

function closeModal() { document.getElementById("modal").classList.remove("open"); }

function saveAdd() {
  var p = formData();
  if (!p.tool_name) { toast("Tool name is required", "error"); return; }
  btnLoad("modal-save", true);
  api("/subscriptions", { method: "POST", body: JSON.stringify(p) })
    .then(function() { toast("Subscription added!", "success"); closeModal(); loadSubs(); loadDashboard(); })
    .catch(function(e) { toast(e.message, "error"); })
    .finally(function() { btnLoad("modal-save", false); });
}

function saveEdit(id) {
  btnLoad("modal-save", true);
  api("/subscriptions/" + id, { method: "PATCH", body: JSON.stringify(formData()) })
    .then(function() { toast("Updated!", "success"); closeModal(); loadSubs(); loadDashboard(); })
    .catch(function(e) { toast(e.message, "error"); })
    .finally(function() { btnLoad("modal-save", false); });
}

function confirmDel(id, name) {
  if (!confirm("Delete \"" + name + "\"?")) return;
  api("/subscriptions/" + id, { method: "DELETE" })
    .then(function() { toast("Deleted.", "success"); loadSubs(); loadDashboard(); })
    .catch(function(e) { toast(e.message, "error"); });
}

function loadRenewals() {
  var c = document.getElementById("renewals-list");
  if (!c) return;
  c.innerHTML = "<div class='loading'>Loading...</div>";
  api("/dashboard/renewals?days=90").then(function(d) {
    c.innerHTML = (d && d.length)
      ? "<div class='renewal-list'>" + d.map(renewalHTML).join("") + "</div>"
      : "<div class='empty'><span class='empty-icon'>🎉</span><h3>All clear!</h3><p>Nothing renewing in 90 days.</p></div>";
  }).catch(function(e) { c.innerHTML = "<p>Error: " + esc(e.message) + "</p>"; });
}

function loadInsights() {
  var c = document.getElementById("insights-list");
  if (!c) return;
  c.innerHTML = "<div class='loading'>Analysing...</div>";
  api("/dashboard/insights").then(function(data) {
    if (!data || !data.length) {
      c.innerHTML = "<div class='empty'><span class='empty-icon'>💡</span><h3>No insights yet</h3><p>Add more subscriptions.</p></div>";
      return;
    }
    var icons = { duplicate:"🔁", annual_saving:"💰", high_cost:"⚠️", summary:"📊" };
    c.innerHTML = "<div class='insight-list'>" + data.map(function(i) {
      return "<div class='insight-item " + (i.type||"") + "'>" +
        "<div class='insight-title'>" + (icons[i.type]||"💡") + " " + esc(i.title) + "</div>" +
        "<div class='insight-detail'>" + esc(i.detail) + "</div>" +
        (i.potential_saving > 0 ? "<div class='insight-saving'>💰 Save ~$" + i.potential_saving.toFixed(2) + "/yr</div>" : "") +
        "</div>";
    }).join("") + "</div>";
  }).catch(function(e) { c.innerHTML = "<p>Error: " + esc(e.message) + "</p>"; });
}

function initChat() {
  var msgs = document.getElementById("chat-msgs");
  if (!msgs || msgs.dataset.init) return;
  msgs.dataset.init = "1";
  var name = (state.user && state.user.full_name) ? state.user.full_name.split(" ")[0] : "there";
  appendMsg("ai", "Hi " + name + "! I am your subscription assistant. Ask me about your spending, renewals, or savings!");
}

function sendChat() {
  var input = document.getElementById("chat-input");
  var msg   = input.value.trim();
  if (!msg) return;
  input.value = "";
  appendMsg("user", msg);
  document.getElementById("send-btn").disabled = true;

  var msgs   = document.getElementById("chat-msgs");
  var botDiv = document.createElement("div");
  botDiv.className = "msg ai";
  botDiv.innerHTML = "<div class='msg-av'>🤖</div><div><div class='msg-bubble' id='sbubble'></div><div class='msg-time'>" +
    new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}) + "</div></div>";
  msgs.appendChild(botDiv);
  msgs.scrollTop = msgs.scrollHeight;
  var bubble = document.getElementById("sbubble");
  if (bubble) bubble.removeAttribute("id");


  fetch("/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json", "Authorization": "Bearer " + state.token },
  body: JSON.stringify({ message: msg, session_id: state.sessionId || "" })
})
.then(function(res) { return res.json(); })
.then(function(d) {
  if (d.reply && bubble) { bubble.innerHTML = d.reply.replace(/\n/g,"<br>"); msgs.scrollTop = msgs.scrollHeight; }
  if (d.session_id) state.sessionId = d.session_id;
  if (d.detail && bubble) bubble.textContent = "Error: " + d.detail;
  document.getElementById("send-btn").disabled = false;
})
.catch(function(err) {
  if (bubble) bubble.textContent = "Error: " + err.message;
  document.getElementById("send-btn").disabled = false;
});


}

function appendMsg(role, content) {
  var msgs = document.getElementById("chat-msgs"); if (!msgs) return;
  var time = new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});
  var av   = role === "user" ? ((state.user && state.user.full_name) ? state.user.full_name[0].toUpperCase() : "U") : "🤖";
  var el   = document.createElement("div");
  el.className = "msg " + role;
  el.innerHTML = "<div class='msg-av'>" + av + "</div><div><div class='msg-bubble'>" +
    content.replace(/\n/g,"<br>") + "</div><div class='msg-time'>" + time + "</div></div>";
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
}

function setTyping(on) {
  var el = document.getElementById("typing-ind");
  if (el) el.classList.toggle("on", on);
}

function suggest(text) {
  var input = document.getElementById("chat-input");
  if (input) { input.value = text; sendChat(); }
}

function newChat() {
  state.sessionId = null;
  var msgs = document.getElementById("chat-msgs");
  if (msgs) {
    msgs.innerHTML = "<div id='typing-ind' class='typing'><div class='dot'></div><div class='dot'></div><div class='dot'></div></div>";
    delete msgs.dataset.init;
  }
  initChat();
  toast("New conversation started", "info");
}

window.addEventListener("DOMContentLoaded", function() {
  if (state.token && state.user) { showApp(); } else { showAuth(); }

  var lf = document.getElementById("login-form");
  if (lf) lf.addEventListener("submit", handleLogin);

  var rf = document.getElementById("register-form");
  if (rf) rf.addEventListener("submit", handleRegister);

  var ci = document.getElementById("chat-input");
  if (ci) {
    ci.addEventListener("keydown", function(e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); }
    });
  }

  var ss = document.getElementById("sub-search");
  if (ss) ss.addEventListener("input", function() { renderSubTable(state.subs); });

  var sf = document.getElementById("sub-cat-filter");
  if (sf) sf.addEventListener("change", function() { renderSubTable(state.subs); });

  document.addEventListener("keydown", function(e) { if (e.key === "Escape") closeModal(); });
});
