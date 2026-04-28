"""
FairGuard AI — Gemini AI Service
Integration with Google Gemini API for bias explanations and report generation.
"""

import google.generativeai as genai
import json
import os
from typing import Optional


def get_gemini_model() -> genai.GenerativeModel:
    """Return a Gemini model that is likely to be supported for the current API key."""
    requested_model = os.getenv("GEMINI_MODEL", "").strip()
    candidate_models = [requested_model] if requested_model else []
    candidate_models.extend([
        "gemini-3-flash-preview",
    ])

    seen: set[str] = set()
    last_error: Optional[Exception] = None

    for model_name in candidate_models:
        if not model_name or model_name in seen:
            continue
        seen.add(model_name)
        try:
            return genai.GenerativeModel(model_name)
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error

    raise RuntimeError("No Gemini model candidates were available")


def configure_gemini(api_key: str):
    """Configure the Gemini API with the provided key."""
    genai.configure(api_key=api_key)


def explain_bias(analysis_results: dict, api_key: str) -> str:
    """Use Gemini to generate a plain-English explanation of bias findings."""
    configure_gemini(api_key)
    model = get_gemini_model()

    prompt = f"""You are FairGuard AI, a responsible AI bias analysis assistant.
Analyze these bias detection results and provide a clear, actionable explanation
for non-technical stakeholders (HR managers, executives, compliance officers).

BIAS ANALYSIS RESULTS:
{json.dumps(analysis_results, indent=2)}

Provide your response in this exact format:

## Key Finding
[One sentence summary of the most critical bias issue found]

## Severity: [LOW/MEDIUM/HIGH]

## What We Found
[2-3 bullet points explaining the bias in plain English. Use specific numbers.
Example: "Female applicants are hired at 31% vs 72% for male applicants"]

## Why This Matters
[1-2 sentences on real-world impact - legal risk, ethical concerns]

## Root Cause Analysis
[2-3 bullet points on likely causes - data imbalance, proxy variables, historical patterns]

## Recommended Actions
1. [Specific actionable step]
2. [Specific actionable step]
3. [Specific actionable step]

## Risk Level: [🟢 LOW / 🟡 MEDIUM / 🔴 HIGH]
[One sentence on deployment recommendation]
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"## Gemini API Error\nCould not generate explanation: {str(e)}\n\nPlease check your API key and try again."


def generate_model_card(analysis_results: dict, model_metrics: dict, api_key: str) -> str:
    """Use Gemini to auto-generate a Model Card for compliance."""
    configure_gemini(api_key)
    model = get_gemini_model()

    prompt = f"""Generate a comprehensive Model Card document based on these results.
Follow the Google Model Cards framework.

BIAS ANALYSIS: {json.dumps(analysis_results, indent=2)}
MODEL METRICS: {json.dumps(model_metrics, indent=2)}

Create a professional Model Card with these sections:
# Model Card — FairGuard AI Analysis

## Model Details
- Model type, version, date

## Intended Use
- Primary use cases
- Out-of-scope uses

## Metrics
- Performance metrics table
- Fairness metrics table with pass/fail status

## Training Data
- Dataset description, size, demographics

## Ethical Considerations
- Identified biases
- Mitigation steps taken
- Remaining risks

## Recommendations
- Deployment conditions
- Monitoring requirements

## Compliance Notes
- GDPR considerations
- EU AI Act risk classification
- Recommended audit frequency

Format as clean markdown. Use tables where appropriate.
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"# Model Card Generation Error\nCould not generate: {str(e)}"


def suggest_mitigations(analysis_results: dict, api_key: str) -> str:
    """Use Gemini to suggest specific mitigation strategies."""
    configure_gemini(api_key)
    model = get_gemini_model()

    prompt = f"""Based on these bias analysis results, suggest specific mitigation strategies.

RESULTS: {json.dumps(analysis_results, indent=2)}

Provide 3-5 concrete mitigation strategies, each with:
1. Strategy name
2. How it works (1-2 sentences)
3. Expected improvement
4. Trade-offs to consider
5. Implementation difficulty (Easy/Medium/Hard)

Format as clean markdown with headers for each strategy.
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"## Error\nCould not generate suggestions: {str(e)}"
