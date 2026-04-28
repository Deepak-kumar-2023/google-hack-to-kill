"""
FairGuard AI — FastAPI Backend Server
Main API server handling dataset upload, bias analysis, mitigation, and Gemini integration.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import io
import os
import json
import traceback

from backend.bias_engine import (
    detect_protected_attributes,
    analyze_dataset,
    analyze_all_protected_attributes,
    train_and_evaluate_model,
    counterfactual_analysis,
)
from backend.mitigation import apply_reweighing, apply_sampling
from backend.gemini_service import explain_bias, generate_model_card, suggest_mitigations
from backend.sample_data import generate_hiring_dataset

app = FastAPI(title="FairGuard AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for uploaded datasets
datasets: dict[str, pd.DataFrame] = {}
analysis_cache: dict[str, dict] = {}

# Serve frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
async def root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "FairGuard AI API is running", "docs": "/docs"}


@app.get("/landing")
async def landing():
    path = os.path.join(frontend_dir, "landing.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Landing page not found"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "service": "FairGuard AI"}


# --- Dataset endpoints ---

class ColumnInfo(BaseModel):
    name: str
    dtype: str
    unique_count: int
    sample_values: list
    null_count: int


@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a CSV dataset and return column analysis."""
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        dataset_id = file.filename or "uploaded_dataset"
        datasets[dataset_id] = df

        columns = []
        for col in df.columns:
            columns.append({
                "name": col,
                "dtype": str(df[col].dtype),
                "unique_count": int(df[col].nunique()),
                "sample_values": [str(v) for v in df[col].dropna().unique()[:5]],
                "null_count": int(df[col].isnull().sum()),
            })

        protected = detect_protected_attributes(df)

        return {
            "dataset_id": dataset_id,
            "rows": len(df),
            "columns": columns,
            "protected_attributes": protected,
            "preview": json.loads(df.head(10).to_json(orient="records")),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sample-dataset")
async def get_sample_dataset():
    """Load the built-in sample hiring dataset."""
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_hiring_data.csv")
        if not os.path.exists(data_path):
            df = generate_hiring_dataset(output_path=data_path)
        else:
            df = pd.read_csv(data_path)

        dataset_id = "sample_hiring_data.csv"
        datasets[dataset_id] = df

        columns = []
        for col in df.columns:
            columns.append({
                "name": col,
                "dtype": str(df[col].dtype),
                "unique_count": int(df[col].nunique()),
                "sample_values": [str(v) for v in df[col].dropna().unique()[:5]],
                "null_count": int(df[col].isnull().sum()),
            })

        protected = detect_protected_attributes(df)

        return {
            "dataset_id": dataset_id,
            "rows": len(df),
            "columns": columns,
            "protected_attributes": protected,
            "preview": json.loads(df.head(10).to_json(orient="records")),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Analysis endpoints ---

class AnalyzeRequest(BaseModel):
    dataset_id: str
    label_column: str
    protected_column: str
    privileged_value: str
    favorable_label: str = "1"


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    """Run bias analysis on a dataset."""
    if req.dataset_id not in datasets:
        raise HTTPException(404, "Dataset not found. Upload first.")
    try:
        df = datasets[req.dataset_id]
        fav = int(req.favorable_label) if req.favorable_label.isdigit() else req.favorable_label
        result = analyze_dataset(df, req.label_column, req.protected_column, req.privileged_value, fav)

        # Also train model and get model-level metrics
        try:
            model_metrics = train_and_evaluate_model(
                df, req.label_column, req.protected_column, req.privileged_value, fav
            )
            result['model_metrics'] = model_metrics
        except Exception:
            result['model_metrics'] = None

        cache_key = f"{req.dataset_id}_{req.protected_column}"
        analysis_cache[cache_key] = result
        return result
    except Exception as e:
        raise HTTPException(500, f"Analysis error: {str(e)}\n{traceback.format_exc()}")


@app.post("/api/analyze-all")
async def analyze_all(dataset_id: str = Form(...), label_column: str = Form(...)):
    """Run bias analysis across all detected protected attributes."""
    if dataset_id not in datasets:
        raise HTTPException(404, "Dataset not found.")
    try:
        df = datasets[dataset_id]
        protected = detect_protected_attributes(df)
        result = analyze_all_protected_attributes(df, label_column, protected)
        analysis_cache[dataset_id] = result
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


# --- Mitigation endpoints ---

class MitigateRequest(BaseModel):
    dataset_id: str
    label_column: str
    protected_column: str
    privileged_value: str
    method: str = "reweighing"


@app.post("/api/mitigate")
async def mitigate(req: MitigateRequest):
    """Apply bias mitigation to a dataset."""
    if req.dataset_id not in datasets:
        raise HTTPException(404, "Dataset not found.")
    try:
        df = datasets[req.dataset_id]
        if req.method == "reweighing":
            result = apply_reweighing(df, req.label_column, req.protected_column, req.privileged_value)
        elif req.method == "sampling":
            result = apply_sampling(df, req.label_column, req.protected_column, req.privileged_value)
        else:
            raise HTTPException(400, f"Unknown method: {req.method}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# --- Gemini endpoints ---

class ExplainRequest(BaseModel):
    dataset_id: str
    protected_column: str
    api_key: str


@app.post("/api/explain")
async def explain(req: ExplainRequest):
    """Get Gemini-powered plain-English explanation of bias."""
    cache_key = f"{req.dataset_id}_{req.protected_column}"
    if cache_key not in analysis_cache:
        raise HTTPException(400, "Run analysis first before requesting explanation.")
    try:
        result = analysis_cache[cache_key]
        explanation = explain_bias(result, req.api_key)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(500, str(e))


class ReportRequest(BaseModel):
    dataset_id: str
    api_key: str


@app.post("/api/report")
async def report(req: ReportRequest):
    """Generate a Model Card using Gemini."""
    if req.dataset_id not in analysis_cache:
        raise HTTPException(400, "Run analysis first.")
    try:
        analysis = analysis_cache[req.dataset_id]
        card = generate_model_card(analysis, {}, req.api_key)
        return {"model_card": card}
    except Exception as e:
        raise HTTPException(500, str(e))


class CounterfactualRequest(BaseModel):
    dataset_id: str
    label_column: str
    protected_column: str
    sample_index: int
    new_value: str


@app.post("/api/counterfactual")
async def run_counterfactual(req: CounterfactualRequest):
    """Run what-if counterfactual analysis."""
    if req.dataset_id not in datasets:
        raise HTTPException(404, "Dataset not found.")
    try:
        df = datasets[req.dataset_id]
        result = counterfactual_analysis(
            df, req.label_column, req.protected_column, req.sample_index, req.new_value
        )
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    import uvicorn
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_hiring_data.csv")
    if not os.path.exists(data_path):
        generate_hiring_dataset(output_path=data_path)
    uvicorn.run(app, host="0.0.0.0", port=8000)
