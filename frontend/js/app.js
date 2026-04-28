/* FairGuard AI — Main Application Controller */
const FairGuard = {
    state: {
        currentPage: 'dashboard',
        datasetId: null,
        datasetInfo: null,
        protectedAttrs: [],
        analysisResult: null,
        stats: { datasets: 0, analyses: 0, reports: 0, alerts: 0 }
    },

    init() {
        this.bindNavigation();
        this.bindUpload();
        this.bindAnalysis();
        this.bindCounterfactual();
        this.bindReports();
        this.bindSettings();
        this.loadSavedKey();
        this.showPage('dashboard');
        this.toast('Welcome to FairGuard AI!', 'info');
    },

    // === Navigation ===
    showPage(page) {
        document.querySelectorAll('.page-container').forEach(p => p.classList.add('page-hidden'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const el = document.getElementById('page-' + page);
        if (el) { el.classList.remove('page-hidden'); el.style.animation = 'none'; el.offsetHeight; el.style.animation = 'fadeIn 0.4s ease'; }
        const nav = document.querySelector(`[data-page="${page}"]`);
        if (nav) nav.classList.add('active');
        const titles = { dashboard:'Dashboard', upload:'Upload Dataset', analysis:'Bias Analysis', counterfactual:'What-If Analysis', reports:'Reports', settings:'Settings' };
        document.getElementById('page-title').textContent = titles[page] || page;
        this.state.currentPage = page;
    },

    bindNavigation() {
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', () => this.showPage(btn.dataset.page));
        });
    },

    // === Toast ===
    toast(msg, type = 'info') {
        const c = document.getElementById('toast-container');
        const icons = { success: '✅', error: '❌', info: 'ℹ️' };
        const t = document.createElement('div');
        t.className = 'toast ' + type;
        t.innerHTML = `<span>${icons[type] || ''}</span><span>${msg}</span>`;
        c.appendChild(t);
        setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 4000);
    },

    addActivity(text, color = 'blue') {
        const list = document.getElementById('activity-list');
        const li = document.createElement('li');
        li.className = 'activity-item';
        li.innerHTML = `<span class="activity-dot ${color}"></span><div><div class="activity-text">${text}</div><div class="activity-time">Just now</div></div>`;
        list.prepend(li);
        if (list.children.length > 10) list.lastChild.remove();
    },

    updateStats() {
        const s = this.state.stats;
        document.getElementById('stat-datasets').textContent = s.datasets;
        document.getElementById('stat-analyses').textContent = s.analyses;
        document.getElementById('stat-reports').textContent = s.reports;
        document.getElementById('stat-alerts').textContent = s.alerts;
    },

    // === Upload ===
    bindUpload() {
        const zone = document.getElementById('upload-zone');
        const input = document.getElementById('file-input');
        zone.addEventListener('click', () => input.click());
        zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
        zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
        zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('dragover'); if (e.dataTransfer.files.length) this.handleFile(e.dataTransfer.files[0]); });
        input.addEventListener('change', e => { if (e.target.files.length) this.handleFile(e.target.files[0]); });
        document.getElementById('btn-sample-data').addEventListener('click', () => this.loadSample());
        document.getElementById('btn-run-analysis').addEventListener('click', () => { this.showPage('analysis'); this.prepareAnalysisForm(); });
    },

    async handleFile(file) {
        if (!file.name.endsWith('.csv')) { this.toast('Please upload a CSV file', 'error'); return; }
        try {
            this.toast('Uploading dataset...', 'info');
            const data = await API.uploadFile(file);
            this.onDatasetLoaded(data);
        } catch (e) { this.toast(e.message, 'error'); }
    },

    async loadSample() {
        try {
            this.toast('Loading sample hiring dataset...', 'info');
            const data = await API.loadSampleDataset();
            this.onDatasetLoaded(data);
        } catch (e) { this.toast(e.message, 'error'); }
    },

    onDatasetLoaded(data) {
        this.state.datasetId = data.dataset_id;
        this.state.datasetInfo = data;
        this.state.protectedAttrs = data.protected_attributes || [];
        this.state.stats.datasets++;
        this.updateStats();
        document.getElementById('dataset-badge').textContent = `${data.dataset_id} (${data.rows} rows)`;
        this.renderPreview(data);
        this.addActivity(`Dataset loaded: ${data.dataset_id} (${data.rows} rows)`, 'green');
        this.toast('Dataset loaded successfully!', 'success');
    },

    renderPreview(data) {
        const section = document.getElementById('preview-section');
        section.classList.remove('page-hidden');
        document.getElementById('preview-info').textContent = `${data.rows} rows × ${data.columns.length} cols`;

        // Table
        const thead = document.querySelector('#preview-table thead');
        const tbody = document.querySelector('#preview-table tbody');
        thead.innerHTML = '<tr>' + data.columns.map(c => `<th>${c.name}</th>`).join('') + '</tr>';
        tbody.innerHTML = data.preview.slice(0, 8).map(row =>
            '<tr>' + data.columns.map(c => `<td>${row[c.name] ?? ''}</td>`).join('') + '</tr>'
        ).join('');

        // Protected attributes
        const pal = document.getElementById('protected-attrs-list');
        if (data.protected_attributes.length) {
            pal.innerHTML = data.protected_attributes.map(a =>
                `<span class="risk-badge risk-medium" style="margin:4px">${a.column} (${a.unique_values.join(', ')})</span>`
            ).join('');
        } else {
            pal.innerHTML = '<p style="color:var(--text-muted)">No protected attributes auto-detected. You can select manually in analysis.</p>';
        }
    },

    // === Analysis ===
    bindAnalysis() {
        document.getElementById('btn-analyze').addEventListener('click', () => this.runAnalysis());
        document.getElementById('btn-explain').addEventListener('click', () => this.getExplanation());
        document.getElementById('btn-mitigate').addEventListener('click', () => this.runMitigation('reweighing'));
        document.getElementById('btn-mitigate-sampling').addEventListener('click', () => this.runMitigation('sampling'));
        document.getElementById('btn-save-key').addEventListener('click', () => this.saveApiKey());
        document.getElementById('analysis-protected-col').addEventListener('change', () => this.updatePrivValues());
    },

    prepareAnalysisForm() {
        if (!this.state.datasetInfo) { return; }
        document.getElementById('analysis-empty').classList.add('page-hidden');
        document.getElementById('analysis-results').classList.remove('page-hidden');

        const info = this.state.datasetInfo;
        const protSel = document.getElementById('analysis-protected-col');
        const labelSel = document.getElementById('analysis-label-col');

        // Populate protected col dropdown
        protSel.innerHTML = '';
        if (this.state.protectedAttrs.length) {
            this.state.protectedAttrs.forEach(a => {
                protSel.innerHTML += `<option value="${a.column}">${a.column}</option>`;
            });
        }
        info.columns.forEach(c => {
            if (!this.state.protectedAttrs.find(a => a.column === c.name)) {
                protSel.innerHTML += `<option value="${c.name}">${c.name}</option>`;
            }
        });

        // Populate label col dropdown
        labelSel.innerHTML = '';
        const likelylabels = info.columns.filter(c => c.unique_count <= 10 || c.name.toLowerCase().includes('hired') || c.name.toLowerCase().includes('label') || c.name.toLowerCase().includes('target'));
        const others = info.columns.filter(c => !likelylabels.includes(c));
        likelylabels.forEach(c => { labelSel.innerHTML += `<option value="${c.name}">${c.name}</option>`; });
        others.forEach(c => { labelSel.innerHTML += `<option value="${c.name}">${c.name}</option>`; });

        // Pre-select 'hired' if present
        const hiredOpt = Array.from(labelSel.options).find(o => o.value.toLowerCase() === 'hired');
        if (hiredOpt) hiredOpt.selected = true;

        this.updatePrivValues();
    },

    updatePrivValues() {
        const col = document.getElementById('analysis-protected-col').value;
        const privSel = document.getElementById('analysis-priv-value');
        privSel.innerHTML = '';
        const attr = this.state.protectedAttrs.find(a => a.column === col);
        if (attr) {
            attr.unique_values.forEach(v => { privSel.innerHTML += `<option value="${v}">${v}</option>`; });
        } else {
            const colInfo = this.state.datasetInfo.columns.find(c => c.name === col);
            if (colInfo) colInfo.sample_values.forEach(v => { privSel.innerHTML += `<option value="${v}">${v}</option>`; });
        }
    },

    async runAnalysis() {
        if (!this.state.datasetId) { this.toast('Load a dataset first', 'error'); return; }
        const protCol = document.getElementById('analysis-protected-col').value;
        const labelCol = document.getElementById('analysis-label-col').value;
        const privVal = document.getElementById('analysis-priv-value').value;

        document.getElementById('analysis-loading').classList.remove('page-hidden');
        document.getElementById('analysis-metrics').classList.add('page-hidden');

        try {
            const result = await API.analyze(this.state.datasetId, labelCol, protCol, privVal);
            this.state.analysisResult = result;
            this.state.stats.analyses++;
            if (result.risk_level === 'HIGH') this.state.stats.alerts++;
            this.updateStats();
            this.renderAnalysisResults(result);
            this.addActivity(`Bias analysis complete: ${protCol} — Risk: ${result.risk_level}`, result.risk_level === 'HIGH' ? 'red' : result.risk_level === 'MEDIUM' ? 'yellow' : 'green');
            this.toast('Analysis complete!', 'success');
        } catch (e) {
            this.toast(e.message, 'error');
        } finally {
            document.getElementById('analysis-loading').classList.add('page-hidden');
        }
    },

    renderAnalysisResults(result) {
        document.getElementById('analysis-metrics').classList.remove('page-hidden');

        // Risk badge
        const rb = document.getElementById('analysis-risk-badge');
        const rc = { LOW: 'risk-low', MEDIUM: 'risk-medium', HIGH: 'risk-high' };
        const ri = { LOW: '🟢', MEDIUM: '🟡', HIGH: '🔴' };
        rb.innerHTML = `<span class="risk-badge ${rc[result.risk_level]}">${ri[result.risk_level]} ${result.risk_level} RISK</span>`;

        // Metric cards
        const m = result.metrics;
        const cards = [
            { name: 'Statistical Parity Diff', value: m.statistical_parity_difference, threshold: 0.1, desc: 'Ideal: 0 | Acceptable: ±0.1' },
            { name: 'Disparate Impact Ratio', value: m.disparate_impact_ratio, threshold: null, desc: 'Ideal: 1.0 | Legal: 0.8–1.25' },
            { name: 'Privileged Favorable Rate', value: m.privileged_favorable_rate + '%', threshold: null, desc: result.privileged_value + ' group' },
            { name: 'Unprivileged Favorable Rate', value: m.unprivileged_favorable_rate + '%', threshold: null, desc: 'Other groups' },
        ];

        document.getElementById('metrics-cards').innerHTML = cards.map(c => {
            let status = '', statusClass = '';
            if (c.name === 'Statistical Parity Diff') {
                const v = Math.abs(parseFloat(c.value));
                status = v <= 0.1 ? '✅ Pass' : v <= 0.2 ? '⚠️ Warning' : '❌ Fail';
                statusClass = v <= 0.1 ? 'status-pass' : v <= 0.2 ? 'status-warn' : 'status-fail';
            } else if (c.name === 'Disparate Impact Ratio') {
                const v = parseFloat(c.value);
                status = (v >= 0.8 && v <= 1.25) ? '✅ Pass' : '❌ Fail (80% rule)';
                statusClass = (v >= 0.8 && v <= 1.25) ? 'status-pass' : 'status-fail';
            }
            return `<div class="metric-card"><div class="metric-name">${c.name}</div><div class="metric-value-large">${c.value}</div><div class="metric-status ${statusClass}">${status}</div><div style="font-size:12px;color:var(--text-muted);margin-top:8px">${c.desc}</div></div>`;
        }).join('');

        // Group comparison chart
        const gs = result.group_stats;
        const groups = Object.keys(gs);
        const rates = groups.map(g => gs[g].favorable_rate);
        FairCharts.groupComparison('group-chart', groups, rates, 'Favorable Rate %');

        // Composition chart
        const counts = groups.map(g => gs[g].count);
        FairCharts.composition('composition-chart', groups, counts);

        // Dashboard chart
        const scores = groups.map(g => {
            const maxRate = Math.max(...rates);
            return maxRate > 0 ? Math.round((gs[g].favorable_rate / maxRate) * 100) : 0;
        });
        FairCharts.fairnessOverview('dashboard-chart', groups, scores);

        // Model metrics
        if (result.model_metrics) {
            const mm = result.model_metrics;
            let html = '<div class="metrics-grid">';
            html += `<div class="metric-card"><div class="metric-name">Model Accuracy</div><div class="metric-value-large">${(mm.accuracy * 100).toFixed(1)}%</div></div>`;
            if (mm.statistical_parity_diff !== undefined) html += `<div class="metric-card"><div class="metric-name">Model SPD</div><div class="metric-value-large">${mm.statistical_parity_diff.toFixed(4)}</div><div class="metric-status ${Math.abs(mm.statistical_parity_diff) <= 0.1 ? 'status-pass' : 'status-fail'}">${Math.abs(mm.statistical_parity_diff) <= 0.1 ? '✅ Pass' : '❌ Fail'}</div></div>`;
            if (mm.equal_opportunity_diff !== undefined) html += `<div class="metric-card"><div class="metric-name">Equal Opportunity Diff</div><div class="metric-value-large">${mm.equal_opportunity_diff.toFixed(4)}</div><div class="metric-status ${Math.abs(mm.equal_opportunity_diff) <= 0.1 ? 'status-pass' : 'status-fail'}">${Math.abs(mm.equal_opportunity_diff) <= 0.1 ? '✅ Pass' : '❌ Fail'}</div></div>`;
            if (mm.average_odds_diff !== undefined) html += `<div class="metric-card"><div class="metric-name">Average Odds Diff</div><div class="metric-value-large">${mm.average_odds_diff.toFixed(4)}</div></div>`;
            html += '</div>';
            if (mm.top_features) {
                html += '<h4 style="margin:16px 0 8px">Top Feature Importances</h4><table class="data-table"><thead><tr><th>Feature</th><th>Importance</th></tr></thead><tbody>';
                mm.top_features.forEach(f => { html += `<tr><td>${f.feature}</td><td>${f.importance.toFixed(4)}</td></tr>`; });
                html += '</tbody></table>';
            }
            document.getElementById('model-metrics-content').innerHTML = html;
        }
    },

    // === Gemini Explanation ===
    saveApiKey() {
        const key = document.getElementById('gemini-api-key').value.trim();
        if (!key) { this.toast('Please enter an API key', 'error'); return; }
        GeminiClient.setApiKey(key);
        document.getElementById('settings-api-key').value = key;
        this.toast('API key saved!', 'success');
    },

    loadSavedKey() {
        const key = GeminiClient.getApiKey();
        if (key) {
            document.getElementById('gemini-api-key').value = key;
            document.getElementById('settings-api-key').value = key;
        }
    },

    async getExplanation() {
        const key = GeminiClient.getApiKey();
        if (!key) { this.toast('Set your Gemini API key first', 'error'); return; }
        if (!this.state.datasetId) { this.toast('Run analysis first', 'error'); return; }

        const protCol = document.getElementById('analysis-protected-col').value;
        const panel = document.getElementById('gemini-explanation');
        panel.innerHTML = '<div class="loading-overlay"><div class="spinner"></div><p>Asking Gemini AI...</p></div>';

        try {
            const data = await API.explain(this.state.datasetId, protCol, key);
            panel.innerHTML = typeof marked !== 'undefined' ? marked.parse(data.explanation) : data.explanation.replace(/\n/g, '<br>');
            document.getElementById('dashboard-gemini').innerHTML = panel.innerHTML;
            this.addActivity('Gemini explanation generated', 'blue');
            this.toast('Gemini explanation ready!', 'success');
        } catch (e) {
            panel.innerHTML = `<p style="color:var(--accent-red)">Error: ${e.message}</p>`;
            this.toast(e.message, 'error');
        }
    },

    // === Mitigation ===
    async runMitigation(method) {
        if (!this.state.datasetId || !this.state.analysisResult) { this.toast('Run analysis first', 'error'); return; }
        const protCol = document.getElementById('analysis-protected-col').value;
        const labelCol = document.getElementById('analysis-label-col').value;
        const privVal = document.getElementById('analysis-priv-value').value;

        try {
            this.toast(`Applying ${method}...`, 'info');
            const result = await API.mitigate(this.state.datasetId, labelCol, protCol, privVal, method);
            this.renderMitigation(result);
            this.addActivity(`Mitigation applied: ${result.method}`, 'green');
            this.toast('Mitigation complete!', 'success');
        } catch (e) { this.toast(e.message, 'error'); }
    },

    renderMitigation(result) {
        const sec = document.getElementById('mitigation-results');
        sec.classList.remove('page-hidden');
        const b = result.before, a = result.after;
        let html = `<h4 style="margin-bottom:12px">${result.method}</h4><p style="color:var(--text-secondary);margin-bottom:20px">${result.description}</p>`;
        html += '<div class="metrics-grid">';
        html += `<div class="metric-card"><div class="metric-name">Before — Privileged Rate</div><div class="metric-value-large">${b.privileged_rate}%</div></div>`;
        html += `<div class="metric-card"><div class="metric-name">Before — Unprivileged Rate</div><div class="metric-value-large">${b.unprivileged_rate}%</div></div>`;
        html += `<div class="metric-card"><div class="metric-name">After — Privileged Rate</div><div class="metric-value-large" style="color:var(--accent-green)">${a.privileged_rate}%</div></div>`;
        html += `<div class="metric-card"><div class="metric-name">After — Unprivileged Rate</div><div class="metric-value-large" style="color:var(--accent-green)">${a.unprivileged_rate}%</div></div>`;
        html += '</div>';
        html += `<div class="chart-container" style="margin-top:16px"><canvas id="mitigation-chart"></canvas></div>`;
        document.getElementById('mitigation-content').innerHTML = html;
        setTimeout(() => {
            FairCharts.mitigationComparison('mitigation-chart',
                { priv: b.privileged_rate, unpriv: b.unprivileged_rate },
                { priv: a.privileged_rate, unpriv: a.unprivileged_rate }
            );
        }, 100);
    },

    // === Counterfactual ===
    bindCounterfactual() {
        document.getElementById('btn-counterfactual').addEventListener('click', () => this.runCounterfactual());
        document.getElementById('cf-protected-col').addEventListener('change', () => this.updateCfValues());
    },

    updateCfValues() {
        const col = document.getElementById('cf-protected-col').value;
        const sel = document.getElementById('cf-new-value');
        sel.innerHTML = '';
        const attr = this.state.protectedAttrs.find(a => a.column === col);
        if (attr) attr.unique_values.forEach(v => { sel.innerHTML += `<option value="${v}">${v}</option>`; });
    },

    async runCounterfactual() {
        if (!this.state.datasetId) { this.toast('Load a dataset first', 'error'); return; }
        // Populate dropdowns if needed
        if (!document.getElementById('cf-protected-col').options.length) {
            const sel = document.getElementById('cf-protected-col');
            this.state.protectedAttrs.forEach(a => { sel.innerHTML += `<option value="${a.column}">${a.column}</option>`; });
            this.updateCfValues();
        }

        const protCol = document.getElementById('cf-protected-col').value;
        const labelCol = document.getElementById('analysis-label-col')?.value || 'hired';
        const idx = parseInt(document.getElementById('cf-sample-idx').value) || 0;
        const newVal = document.getElementById('cf-new-value').value;

        if (!protCol || !newVal) { this.toast('Select attribute and value', 'error'); return; }

        try {
            this.toast('Running counterfactual analysis...', 'info');
            const result = await API.counterfactual(this.state.datasetId, labelCol, protCol, idx, newVal);
            this.renderCounterfactual(result);
            this.addActivity('Counterfactual analysis completed', 'blue');
            this.toast('What-If analysis complete!', 'success');
        } catch (e) { this.toast(e.message, 'error'); }
    },

    renderCounterfactual(result) {
        document.getElementById('cf-results').classList.remove('page-hidden');
        const o = result.original, m = result.modified;

        // Original card
        let oHtml = '<table class="data-table"><tbody>';
        Object.entries(o.attributes).forEach(([k, v]) => {
            const highlight = k === m.changed_attribute ? 'style="color:var(--accent-blue);font-weight:600"' : '';
            oHtml += `<tr><td ${highlight}>${k}</td><td ${highlight}>${v}</td></tr>`;
        });
        oHtml += '</tbody></table>';
        oHtml += `<div style="margin-top:16px;padding:12px;background:var(--bg-glass);border-radius:var(--radius-sm)"><strong>Prediction:</strong> ${o.predicted_class === 1 ? '✅ Positive' : '❌ Negative'} (${(o.prediction_probabilities.positive * 100).toFixed(1)}%)</div>`;
        document.getElementById('cf-original').innerHTML = oHtml;

        // Modified card
        let mHtml = `<div style="padding:12px;background:rgba(0,210,255,0.1);border-radius:var(--radius-sm);margin-bottom:12px"><strong>${m.changed_attribute}:</strong> ${m.original_value} → <span style="color:var(--accent-cyan)">${m.new_value}</span></div>`;
        mHtml += `<div style="padding:12px;background:var(--bg-glass);border-radius:var(--radius-sm)"><strong>Prediction:</strong> ${m.predicted_class === 1 ? '✅ Positive' : '❌ Negative'} (${(m.prediction_probabilities.positive * 100).toFixed(1)}%)</div>`;
        mHtml += `<div style="margin-top:12px;padding:12px;background:${Math.abs(result.prediction_shift) > 0.05 ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)'};border-radius:var(--radius-sm)"><strong>Shift:</strong> ${(result.prediction_shift * 100).toFixed(1)}% ${Math.abs(result.prediction_shift) > 0.05 ? '⚠️ Significant' : '✅ Minimal'}</div>`;
        document.getElementById('cf-modified').innerHTML = mHtml;

        FairCharts.counterfactual('cf-chart', o.prediction_probabilities, m.prediction_probabilities);
    },

    // === Reports ===
    bindReports() {
        document.getElementById('btn-gen-report').addEventListener('click', () => this.generateReport());
    },

    async generateReport() {
        const key = GeminiClient.getApiKey();
        if (!key) { this.toast('Set your Gemini API key first', 'error'); return; }
        if (!this.state.datasetId) { this.toast('Run analysis first', 'error'); return; }

        const panel = document.getElementById('report-content');
        panel.innerHTML = '<div class="loading-overlay"><div class="spinner"></div><p>Generating Model Card with Gemini AI...</p></div>';

        try {
            const data = await API.generateReport(this.state.datasetId, key);
            panel.innerHTML = typeof marked !== 'undefined' ? marked.parse(data.model_card) : data.model_card.replace(/\n/g, '<br>');
            this.state.stats.reports++;
            this.updateStats();
            this.addActivity('Model Card report generated', 'green');
            this.toast('Report generated!', 'success');
        } catch (e) {
            panel.innerHTML = `<p style="color:var(--accent-red)">Error: ${e.message}</p>`;
            this.toast(e.message, 'error');
        }
    },

    // === Settings ===
    bindSettings() {
        document.getElementById('btn-settings-save-key').addEventListener('click', () => {
            const key = document.getElementById('settings-api-key').value.trim();
            if (key) {
                GeminiClient.setApiKey(key);
                document.getElementById('gemini-api-key').value = key;
                this.toast('API key saved!', 'success');
            }
        });
    }
};

// Boot
document.addEventListener('DOMContentLoaded', () => FairGuard.init());
