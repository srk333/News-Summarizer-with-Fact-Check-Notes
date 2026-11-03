const API_BASE =
  location.hostname === "localhost" || location.hostname === "127.0.0.1"
    ? "http://localhost:5000/api"
    : "https://news-summarizer-with-fact-check-notes.onrender.com/api";
const $ = (id) => document.getElementById(id);

/* ---------- helpers ---------- */
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? u : "#");

function toast(msg, type = "") {
  const box = $("toasts");
  if (!box) return;
  const t = document.createElement("div");
  t.className = "toast " + type;
  t.textContent = msg;
  box.appendChild(t);
  setTimeout(() => t.remove(), 3800);
}

/* ---------- session ---------- */
const getToken = () => {
  try {
    return localStorage.getItem("nl_token");
  } catch (e) {
    return null;
  }
};
const getEmail = () => {
  try {
    return localStorage.getItem("nl_email");
  } catch (e) {
    return null;
  }
};
const saveSession = (t, e) => {
  try {
    localStorage.setItem("nl_token", t);
    localStorage.setItem("nl_email", e);
  } catch (x) {}
};
const clearSession = () => {
  try {
    localStorage.removeItem("nl_token");
    localStorage.removeItem("nl_email");
  } catch (x) {}
};
const isLoggedIn = () => !!getToken();

async function authFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(API_BASE + path, { ...options, headers });
  if (res.status === 401 && token) {
    clearSession();
    renderAuthNav();
    updateSaveHint();
  }
  return res;
}

/* ---------- header ---------- */
function renderHeader() {
  const page = document.body.dataset.page;
  const link = (h, k, t) =>
    `<a href="${h}" class="${page === k ? "active" : ""}">${t}</a>`;
  $("app-header").innerHTML = `<header class="nav-bar"><div class="wrap nav-in">
      <a href="index.html" class="brand">
        <svg width="28" height="28" viewBox="0 0 32 32" fill="none"><defs><linearGradient id="lg" x1="0" y1="0" x2="32" y2="32"><stop stop-color="#3B82F6"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs>
        <rect width="32" height="32" rx="9" fill="url(#lg)"/><circle cx="14" cy="14" r="6" stroke="#fff" stroke-width="2.2"/><path d="M19 19l5 5" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/><circle cx="14" cy="14" r="1.8" fill="#22D3EE"/></svg>
        NewsLens <b>AI</b></a>
      <nav class="links">${link("index.html", "analyze", "Analyze News")}${link("history.html", "history", "History")}${link("about.html", "about", "About")}</nav>
      <div id="auth-nav" class="auth-nav"></div></div></header>`;
  renderAuthNav();
}

function renderAuthNav() {
  const box = $("auth-nav");
  if (!box) return;
  box.innerHTML = isLoggedIn()
    ? `<span class="user-chip">${esc(getEmail())}</span><button class="nav-btn" onclick="logout()">Log out</button>`
    : `<button class="nav-btn" onclick="openAuth('login')">Log in</button><button class="nav-btn nav-btn-primary" onclick="openAuth('signup')">Get Started</button>`;
}

/* ---------- login popup: created only when opened, so no email/password fields exist at page load ---------- */
let authMode = "login";

function openAuth(mode) {
  closeAuth();
  authMode = mode || "login";
  const m = document.createElement("div");
  m.id = "auth-modal";
  m.className = "modal-overlay";
  m.innerHTML = `<form class="modal-box" id="auth-form" onsubmit="submitAuth(event)" novalidate>
      <button type="button" class="modal-close" aria-label="Close" onclick="closeAuth()">&times;</button>
      <h2 id="auth-title"></h2><p id="auth-sub" class="modal-sub"></p>
      <div id="auth-error" class="error hidden"></div>
      <label class="field-label" for="auth-email">Email</label>
      <input id="auth-email" name="email" type="email" class="field" placeholder="you@example.com">
      <label class="field-label" for="auth-password">Password</label>
      <input id="auth-password" name="password" type="password" class="field" placeholder="At least 8 characters">
      <button id="auth-submit" type="submit" class="btn btn-primary btn-block"></button>
      <p class="modal-switch"><span id="auth-switch-text"></span> <a href="#" id="auth-switch-link" onclick="toggleAuthMode(event)"></a></p></form>`;
  document.body.appendChild(m);
  m.addEventListener("mousedown", (e) => {
    if (e.target === m) closeAuth();
  });
  m.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAuth();
  });
  setAuthMode(authMode);
  $("auth-email").focus();
}

