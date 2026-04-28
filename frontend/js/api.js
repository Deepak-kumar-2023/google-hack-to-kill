/* FairGuard AI — Backend API Client */
const API = {
    baseUrl: 'http://localhost:8000',

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        try {
            const res = await fetch(url, {
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(err.detail || 'API request failed');
            }
            return await res.json();
        } catch (e) {
            if (e.message.includes('Failed to fetch')) throw new Error('Backend not running. Start with: python start.py');
            throw e;
        }
    },

    async uploadFile(file) {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch(`${this.baseUrl}/api/upload`, { method: 'POST', body: form });
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Upload failed'); }
        return res.json();
    },

    loadSampleDataset() { return this.request('/api/sample-dataset'); },
    
    analyze(datasetId, labelCol, protectedCol, privValue) {
        return this.request('/api/analyze', {
            method: 'POST',
            body: JSON.stringify({ dataset_id: datasetId, label_column: labelCol, protected_column: protectedCol, privileged_value: privValue, favorable_label: '1' })
        });
    },

    mitigate(datasetId, labelCol, protectedCol, privValue, method) {
        return this.request('/api/mitigate', {
            method: 'POST',
            body: JSON.stringify({ dataset_id: datasetId, label_column: labelCol, protected_column: protectedCol, privileged_value: privValue, method })
        });
    },

    explain(datasetId, protectedCol, apiKey) {
        return this.request('/api/explain', {
            method: 'POST',
            body: JSON.stringify({ dataset_id: datasetId, protected_column: protectedCol, api_key: apiKey })
        });
    },

    generateReport(datasetId, apiKey) {
        return this.request('/api/report', {
            method: 'POST',
            body: JSON.stringify({ dataset_id: datasetId, api_key: apiKey })
        });
    },

    counterfactual(datasetId, labelCol, protectedCol, sampleIdx, newValue) {
        return this.request('/api/counterfactual', {
            method: 'POST',
            body: JSON.stringify({ dataset_id: datasetId, label_column: labelCol, protected_column: protectedCol, sample_index: sampleIdx, new_value: newValue })
        });
    },

    health() { return this.request('/api/health'); }
};
