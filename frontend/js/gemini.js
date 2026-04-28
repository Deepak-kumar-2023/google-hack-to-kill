/* FairGuard AI — Gemini API Client */
const GeminiClient = {
    getApiKey() {
        console.log("getapi");
        return localStorage.getItem('fairguard_gemini_key') || '';
    },
    setApiKey(key) {
        console.log("setapi");
        localStorage.setItem('fairguard_gemini_key', key);
    },
    hasApiKey() {
        return !!this.getApiKey();
    }
};
