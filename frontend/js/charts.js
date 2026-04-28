/* FairGuard AI — Chart.js Utilities (dark theme) */
const FairCharts = {
    instances: {},

    defaults() {
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
        Chart.defaults.font.family = "'Inter', sans-serif";
    },

    destroy(id) {
        if (this.instances[id]) { this.instances[id].destroy(); delete this.instances[id]; }
    },

    fairnessOverview(canvasId, labels, scores) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        const colors = scores.map(s => s >= 80 ? 'rgba(16,185,129,0.8)' : s >= 60 ? 'rgba(245,158,11,0.8)' : 'rgba(239,68,68,0.8)');
        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: { labels, datasets: [{ label: 'Fairness Score %', data: scores, backgroundColor: colors, borderRadius: 6, barThickness: 36 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.04)' } }, x: { grid: { display: false } } } }
        });
    },

    groupComparison(canvasId, groups, rates, label) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        const colors = ['rgba(102,126,234,0.8)', 'rgba(0,210,255,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(239,68,68,0.8)', 'rgba(168,85,247,0.8)'];
        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: { labels: groups, datasets: [{ label: label || 'Favorable Rate %', data: rates, backgroundColor: colors.slice(0, groups.length), borderRadius: 6, barThickness: 40 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.04)' } }, x: { grid: { display: false } } } }
        });
    },

    composition(canvasId, labels, values) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        const colors = ['rgba(102,126,234,0.8)', 'rgba(0,210,255,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(239,68,68,0.8)', 'rgba(168,85,247,0.8)'];
        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: { labels, datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length), borderWidth: 0, hoverOffset: 8 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyleWidth: 10 } } }, cutout: '65%' }
        });
    },

    counterfactual(canvasId, origProb, modProb) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Negative Outcome', 'Positive Outcome'],
                datasets: [
                    { label: 'Original', data: [origProb.negative * 100, origProb.positive * 100], backgroundColor: 'rgba(102,126,234,0.8)', borderRadius: 6 },
                    { label: 'Modified', data: [modProb.negative * 100, modProb.positive * 100], backgroundColor: 'rgba(0,210,255,0.8)', borderRadius: 6 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true, max: 100, title: { display: true, text: 'Probability %' }, grid: { color: 'rgba(255,255,255,0.04)' } }, x: { grid: { display: false } } } }
        });
    },

    mitigationComparison(canvasId, before, after) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Privileged Rate', 'Unprivileged Rate'],
                datasets: [
                    { label: 'Before', data: [before.priv, before.unpriv], backgroundColor: 'rgba(239,68,68,0.7)', borderRadius: 6 },
                    { label: 'After', data: [after.priv, after.unpriv], backgroundColor: 'rgba(16,185,129,0.7)', borderRadius: 6 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.04)' } }, x: { grid: { display: false } } } }
        });
    }
};

FairCharts.defaults();
