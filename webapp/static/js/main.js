/**
 * GTM AI Operations Hub — Main JavaScript
 * Handles: AI Status polling, Kanban drag-and-drop, Chart.js, AJAX forms
 */

// ─────────── AI Status Monitor ───────────

class AIStatusMonitor {
    constructor() {
        this.badge = document.getElementById('ai-status-badge');
        this.label = document.getElementById('ai-status-label');
        this.latency = document.getElementById('ai-status-latency');
        this.interval = null;
        this.consecutiveErrors = 0;

        if (this.badge) this.start();
    }

    start() {
        this.check();
        this.interval = setInterval(() => this.check(), 30000);
    }

    async check() {
        if (!this.badge) return;

        this.badge.setAttribute('data-status', 'checking');
        this.label.textContent = 'Checking…';
        this.latency.textContent = '';

        try {
            const resp = await fetch('/api/ai-status');
            const data = await resp.json();

            this.badge.setAttribute('data-status', data.status);
            this.consecutiveErrors = 0;

            switch (data.status) {
                case 'connected':
                    this.label.textContent = 'AI Connected';
                    this.latency.textContent = data.latency_ms ? `${data.latency_ms}ms` : '';
                    // Slow poll when connected
                    this.setInterval(30000);
                    break;
                case 'disconnected':
                    this.label.textContent = 'AI Disconnected';
                    this.latency.textContent = data.latency_ms ? `${data.latency_ms}ms` : '';
                    // Faster retry
                    this.setInterval(15000);
                    break;
                case 'no_token':
                    this.label.textContent = 'Mock Mode';
                    this.latency.textContent = '';
                    this.setInterval(60000);
                    break;
                default:
                    this.label.textContent = 'Unknown';
            }
        } catch (err) {
            this.consecutiveErrors++;
            this.badge.setAttribute('data-status', 'disconnected');
            this.label.textContent = 'Server Error';
            this.latency.textContent = '';

            if (this.consecutiveErrors > 3) {
                this.setInterval(60000);
            }
        }
    }

    setInterval(ms) {
        if (this.interval) clearInterval(this.interval);
        this.interval = setInterval(() => this.check(), ms);
    }
}

// ─────────── Kanban Drag & Drop ───────────

function initKanban() {
    const cards = document.querySelectorAll('.kanban-card[draggable="true"]');
    const columns = document.querySelectorAll('.kanban-cards');

    cards.forEach(card => {
        card.addEventListener('dragstart', (e) => {
            card.classList.add('dragging');
            e.dataTransfer.setData('text/plain', card.dataset.itemId);
            e.dataTransfer.effectAllowed = 'move';
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            document.querySelectorAll('.kanban-column.drag-over').forEach(c => c.classList.remove('drag-over'));
        });
    });

    columns.forEach(col => {
        col.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            col.closest('.kanban-column').classList.add('drag-over');
        });

        col.addEventListener('dragleave', () => {
            col.closest('.kanban-column').classList.remove('drag-over');
        });

        col.addEventListener('drop', async (e) => {
            e.preventDefault();
            const column = col.closest('.kanban-column');
            column.classList.remove('drag-over');

            const itemId = e.dataTransfer.getData('text/plain');
            const newStatus = column.dataset.status;

            if (!itemId || !newStatus) return;

            // Optimistic UI update
            const card = document.querySelector(`.kanban-card[data-item-id="${itemId}"]`);
            if (card) {
                col.appendChild(card);
                updateColumnCounts();
            }

            // Persist to server
            try {
                const form = new FormData();
                form.append('item_id', itemId);
                form.append('new_status', newStatus);
                const resp = await fetch('/backlog/update', { method: 'POST', body: form });
                const data = await resp.json();
                if (!data.success) {
                    console.error('Update failed:', data.error);
                    location.reload();
                }
            } catch (err) {
                console.error('Drag update error:', err);
                location.reload();
            }
        });
    });
}

function updateColumnCounts() {
    document.querySelectorAll('.kanban-column').forEach(col => {
        const count = col.querySelectorAll('.kanban-card').length;
        const badge = col.querySelector('.kanban-column-count');
        if (badge) badge.textContent = count;
    });
}

// ─────────── Blueprint Generator ───────────

