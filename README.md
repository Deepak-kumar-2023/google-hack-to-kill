# 🛡️ FairGuard AI

**Responsible AI Bias Detection Platform**

> The only bias detection platform that speaks human.

FairGuard AI is an end-to-end platform that helps organizations detect, understand, and fix hidden bias in their datasets and machine learning models before they impact real people.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the application
python start.py
```

Then open your browser to:
- **Dashboard**: http://localhost:8000
- **Landing Page**: http://localhost:8000/landing
- **API Docs**: http://localhost:8000/docs

### Gemini API Key
To use AI-powered explanations and report generation:
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/)
2. Enter it in Settings or when prompted in the dashboard

---

## ✨ Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Dataset Bias Scanner** | Upload CSV → automatic demographic analysis with 8+ fairness metrics |
| 2 | **Visual Bias Dashboard** | Interactive Chart.js charts showing fairness metrics across groups |
| 3 | **Gemini AI Explainer** | Plain-English explanations of detected bias via Google Gemini 1.5 Pro |
| 4 | **Auto-Mitigation Engine** | One-click Reweighing and Balanced Sampling debiasing |
| 5 | **Counterfactual Analysis** | "What if this applicant were male?" scenario testing |
| 6 | **Model Card Generator** | Gemini auto-generates compliance documentation |
| 7 | **Risk Assessment** | Automatic LOW/MEDIUM/HIGH risk classification |
| 8 | **Model Fairness** | Train a model and evaluate fairness (SPD, EOD, AOD) |

---

## 🏗️ Architecture

```
Frontend (HTML/CSS/JS) → FastAPI Backend → AIF360/Fairlearn + Gemini API
                                   ↓
                          Bias Metrics Engine
                          Mitigation Engine
                          Report Generator
```

### Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Vanilla HTML/CSS/JS, Chart.js, marked.js |
| **Backend** | Python, FastAPI, Uvicorn |
| **AI/ML** | Google Gemini 1.5 Pro, Scikit-learn |
| **Fairness** | AIF360-inspired metrics, Reweighing, Balanced Sampling |
| **Design** | Dark glassmorphism, Space Grotesk + Inter fonts |

---

## 📁 Project Structure

```
GoogleSolution/
├── start.py                 # One-command startup
├── requirements.txt         # Python dependencies
├── README.md
├── backend/
│   ├── main.py              # FastAPI server & endpoints
│   ├── bias_engine.py       # Fairness metrics engine
│   ├── mitigation.py        # Bias mitigation algorithms
│   ├── gemini_service.py    # Google Gemini integration
│   └── sample_data.py       # Sample dataset generator
├── frontend/
│   ├── index.html           # Main dashboard SPA
│   ├── landing.html         # Marketing landing page
│   ├── css/
│   │   └── styles.css       # Premium design system
│   └── js/
│       ├── app.js           # Main app controller
│       ├── api.js           # Backend API client
│       ├── charts.js        # Chart.js utilities
│       └── gemini.js        # Gemini key manager
└── data/
    └── sample_hiring_data.csv  # Auto-generated demo data
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/sample-dataset` | Load built-in demo dataset |
| POST | `/api/upload` | Upload CSV dataset |
| POST | `/api/analyze` | Run bias analysis |
| POST | `/api/mitigate` | Apply mitigation algorithm |
| POST | `/api/explain` | Get Gemini AI explanation |
| POST | `/api/counterfactual` | Run what-if analysis |
| POST | `/api/report` | Generate Model Card |

---

## 📊 Fairness Metrics Computed

- **Statistical Parity Difference** — Difference in favorable outcome rates
- **Disparate Impact Ratio** — Ratio of favorable outcomes (80% rule)
- **Equal Opportunity Difference** — Difference in true positive rates
- **Average Odds Difference** — Average of TPR and FPR differences
- **False Positive Rate Parity** — FPR comparison across groups
- **Model Accuracy** — Overall model performance
- **Feature Importance** — Which features drive predictions

---

## 🤝 Built For

**Google Solution Challenge 2025**

Using Google Gemini AI to make bias detection accessible to everyone — from data scientists to HR managers to compliance officers.

---

## 📝 License

MIT License — Built with ❤️ for fairer AI.
