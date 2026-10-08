const API_BASE = 'http://localhost:5000/api';

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    
    if (tab === 'url') {
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
        document.getElementById('url-input').classList.remove('hidden');
    } else {
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
        document.getElementById('text-input').classList.remove('hidden');
    }
}

function clearInput() {
    document.getElementById('article-url').value = '';
    document.getElementById('article-text').value = '';
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('error-message').classList.add('hidden');
}

async function analyzeArticle() {
    const isUrl = document.querySelector('.tab-btn.active').innerText === 'URL';
    const url = document.getElementById('article-url').value;
    const text = document.getElementById('article-text').value;
    
    const payload = {};
    if (isUrl) {
        if (!url) return showError("Please enter a URL");
        payload.url = url;
    } else {
        if (!text) return showError("Please paste article text");
        payload.text = text;
    }

    // UI State
    document.getElementById('error-message').classList.add('hidden');
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
            throw new Error(data.error || "Analysis failed");
        }

        displayResults(data);
    } catch (err) {
        showError(err.message);
    } finally {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('analyze-btn').disabled = false;
    }
}

function showError(msg) {
    const errEl = document.getElementById('error-message');
    if(errEl) {
        errEl.innerText = msg;
        errEl.classList.remove('hidden');
    }
}

function displayResults(data) {
    document.getElementById('results-section').classList.remove('hidden');
    
    // Article Info
    document.getElementById('res-title').innerText = data.title || "Untitled Article";
    const sourceEl = document.getElementById('res-source');
    sourceEl.innerText = data.source;
    sourceEl.href = data.url || "#";
    
    // Summary
    document.getElementById('res-summary').innerText = data.summary;
    const kpEl = document.getElementById('res-key-points');
    kpEl.innerHTML = '';
    if (data.key_points && Array.isArray(data.key_points)) {
        data.key_points.forEach(kp => {
            const li = document.createElement('li');
            li.innerText = kp;
            kpEl.appendChild(li);
        });
    }

    // Claims and Stats
    let supported = 0, partial = 0, contradicted = 0, insufficient = 0;
    
    const claimsContainer = document.getElementById('claims-container');
    claimsContainer.innerHTML = '';
    
    if (data.claims && data.claims.length > 0) {
        data.claims.forEach((claim, idx) => {
            // Stats
            const v = claim.verdict || "";
            if (v.includes('SUPPORTED') && !v.includes('PARTIALLY')) supported++;
            else if (v.includes('PARTIALLY')) partial++;
            else if (v.includes('CONTRADICTED')) contradicted++;
            else insufficient++;

            // Card
            let vClass = 'verdict-UNABLE';
            let vIcon = '⚫';
            if (v.includes('SUPPORTED') && !v.includes('PARTIALLY')) { vClass = 'verdict-SUPPORTED'; vIcon='🟢'; }
            else if (v.includes('PARTIALLY')) { vClass = 'verdict-PARTIALLY'; vIcon='🟡'; }
            else if (v.includes('CONTRADICTED')) { vClass = 'verdict-CONTRADICTED'; vIcon='🔴'; }
            else if (v.includes('INSUFFICIENT')) { vClass = 'verdict-INSUFFICIENT'; vIcon='⚪'; }

            let evidenceHtml = '';
            if (claim.evidence && claim.evidence.length > 0) {
                evidenceHtml = `
                    <div class="evidence-list">
                        <h5>Evidence Sources:</h5>
                        ${claim.evidence.map(e => `
                            <div class="evidence-item">
                                <a href="${e.source_url}" target="_blank">${e.source_domain}</a> 
                                <span class="trust-badge">${e.source_quality}</span>
                                <div>${e.source_title}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                evidenceHtml = `<p class="small-text">No sources could be retrieved.</p>`;
            }

            const html = `
                <div class="claim-card">
                    <div class="claim-header">Claim #${idx + 1}: "${claim.claim_text}"</div>
                    <div class="verdict-badge ${vClass}">${vIcon} ${claim.verdict}</div>
                    <div class="note-box">
                        <strong>Fact-check Note:</strong> ${claim.fact_check_note}
                    </div>
                    ${evidenceHtml}
                </div>
            `;
            claimsContainer.innerHTML += html;
        });
    } else {
        claimsContainer.innerHTML = '<p>No factual claims extracted.</p>';
    }

    // Update Stats
    document.getElementById('total-claims').innerText = (data.claims || []).length;
    document.getElementById('supported-claims').innerText = supported;
    document.getElementById('partial-claims').innerText = partial;
    document.getElementById('contradicted-claims').innerText = contradicted;
    document.getElementById('insufficient-claims').innerText = insufficient;
}

// History logic
async function loadHistory() {
    const tableBody = document.getElementById('history-body');
    if (!tableBody) return; // not on history page
    
    document.getElementById('loading').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/history`);
        const data = await response.json();
        
        document.getElementById('loading').classList.add('hidden');
        
        if (data.length === 0) {
            document.getElementById('no-history').classList.remove('hidden');
            document.querySelector('.table-container').classList.add('hidden');
            return;
        }
        
        tableBody.innerHTML = '';
        data.forEach(item => {
            const date = new Date(item.created_at).toLocaleDateString();
            tableBody.innerHTML += `
                <tr>
                    <td>${date}</td>
                    <td>${item.title || "Untitled"}</td>
                    <td>${item.source.substring(0, 30)}...</td>
                    <td>${item.claims_count}</td>
                    <td>
                        <button class="btn btn-secondary" onclick="viewHistory(${item.id})" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">View</button>
                    </td>
                </tr>
            `;
        });
    } catch (err) {
        document.getElementById('loading').classList.add('hidden');
        showError("Failed to load history");
    }
}

function viewHistory(id) {
    alert("Viewing past analysis directly from history page is not fully implemented in the UI yet. Check the API directly via GET /api/history/" + id);
}

function runDemoMode() {
    // Demo data for academic presentation
    const demoData = {
        title: "[Demo Data] Economic Growth Reaches New Heights in 2026",
        source: "Demo News Outlet",
        url: "#",
        summary: "The economy has experienced significant growth over the past year. Tech sector innovations and new policy changes are credited for this rapid expansion.",
        key_points: [
            "Economy grew by 7.8% in Q1.",
            "Tech sector stocks surged.",
            "New trade policy implemented."
        ],
        claims: [
            {
                claim_text: "The economy grew by 7.8% in Q1 of 2026.",
                verdict: "SUPPORTED",
                fact_check_note: "Official government statistical data confirms the 7.8% GDP growth in the specified quarter.",
                evidence: [
                    {
                        source_domain: "gov.statistics",
                        source_url: "#",
                        source_title: "Q1 2026 GDP Growth Report",
                        source_quality: "HIGH TRUST"
                    }
                ]
            },
            {
                claim_text: "The new AI act bans all open-source models.",
                verdict: "CONTRADICTED",
                fact_check_note: "The AI act specifically protects and exempts open-source models under certain conditions, rather than banning them.",
                evidence: [
                    {
                        source_domain: "legaltech.org",
                        source_url: "#",
                        source_title: "Understanding the New AI Act",
                        source_quality: "MEDIUM TRUST"
                    }
                ]
            },
            {
                claim_text: "Company Z fired 50,000 employees last week.",
                verdict: "INSUFFICIENT EVIDENCE",
                fact_check_note: "No credible news outlets or company filings report a 50,000 employee layoff at Company Z.",
                evidence: []
            }
        ]
    };
    
    document.getElementById('error-message').classList.add('hidden');
    displayResults(demoData);
}