async function generateBlueprint(requestId) {
    const btn = document.getElementById('generate-blueprint-btn');
    const output = document.getElementById('blueprint-output');

    if (!btn || !output) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generating…';
    output.innerHTML = '<div class="empty-state"><div class="spinner"></div><p style="margin-top: 12px;">AI is generating your workflow blueprint…</p></div>';

    try {
        const resp = await fetch(`/builder/${requestId}/generate`, { method: 'POST' });
        const data = await resp.json();

        if (data.success && data.blueprint) {
            const bp = data.blueprint;
            let html = `<div class="result-panel success fade-in">`;
            html += `<div class="result-header"><span>✨</span><h3>${bp.workflow_name || 'Workflow Blueprint'}</h3>`;
            html += `<span class="badge ${bp._source === 'llm' ? 'badge-green' : 'badge-yellow'}">${bp._source === 'llm' ? 'AI Generated' : 'Mock'}</span></div>`;

            if (bp.current_state) {
                html += `<div class="blueprint-section"><h4>📋 Current State (Manual)</h4><ul class="blueprint-list">`;
                (Array.isArray(bp.current_state) ? bp.current_state : [bp.current_state]).forEach(s => { html += `<li>${s}</li>`; });
                html += `</ul></div>`;
            }

            html += `<div class="blueprint-arrow">⬇️ AI Transformation ⬇️</div>`;

            if (bp.proposed_state) {
                html += `<div class="blueprint-section"><h4>🚀 Proposed State (AI-Assisted)</h4><ul class="blueprint-list">`;
                (Array.isArray(bp.proposed_state) ? bp.proposed_state : [bp.proposed_state]).forEach(s => { html += `<li>${s}</li>`; });
                html += `</ul></div>`;
            }

            if (bp.integrations) {
                html += `<div class="blueprint-section"><h4>🔗 Integrations</h4><div style="display:flex;gap:8px;flex-wrap:wrap;">`;
                (Array.isArray(bp.integrations) ? bp.integrations : [bp.integrations]).forEach(i => { html += `<span class="badge badge-blue">${i}</span>`; });
                html += `</div></div>`;
            }

            if (bp.estimated_time_savings) {
                html += `<div class="blueprint-section" style="margin-top:16px;"><span class="badge badge-green">⏱ Est. Time Savings: ${bp.estimated_time_savings}</span></div>`;
            }

            html += `</div>`;
            output.innerHTML = html;
        } else {
            output.innerHTML = `<div class="error-banner">Failed to generate: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (err) {
        output.innerHTML = `<div class="error-banner">Error: ${err.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🧠 Generate Blueprint';
    }
}

// ─────────── Prompt Lab ───────────

async function submitPrompt(requestId) {
    const textarea = document.getElementById('prompt-input');
    const output = document.getElementById('prompt-output');
    const btn = document.getElementById('prompt-submit-btn');

    if (!textarea || !output || !btn) return;

    const promptText = textarea.value.trim();
    if (!promptText) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Running…';

    try {
        const form = new FormData();
        form.append('prompt_text', promptText);

        const resp = await fetch(`/builder/${requestId}/prompt-lab`, { method: 'POST', body: form });
        const data = await resp.json();

        if (data.success) {
            output.innerHTML = `
                <div class="result-panel success fade-in">
                    <div class="result-header">
                        <span>📝</span>
                        <h3>Version ${data.version}</h3>
                        <span class="badge ${data.source === 'llm' ? 'badge-green' : 'badge-yellow'}">${data.source === 'llm' ? 'AI' : 'Mock'}</span>
                    </div>
                    <div class="result-body"><pre>${escapeHtml(data.response)}</pre></div>
                </div>`;
        } else {
            output.innerHTML = `<div class="error-banner">${data.error}</div>`;
        }
    } catch (err) {
        output.innerHTML = `<div class="error-banner">${err.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '▶ Run Prompt';
    }
}

// ─────────── Impact Charts ───────────

function initImpactCharts() {
    const timeCanvas = document.getElementById('time-savings-chart');
    const roiCanvas = document.getElementById('roi-chart');

    if (!timeCanvas && !roiCanvas) return;
    if (typeof Chart === 'undefined') return;

    Chart.defaults.color = '#4b5563';
    Chart.defaults.borderColor = '#e2e5ea';
    Chart.defaults.font.family = "'Inter', sans-serif";

    // Time Savings Chart
    if (timeCanvas) {
        const ctx = timeCanvas.getContext('2d');
        const labels = JSON.parse(timeCanvas.dataset.labels || '[]');
        const beforeData = JSON.parse(timeCanvas.dataset.before || '[]');
        const afterData = JSON.parse(timeCanvas.dataset.after || '[]');

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Manual (hrs/wk)',
                        data: beforeData,
                        backgroundColor: 'rgba(248, 113, 113, 0.7)',
                        borderRadius: 6,
                    },
                    {
                        label: 'AI-Assisted (hrs/wk)',
                        data: afterData,
                        backgroundColor: 'rgba(52, 211, 153, 0.7)',
                        borderRadius: 6,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#e2e5ea' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // ROI Chart
    if (roiCanvas) {
        const ctx = roiCanvas.getContext('2d');
        const labels = JSON.parse(roiCanvas.dataset.labels || '[]');
        const roiData = JSON.parse(roiCanvas.dataset.roi || '[]');

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: roiData,
                    backgroundColor: [
                        'rgba(79, 143, 247, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(52, 211, 153, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                    ],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: { position: 'right' }
                }
            }
        });
    }
}

// ─────────── Utilities ───────────

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ─────────── Init ───────────

document.addEventListener('DOMContentLoaded', () => {
    new AIStatusMonitor();
    initKanban();
    initImpactCharts();
});
