const API_BASE = 'http://localhost:5000/api';

// Tab switching
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    if (tab === 'url') {
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
        document.getElementById('url-input').classList.remove('hidden');
    } else {
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
        document.getElementById('text-input').classList.remove('hidden');
    }
}

function clearInput() {
    const urlEl = document.getElementById('article-url');
    const textEl = document.getElementById('article-text');
    if (urlEl) urlEl.value = '';
    if (textEl) textEl.value = '';
    const resultsEl = document.getElementById('results-section');
    if (resultsEl) resultsEl.classList.add('hidden');
    hideError();
}

function showError(msg) {
    const errEl = document.getElementById('error-message');
    if (errEl) {
        errEl.innerText = '⚠️ ' + msg;
        errEl.classList.remove('hidden');
    }
}

function hideError() {
    const errEl = document.getElementById('error-message');
    if (errEl) errEl.classList.add('hidden');
}

async function analyzeArticle() {
    const activeTab = document.querySelector('.tab-btn.active');
    const isUrl = activeTab && activeTab.innerText.trim() === 'URL';
    const urlEl = document.getElementById('article-url');
    const textEl = document.getElementById('article-text');
    const url = urlEl ? urlEl.value.trim() : '';
    const text = textEl ? textEl.value.trim() : '';

    hideError();

    if (isUrl && !url) return showError("Please enter a news article URL.");
    if (!isUrl && !text) return showError("Please paste the news article text.");

    const payload = isUrl ? { url } : { text };

    // UI: show loading
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('analyze-btn').disabled = true;

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed. Please try again.');
        }

        displayResults(data);
    } catch (err) {
        showError(err.message);
    } finally {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('analyze-btn').disabled = false;
    }
}