function setAuthMode(mode) {
  authMode = mode;
  const s = mode === "signup";
  $("auth-title").textContent = s ? "Create your account" : "Welcome back";
  $("auth-sub").textContent = s
    ? "Save every analysis to your own history."
    : "Log in to see your saved analyses.";
  $("auth-submit").textContent = s ? "Sign up" : "Log in";
  $("auth-switch-text").textContent = s
    ? "Already have an account?"
    : "New here?";
  $("auth-switch-link").textContent = s ? "Log in" : "Create an account";
  $("auth-email").autocomplete = s ? "email" : "username";
  $("auth-password").autocomplete = s ? "new-password" : "current-password";
  $("auth-error").classList.add("hidden");
}
function toggleAuthMode(e) {
  e.preventDefault();
  setAuthMode(authMode === "login" ? "signup" : "login");
}
function closeAuth() {
  const m = $("auth-modal");
  if (m) m.remove();
}

async function submitAuth(e) {
  e.preventDefault();
  const email = $("auth-email").value.trim(),
    password = $("auth-password").value;
  const err = $("auth-error"),
    btn = $("auth-submit");
  const fail = (msg) => {
    err.textContent = msg;
    err.classList.remove("hidden");
  };
  err.classList.add("hidden");
  if (!email || !password) return fail("Enter your email and password.");
  if (authMode === "signup" && password.length < 8)
    return fail("Password must be at least 8 characters.");
  btn.disabled = true;
  try {
    const res = await fetch(
      `${API_BASE}/auth/${authMode === "signup" ? "register" : "login"}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      },
    );
    const data = await res.json();
    if (!res.ok)
      return fail(data.error || "Something went wrong. Please try again.");
    saveSession(data.token, data.email);
    closeAuth();
    renderAuthNav();
    updateSaveHint();
    toast("Logged in as " + data.email, "good");
    if ($("history-list")) loadHistory();
  } catch (x) {
    fail("Cannot reach the server. Is the backend running?");
  } finally {
    btn.disabled = false;
  }
}

function logout() {
  clearSession();
  renderAuthNav();
  updateSaveHint();
  toast("Logged out");
  if ($("history-list")) loadHistory();
}

function updateSaveHint() {
  const h = $("save-hint");
  if (!h) return;
  h.innerHTML = isLoggedIn()
    ? "Your analyses are saved to your history."
    : 'Log in to save analyses to a personal history. <a href="#" onclick="openAuth(\'login\');return false;">Log in</a>';
}

/* ---------- input form ---------- */
function switchTab(tab) {
  const url = tab === "url";
  $("tab-url").classList.toggle("active", url);
  $("tab-text").classList.toggle("active", !url);
  $("url-form").classList.toggle("hidden", !url);
  $("text-panel").classList.toggle("hidden", url);
  hideError();
}
const activeTab = () =>
  $("tab-url").classList.contains("active") ? "url" : "text";

function updateCount() {
  $("char-count").textContent =
    $("article-text").value.length.toLocaleString() + " characters";
}

function clearInput() {
  $("article-url").value = "";
  $("article-text").value = "";
  updateCount();
  $("results").classList.add("hidden");
  hideError();
}

function showError(msg) {
  const e = $("error-message");
  e.textContent = msg;
  e.classList.remove("hidden");
}
function hideError() {
  $("error-message").classList.add("hidden");
}

function validateArticleUrl(v) {
  if (!v) return "Paste a news article URL.";
  if (/^[^\s@\/]+@[^\s@\/]+\.[^\s@\/]+$/.test(v))
    return "That looks like an email address, not an article URL.";
  let u;
  try {
    u = new URL(v);
  } catch (e) {
    return "Enter a full URL starting with http:// or https://";
  }
  if (!["http:", "https:"].includes(u.protocol))
    return "Only http:// and https:// links are supported.";
  if (!u.hostname.includes("."))
    return "Enter a valid web address, like https://example.com/news/article";
  return "";
}

function loadExample() {
  switchTab("text");
  $("article-text").value =
    "The city council approved a 2.5 billion rupee plan on Tuesday to extend the metro line by 12 kilometres. Officials said construction will begin in March 2027 and finish within four years. The mayor said the project will reduce traffic congestion on the main highway by 20 percent. Opposition members argued that the budget is too high and called for a public review of the contracts.";
  updateCount();
}

/* ---------- analyze ---------- */
const STAGES = [
  "Extracting article...",
  "Summarizing...",
  "Extracting claims...",
  "Searching the web for evidence...",
  "Fact-checking each claim...",
];
let stageTimer = null;

function startProgress() {
  let i = 0;
  const tick = () => {
    $("stage-text").textContent = STAGES[Math.min(i, STAGES.length - 1)];
    $("bar-fill").style.width = Math.min(8 + i * 19, 92) + "%";
    i++;
  };
  $("loading").classList.remove("hidden");
  tick();
  stageTimer = setInterval(tick, 7000);
}
function stopProgress() {
  clearInterval(stageTimer);
  $("loading").classList.add("hidden");
  $("bar-fill").style.width = "5%";
}

async function analyzeArticle(e) {
  if (e) e.preventDefault();
  hideError();
  let payload;
  if (activeTab() === "url") {
    const url = $("article-url").value.trim();
    const problem = validateArticleUrl(url);
    if (problem) return showError(problem);
    payload = { url };
  } else {
    const text = $("article-text").value.trim();
    if (text.length < 100)
      return showError(
        "Paste at least a few sentences (100+ characters) of the article.",
      );
    payload = { text };
  }
  $("results").classList.add("hidden");
  $("analyze-btn").disabled = true;
  startProgress();
  try {
    const res = await authFetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok)
      throw new Error(data.error || "Analysis failed. Please try again.");
    displayResults(data);
    toast("Analysis complete", "good");
  } catch (err) {
    showError(err.message);
    toast("Analysis failed", "err");
  } finally {
    stopProgress();
    $("analyze-btn").disabled = false;
  }
}

/* ---------- results (everything shown comes from the backend response) ---------- */
function verdictInfo(v) {
  v = String(v || "")
    .toUpperCase()
    .replace(/_/g, " ");
  if (v === "SUPPORTED") return { k: "ok", label: "Supported" };
  if (v === "PARTIALLY SUPPORTED")
    return { k: "mid", label: "Partially supported" };
  if (v === "CONTRADICTED") return { k: "bad", label: "Contradicted" };
  if (v === "INSUFFICIENT EVIDENCE")
    return { k: "na", label: "Insufficient evidence" };
  return { k: "na", label: "Unable to verify" };
}

function displayResults(data) {
  const claims = Array.isArray(data.claims) ? data.claims : [];
  const n = claims.length;
  const count = { ok: 0, mid: 0, bad: 0, na: 0 };
  claims.forEach((c) => count[verdictInfo(c.verdict).k]++);
  const pct = n ? Math.round(((count.ok + 0.5 * count.mid) / n) * 100) : 0;

  const trust = {};
  claims.forEach((c) =>
    (c.evidence || []).forEach((e) => {
      const q = e.source_quality || "Unrated";
      trust[q] = (trust[q] || 0) + 1;
    }),
  );

  let summary = data.summary;
  if (summary && typeof summary === "object") summary = summary.summary || "";
  const points = Array.isArray(data.key_points) ? data.key_points : [];
  const entities = Array.isArray(data.entities) ? data.entities : [];

  const bar = ["ok", "mid", "bad", "na"]
    .map((k) =>
      count[k]
        ? `<i class="${k}" style="width:${(count[k] / n) * 100}%"></i>`
        : "",
    )
    .join("");
  const legend = [
    ["ok", "Supported"],
    ["mid", "Partially supported"],
    ["bad", "Contradicted"],
    ["na", "Insufficient / unable"],
  ]
    .map(
      ([k, t]) =>
        `<div class="${k}"><span><i class="sw"></i>${t}</span><b>${count[k]}</b></div>`,
    )
    .join("");
  const trustHtml = Object.keys(trust).length
    ? Object.entries(trust)
        .map(([q, c]) => `<div><span>${esc(q)}</span><b>${c}</b></div>`)
        .join("")
    : "<div><span>No sources retrieved</span><b>0</b></div>";

  const extras =
    (data.sentiment ? `<h4>Sentiment</h4><p>${esc(data.sentiment)}</p>` : "") +
    (data.bias ? `<h4>Bias</h4><p>${esc(data.bias)}</p>` : "") +
    (entities.length
      ? `<h4>Key entities</h4><div class="chips">${entities.map((x) => `<span class="chip">${esc(x)}</span>`).join("")}</div>`
      : "");

  const claimsHtml = n
    ? claims
        .map((c, i) => {
          const v = verdictInfo(c.verdict);
          const ev = Array.isArray(c.evidence) ? c.evidence : [];
          const srcs = ev.length
            ? ev
                .map(
                  (e) =>
                    `<div class="src"><div><a href="${esc(safeUrl(e.source_url))}" target="_blank" rel="noopener noreferrer">${esc(e.source_domain || "Unknown")}</a><small>${esc(e.source_title || "")}</small></div><span class="trust">${esc(e.source_quality || "")}</span></div>`,
                )
                .join("")
            : '<p class="hint">No external sources could be retrieved for this claim.</p>';
          return `<details class="claim ${v.k}"${i === 0 ? " open" : ""}><summary><span class="claim-text">${esc(c.claim_text)}</span><span class="vb">${v.label}</span></summary>
          <div class="claim-body"><div class="note-box">${esc(c.fact_check_note || "No notes available.")}</div><div style="margin-top:.8rem">${srcs}</div></div></details>`;
        })
        .join("")
    : '<p class="hint">No factual claims were extracted from this article.</p>';

  const box = $("results");
  box.innerHTML = `
      <div class="res-head"><h2>${esc(data.title || "Untitled article")}</h2>
        <p>Source: <a href="${esc(safeUrl(data.url))}" target="_blank" rel="noopener noreferrer">${esc(data.source || "Unknown")}</a></p></div>
      <div class="grid3">
        <div class="panel"><h3>Claim support score</h3><div class="ring" style="--p:${pct}"><span>${pct}%</span></div>
          <p class="caption">Share of ${n} claim${n === 1 ? "" : "s"} backed by evidence (partial counts half)</p></div>
        <div class="panel"><h3>Fact-check verdicts</h3><div class="stack">${bar}</div><div class="legend">${legend}</div></div>
        <div class="panel"><h3>Evidence sources by trust</h3><div class="legend">${trustHtml}</div></div>
      </div>
      <div class="grid2">
        <div class="panel"><h3>AI summary</h3><p>${esc(summary || "Summary not available.")}</p>
          ${points.length ? "<h4>Key points</h4><ul>" + points.map((p) => `<li>${esc(p)}</li>`).join("") + "</ul>" : ""}${extras}</div>
        <div class="panel"><h3>Fact-checked claims</h3>${claimsHtml}</div>
      </div>`;
  box.classList.remove("hidden");
  box.scrollIntoView({ behavior: "smooth" });
}

/* ---------- demo mode ---------- */
function runDemoMode() {
  hideError();
  displayResults({
    title: "[DEMO] AI Startup Raises $500M in Landmark Funding Round",
    source: "Demo mode, not a real article",
    url: "#",
    summary:
      "A major AI startup has secured $500 million in a Series D funding round. The funds will be used to expand research and launch new models.",
    key_points: [
      "AI startup raised $500M in Series D funding.",
      "Funds will expand research and product development.",
      "Several major tech firms participated.",
    ],
    claims: [
      {
        claim_text: "The AI startup raised $500 million in a Series D round.",
        verdict: "SUPPORTED",
        fact_check_note: "Multiple outlets confirm the $500M Series D round.",
        evidence: [
          {
            source_domain: "reuters.com",
            source_url: "#",
            source_title: "AI Startup Closes $500M Series D Round",
            source_quality: "HIGH TRUST",
          },
        ],
      },
      {
        claim_text: "The company's valuation is now $10 billion.",
        verdict: "PARTIALLY SUPPORTED",
        fact_check_note:
          "Sources cite $5 to $8 billion; $10 billion could not be confirmed.",
        evidence: [
          {
            source_domain: "bloomberg.com",
            source_url: "#",
            source_title: "AI Valuation Analysis",
            source_quality: "MEDIUM TRUST",
          },
        ],
      },
      {
        claim_text: "The startup has offices in 50 countries.",
        verdict: "INSUFFICIENT EVIDENCE",
        fact_check_note: "No reliable source could confirm this.",
        evidence: [],
      },
    ],
  });
}

/* ---------- history ---------- */
let historyItems = [];

function loadHistory() {
  const list = $("history-list");
  if (!list) return;
  if (!isLoggedIn()) {
    list.innerHTML = `<div class="card empty"><h3>Log in to see your history</h3><p>Your analyses are saved privately to your account.</p><button class="btn btn-primary" onclick="openAuth('login')">Log in</button></div>`;
    return;
  }
  list.innerHTML =
    '<div class="skel"></div><div class="skel"></div><div class="skel"></div>';
  authFetch("/history")
    .then(async (res) => {
      const data = await res.json();
      if (res.status === 401) return loadHistory();
      if (!res.ok) throw new Error(data.error || "Failed to load history");
      historyItems = data;
      renderHistory();
    })
    .catch(() => {
      list.innerHTML =
        '<div class="card empty"><h3>Could not load history</h3><p>Is the backend server running?</p></div>';
    });
}

function renderHistory() {
  const list = $("history-list");
  if (!list || !isLoggedIn()) return;
  const q = ($("history-search").value || "").toLowerCase();
  const items = historyItems.filter(
    (i) =>
      (i.title || "").toLowerCase().includes(q) ||
      (i.source || "").toLowerCase().includes(q),
  );
  if (!items.length) {
    list.innerHTML = `<div class="card empty"><h3>${historyItems.length ? "No matches" : "No analyses yet"}</h3><p>${historyItems.length ? "Try a different search." : "Analyze an article while logged in and it will appear here."}</p>${historyItems.length ? "" : '<a class="btn btn-primary" href="index.html" style="text-decoration:none;display:inline-block">Analyze an article</a>'}</div>`;
    return;
  }
  list.innerHTML = items
    .map(
      (
        i,
      ) => `<div class="card h-item"><div><h3>${esc(i.title || "Untitled")}</h3>
      <p>${esc(i.source || "Unknown")} &middot; ${i.created_at ? esc(new Date(i.created_at).toLocaleDateString()) : ""} &middot; ${Number(i.claims_count) || 0} claims</p></div>
      <div class="h-actions"><button class="btn btn-ghost" onclick="viewHistory(${Number(i.id)})">View</button>
      <button class="btn btn-ghost" onclick="deleteHistory(${Number(i.id)})">Delete</button></div></div>`,
    )
    .join("");
}

async function viewHistory(id) {
  try {
    const res = await authFetch("/history/" + id),
      data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to load");
    sessionStorage.setItem("viewResult", JSON.stringify(data));
    window.location.href = "index.html?view=" + id;
  } catch (err) {
    toast("Could not load that analysis: " + err.message, "err");
  }
}

async function deleteHistory(id) {
  if (!confirm("Delete this analysis permanently?")) return;
  try {
    const res = await authFetch("/history/" + id, { method: "DELETE" });
    if (!res.ok) throw new Error((await res.json()).error || "Delete failed");
    historyItems = historyItems.filter((i) => i.id !== id);
    renderHistory();
    toast("Analysis deleted", "good");
  } catch (err) {
    toast(err.message, "err");
  }
}

/* ---------- page load ---------- */
window.addEventListener("DOMContentLoaded", () => {
  renderHeader();
  updateSaveHint();
  if ($("history-list")) loadHistory();
  const view = new URLSearchParams(location.search).get("view");
  if (view && $("results")) {
    const stored = sessionStorage.getItem("viewResult");
    if (stored) {
      displayResults(JSON.parse(stored));
      sessionStorage.removeItem("viewResult");
    }
  }
});
