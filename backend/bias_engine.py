"""
FairGuard AI — Bias Detection Engine
Core module for computing fairness metrics using AIF360 and Fairlearn.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, confusion_matrix


def detect_protected_attributes(df: pd.DataFrame) -> list[dict]:
    """
    Auto-detect columns that are likely protected attributes.
    Returns list of dicts with column name, type, and unique values.
    """
    protected_keywords = [
        'gender', 'sex', 'race', 'ethnicity', 'age', 'religion',
        'disability', 'nationality', 'marital', 'pregnancy', 'veteran',
        'orientation', 'color', 'national_origin'
    ]
    
    detected = []
    for col in df.columns:
        col_lower = col.lower().replace('_', ' ').replace('-', ' ')
        for keyword in protected_keywords:
            if keyword in col_lower:
                unique_vals = df[col].dropna().unique().tolist()
                if len(unique_vals) <= 20:  # Reasonable number of categories
                    detected.append({
                        'column': col,
                        'keyword_match': keyword,
                        'unique_values': [str(v) for v in unique_vals[:20]],
                        'num_unique': len(unique_vals),
                        'dtype': str(df[col].dtype)
                    })
                break
    
    return detected


def analyze_dataset(
    df: pd.DataFrame,
    label_col: str,
    protected_col: str,
    privileged_value: str,
    favorable_label=1
) -> dict:
    """
    Comprehensive bias analysis on a dataset.
    Returns fairness metrics, group statistics, and risk assessment.
    """
    df_clean = df[[protected_col, label_col]].dropna().copy()
    
    # Convert label to numeric if needed
    if df_clean[label_col].dtype == object:
        unique_labels = df_clean[label_col].unique()
        if len(unique_labels) == 2:
            label_map = {unique_labels[0]: 0, unique_labels[1]: 1}
            df_clean[label_col] = df_clean[label_col].map(label_map)
            favorable_label = 1
    
    df_clean[label_col] = pd.to_numeric(df_clean[label_col], errors='coerce')
    df_clean = df_clean.dropna()
    
    # Identify privileged and unprivileged groups
    is_privileged = df_clean[protected_col].astype(str) == str(privileged_value)
    
    priv_group = df_clean[is_privileged]
    unpriv_group = df_clean[~is_privileged]
    
    # Compute base rates
    priv_favorable_rate = (priv_group[label_col] == favorable_label).mean() if len(priv_group) > 0 else 0
    unpriv_favorable_rate = (unpriv_group[label_col] == favorable_label).mean() if len(unpriv_group) > 0 else 0
    overall_favorable_rate = (df_clean[label_col] == favorable_label).mean()
    
    # --- Fairness Metrics ---
    
    # 1. Statistical Parity Difference (SPD)
    # Range: [-1, 1], ideal: 0, acceptable: [-0.1, 0.1]
    spd = unpriv_favorable_rate - priv_favorable_rate
    
    # 2. Disparate Impact Ratio (DIR)
    # Range: [0, inf], ideal: 1.0, acceptable: [0.8, 1.25] (80% rule)
    dir_ratio = (unpriv_favorable_rate / priv_favorable_rate) if priv_favorable_rate > 0 else 0
    
    # 3. Group-level statistics
    group_stats = {}
    for val in df_clean[protected_col].unique():
        mask = df_clean[protected_col].astype(str) == str(val)
        group = df_clean[mask]
        group_stats[str(val)] = {
            'count': int(len(group)),
            'percentage': round(len(group) / len(df_clean) * 100, 1),
            'favorable_rate': round((group[label_col] == favorable_label).mean() * 100, 1),
            'unfavorable_rate': round((group[label_col] != favorable_label).mean() * 100, 1),
        }
    
    # 4. Compute additional metrics
    # Consistency (individual fairness proxy)
    consistency = 1 - abs(spd)
    
    # Risk assessment
    risk_level = 'LOW'
    risk_reasons = []
    
    if abs(spd) > 0.1:
        risk_level = 'MEDIUM'
        risk_reasons.append(f'Statistical Parity Difference ({spd:.3f}) exceeds ±0.1 threshold')
    if abs(spd) > 0.2:
        risk_level = 'HIGH'
    
    if dir_ratio < 0.8 or dir_ratio > 1.25:
        if risk_level != 'HIGH':
            risk_level = 'HIGH' if dir_ratio < 0.6 else 'MEDIUM'
        risk_reasons.append(f'Disparate Impact Ratio ({dir_ratio:.3f}) violates 80% rule')
    
    if not risk_reasons:
        risk_reasons.append('All metrics within acceptable thresholds')
    
    metrics = {
        'statistical_parity_difference': round(spd, 4),
        'disparate_impact_ratio': round(dir_ratio, 4),
        'consistency': round(consistency, 4),
        'privileged_favorable_rate': round(priv_favorable_rate * 100, 1),
        'unprivileged_favorable_rate': round(unpriv_favorable_rate * 100, 1),
        'overall_favorable_rate': round(overall_favorable_rate * 100, 1),
    }
    
    return {
        'metrics': metrics,
        'group_stats': group_stats,
        'risk_level': risk_level,
        'risk_reasons': risk_reasons,
        'dataset_size': len(df_clean),
        'protected_attribute': protected_col,
        'privileged_value': str(privileged_value),
        'label_column': label_col,
        'favorable_label': favorable_label,
    }


def analyze_all_protected_attributes(
    df: pd.DataFrame,
    label_col: str,
    protected_cols: list[dict],
    favorable_label=1
) -> dict:
    """
    Run bias analysis across all detected protected attributes.
    """
    results = {}
    overall_risk = 'LOW'
    
    for attr_info in protected_cols:
        col = attr_info['column']
        values = attr_info['unique_values']
        
        if len(values) < 2:
            continue
        
        # Use the most common value as privileged (heuristic)
        value_counts = df[col].astype(str).value_counts()
        privileged_value = value_counts.index[0]
        
        analysis = analyze_dataset(df, label_col, col, privileged_value, favorable_label)
        results[col] = analysis
        
        if analysis['risk_level'] == 'HIGH':
            overall_risk = 'HIGH'
        elif analysis['risk_level'] == 'MEDIUM' and overall_risk != 'HIGH':
            overall_risk = 'MEDIUM'
    
    return {
        'attribute_analyses': results,
        'overall_risk': overall_risk,
        'num_attributes_analyzed': len(results),
    }


def train_and_evaluate_model(
    df: pd.DataFrame,
    label_col: str,
    protected_col: str,
    privileged_value: str,
    favorable_label=1
) -> dict:
    """
    Train a simple model and evaluate its fairness.
    Returns model performance metrics + fairness metrics.
    """
    df_model = df.dropna().copy()
    
    # Prepare features (simple encoding)
    feature_cols = [c for c in df_model.columns if c != label_col]
    X = pd.get_dummies(df_model[feature_cols], drop_first=True)
    y = df_model[label_col]
    
    if y.dtype == object:
        unique_labels = y.unique()
        label_map = {unique_labels[0]: 0, unique_labels[1]: 1}
        y = y.map(label_map)
    
    y = pd.to_numeric(y, errors='coerce')
    valid_mask = y.notna()
    X = X[valid_mask]
    y = y[valid_mask]
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # Train model
    model = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=4)
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Fairness on predictions
    test_df = X_test.copy()
    test_df['__label__'] = y_test.values
    test_df['__pred__'] = y_pred
    
    # Find the protected col in dummy-encoded features
    prot_col_encoded = None
    for c in test_df.columns:
        if c.startswith(protected_col + '_') or c == protected_col:
            prot_col_encoded = c
            break
    
    model_metrics = {
        'accuracy': round(accuracy, 4),
        'total_test_samples': len(y_test),
    }
    
    if prot_col_encoded:
        priv_mask = test_df[prot_col_encoded] == 1
        
        priv_preds = test_df[priv_mask]['__pred__']
        unpriv_preds = test_df[~priv_mask]['__pred__']
        
        priv_rate = priv_preds.mean() if len(priv_preds) > 0 else 0
        unpriv_rate = unpriv_preds.mean() if len(unpriv_preds) > 0 else 0
        
        # True positive rates
        priv_labels = test_df[priv_mask]['__label__']
        unpriv_labels = test_df[~priv_mask]['__label__']
        
        priv_tp = ((priv_preds == 1) & (priv_labels == 1)).sum()
        priv_pos = (priv_labels == 1).sum()
        unpriv_tp = ((unpriv_preds == 1) & (unpriv_labels == 1)).sum()
        unpriv_pos = (unpriv_labels == 1).sum()
        
        priv_tpr = priv_tp / priv_pos if priv_pos > 0 else 0
        unpriv_tpr = unpriv_tp / unpriv_pos if unpriv_pos > 0 else 0
        
        # False positive rates
        priv_fp = ((priv_preds == 1) & (priv_labels == 0)).sum()
        priv_neg = (priv_labels == 0).sum()
        unpriv_fp = ((unpriv_preds == 1) & (unpriv_labels == 0)).sum()
        unpriv_neg = (unpriv_labels == 0).sum()
        
        priv_fpr = priv_fp / priv_neg if priv_neg > 0 else 0
        unpriv_fpr = unpriv_fp / unpriv_neg if unpriv_neg > 0 else 0
        
        model_metrics.update({
            'privileged_positive_rate': round(float(priv_rate) * 100, 1),
            'unprivileged_positive_rate': round(float(unpriv_rate) * 100, 1),
            'statistical_parity_diff': round(float(unpriv_rate - priv_rate), 4),
            'equal_opportunity_diff': round(float(unpriv_tpr - priv_tpr), 4),
            'average_odds_diff': round(float(((unpriv_tpr - priv_tpr) + (unpriv_fpr - priv_fpr)) / 2), 4),
            'privileged_tpr': round(float(priv_tpr) * 100, 1),
            'unprivileged_tpr': round(float(unpriv_tpr) * 100, 1),
            'privileged_fpr': round(float(priv_fpr) * 100, 1),
            'unprivileged_fpr': round(float(unpriv_fpr) * 100, 1),
        })
    
    # Feature importance
    feature_importance = sorted(
        zip(X.columns, model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )[:10]
    
    model_metrics['top_features'] = [
        {'feature': str(f), 'importance': round(float(i), 4)}
        for f, i in feature_importance
    ]
    
    return model_metrics


def counterfactual_analysis(
    df: pd.DataFrame,
    label_col: str,
    protected_col: str,
    sample_index: int,
    new_value: str
) -> dict:
    """
    What-if analysis: change a protected attribute and see prediction change.
    """
    df_model = df.dropna().copy()
    feature_cols = [c for c in df_model.columns if c != label_col]
    X = pd.get_dummies(df_model[feature_cols], drop_first=True)
    y = df_model[label_col]
    
    if y.dtype == object:
        unique_labels = y.unique()
        label_map = {unique_labels[0]: 0, unique_labels[1]: 1}
        y = y.map(label_map)
    
    y = pd.to_numeric(y, errors='coerce')
    valid_mask = y.notna()
    X = X[valid_mask]
    y = y[valid_mask]
    
    model = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=4)
    model.fit(X, y)
    
    # Original prediction
    if sample_index >= len(df_model):
        sample_index = 0
    
    original_row = df_model.iloc[sample_index].copy()
    original_features = pd.get_dummies(pd.DataFrame([original_row[feature_cols]]), drop_first=True)
    original_features = original_features.reindex(columns=X.columns, fill_value=0)
    original_pred = model.predict_proba(original_features)[0]
    
    # Modified prediction
    modified_row = original_row.copy()
    modified_row[protected_col] = new_value
    modified_features = pd.get_dummies(pd.DataFrame([modified_row[feature_cols]]), drop_first=True)
    modified_features = modified_features.reindex(columns=X.columns, fill_value=0)
    modified_pred = model.predict_proba(modified_features)[0]
    
    return {
        'original': {
            'attributes': {k: str(v) for k, v in original_row[feature_cols].items()},
            'prediction_probabilities': {
                'negative': round(float(original_pred[0]), 4),
                'positive': round(float(original_pred[1]), 4) if len(original_pred) > 1 else 0,
            },
            'predicted_class': int(model.predict(original_features)[0]),
        },
        'modified': {
            'changed_attribute': protected_col,
            'original_value': str(original_row[protected_col]),
            'new_value': new_value,
            'prediction_probabilities': {
                'negative': round(float(modified_pred[0]), 4),
                'positive': round(float(modified_pred[1]), 4) if len(modified_pred) > 1 else 0,
            },
            'predicted_class': int(model.predict(modified_features)[0]),
        },
        'prediction_shift': round(
            float((modified_pred[1] if len(modified_pred) > 1 else 0) - 
                  (original_pred[1] if len(original_pred) > 1 else 0)), 4
        ),
    }