function displayResults(data) {
    document.getElementById('results-section').classList.remove('hidden');

    // Article info
    document.getElementById('res-title').innerText = data.title || 'Untitled Article';
    const sourceEl = document.getElementById('res-source');
    if (sourceEl) {
        sourceEl.innerText = data.source || 'Unknown';
        sourceEl.href = data.url || '#';
    }

    // Summary — handle both string and object
    const summaryEl = document.getElementById('res-summary');
    if (summaryEl) {
        if (typeof data.summary === 'string') {
            summaryEl.innerText = data.summary;
        } else if (data.summary && typeof data.summary === 'object') {
            summaryEl.innerText = data.summary.summary || JSON.stringify(data.summary);
        } else {
            summaryEl.innerText = 'Summary not available.';
        }
    }

    // Key points
    const kpEl = document.getElementById('res-key-points');
    if (kpEl) {
        kpEl.innerHTML = '';
        const keyPoints = Array.isArray(data.key_points) ? data.key_points : [];
        if (keyPoints.length === 0) {
            kpEl.innerHTML = '<li>No key points extracted.</li>';
        } else {
            keyPoints.forEach(kp => {
                const li = document.createElement('li');
                li.innerText = kp;
                kpEl.appendChild(li);
            });
        }
    }

    // Claims and stats
    const claims = Array.isArray(data.claims) ? data.claims : [];
    let supported = 0, partial = 0, contradicted = 0, insufficient = 0;

    const claimsContainer = document.getElementById('claims-container');
    if (claimsContainer) {
        claimsContainer.innerHTML = '';

        if (claims.length === 0) {
            claimsContainer.innerHTML = '<p style="color:#64748b;">No factual claims were extracted from this article.</p>';
        } else {
            claims.forEach((claim, idx) => {
                const v = (claim.verdict || '').toUpperCase();

                // Count for stats
                if (v === 'SUPPORTED') supported++;
                else if (v === 'PARTIALLY SUPPORTED') partial++;
                else if (v === 'CONTRADICTED') contradicted++;
                else insufficient++;

                // Verdict styling
                let vClass = 'verdict-UNABLE';
                let vIcon = '⚫';
                if (v === 'SUPPORTED') { vClass = 'verdict-SUPPORTED'; vIcon = '🟢'; }
                else if (v === 'PARTIALLY SUPPORTED') { vClass = 'verdict-PARTIALLY'; vIcon = '🟡'; }
                else if (v === 'CONTRADICTED') { vClass = 'verdict-CONTRADICTED'; vIcon = '🔴'; }
                else if (v === 'INSUFFICIENT EVIDENCE') { vClass = 'verdict-INSUFFICIENT'; vIcon = '⚪'; }

                // Evidence
                const evidence = Array.isArray(claim.evidence) ? claim.evidence : [];
                let evidenceHtml = '';
                if (evidence.length > 0) {
                    evidenceHtml = `<div class="evidence-list"><strong>Evidence Sources:</strong>`;
                    evidence.forEach(e => {
                        evidenceHtml += `
                        <div class="evidence-item">
                            <a href="${e.source_url || '#'}" target="_blank">${e.source_domain || 'Unknown'}</a>
                            <span class="trust-badge">${e.source_quality || ''}</span>
                            <div style="color:#64748b; font-size:0.85rem;">${e.source_title || ''}</div>
                        </div>`;
                    });
                    evidenceHtml += `</div>`;
                } else {
                    evidenceHtml = `<p style="color:#94a3b8; font-size:0.9rem;">⚠️ No external sources could be retrieved for this claim.</p>`;
                }

                claimsContainer.innerHTML += `
                <div class="claim-card">
                    <div class="claim-header">Claim #${idx + 1}</div>
                    <p style="margin-bottom:1rem;">"${claim.claim_text}"</p>
                    <span class="verdict-badge ${vClass}">${vIcon} ${claim.verdict || 'UNABLE TO VERIFY'}</span>
                    <div class="note-box">
                        <strong>Fact-check Note:</strong><br>${claim.fact_check_note || 'No notes available.'}
                    </div>
                    ${evidenceHtml}
                </div>`;
            });
        }
    }

    // Update stats
    document.getElementById('total-claims').innerText = claims.length;
    document.getElementById('supported-claims').innerText = supported;
    document.getElementById('partial-claims').innerText = partial;
    document.getElementById('contradicted-claims').innerText = contradicted;
    document.getElementById('insufficient-claims').innerText = insufficient;

    // Scroll to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

// ---- DEMO MODE ----
function runDemoMode() {
    hideError();
    const demoData = {
        title: "[DEMO] AI Startup Raises $500M in Landmark Funding Round",
        source: "Demo Mode — Not a real article",
        url: "#",
        summary: "A major AI startup has secured $500 million in a Series D funding round, one of the largest in the industry this year. The funds will be used to expand their research team and launch new AI models. Several major tech firms participated in the round.",
        key_points: [
            "AI startup raised $500M in Series D funding.",
            "Funding will be used to expand research and product development.",
            "Several major tech firms participated as investors.",
            "The startup plans to launch 3 new AI models next year.",
            "Total valuation now stands at $5 billion."
        ],
        claims: [
            {
                claim_text: "The AI startup raised $500 million in a Series D round.",
                verdict: "SUPPORTED",
                fact_check_note: "Multiple financial news outlets and official press releases confirm the $500M Series D funding round closed this quarter.",
                evidence: [
                    { source_domain: "reuters.com", source_url: "#", source_title: "AI Startup Closes $500M Series D Round", source_quality: "MEDIUM TRUST" },
                    { source_domain: "techcrunch.com", source_url: "#", source_title: "Landmark AI Funding Round Closes", source_quality: "MEDIUM TRUST" }
                ]
            },
            {
                claim_text: "The company's total valuation is now $10 billion.",
                verdict: "PARTIALLY SUPPORTED",
                fact_check_note: "Some sources cite a $5 billion valuation while others estimate up to $8 billion. The $10 billion figure could not be confirmed.",
                evidence: [
                    { source_domain: "bloomberg.com", source_url: "#", source_title: "AI Valuation Analysis Q4", source_quality: "MEDIUM TRUST" }
                ]
            },
            {
                claim_text: "The startup has offices in 50 countries.",
                verdict: "INSUFFICIENT EVIDENCE",
                fact_check_note: "No reliable external sources could confirm the number of countries the startup operates in.",
                evidence: []
            }
        ]
    };
    displayResults(demoData);
}

// ---- HISTORY PAGE ----
async function loadHistory() {
    const tableBody = document.getElementById('history-body');
    if (!tableBody) return;

    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/history`);
        const data = await response.json();

        if (loadingEl) loadingEl.classList.add('hidden');

        if (!data || data.length === 0) {
            const noHistEl = document.getElementById('no-history');
            if (noHistEl) noHistEl.classList.remove('hidden');
            const tableContainer = document.querySelector('.table-container');
            if (tableContainer) tableContainer.classList.add('hidden');
            return;
        }

        tableBody.innerHTML = '';
        data.forEach(item => {
            const date = new Date(item.created_at).toLocaleDateString();
            const source = (item.source || 'Unknown').substring(0, 40);
            tableBody.innerHTML += `
            <tr>
                <td>${date}</td>
                <td>${item.title || 'Untitled'}</td>
                <td>${source}</td>
                <td>${item.claims_count || 0}</td>
                <td>
                    <button class="btn btn-secondary" onclick="viewHistory(${item.id})"
                        style="padding:0.25rem 0.75rem; font-size:0.85rem;">
                        View
                    </button>
                </td>
            </tr>`;
        });
    } catch (err) {
        if (loadingEl) loadingEl.classList.add('hidden');
        showError('Failed to load history. Is the backend server running?');
    }
}

async function viewHistory(id) {
    try {
        const response = await fetch(`${API_BASE}/history/${id}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to load');

        // Store data and redirect to index page
        sessionStorage.setItem('viewResult', JSON.stringify(data));
        window.location.href = 'index.html?view=' + id;
    } catch (err) {
        alert('Could not load that analysis: ' + err.message);
    }
}

// On page load — check if we came from history
window.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('view')) {
        const stored = sessionStorage.getItem('viewResult');
        if (stored) {
            displayResults(JSON.parse(stored));
            sessionStorage.removeItem('viewResult');
        }
    }
});
