"""
FairGuard AI — Bias Mitigation Engine
Pre-processing mitigation algorithms to reduce dataset bias.
"""

import pandas as pd
import numpy as np


def apply_reweighing(df, label_col, protected_col, privileged_value, favorable_label=1):
    """Apply Reweighing algorithm: compute sample weights balancing protected groups."""
    df_clean = df[[protected_col, label_col]].dropna().copy()
    if df_clean[label_col].dtype == object:
        ul = df_clean[label_col].unique()
        df_clean[label_col] = df_clean[label_col].map({ul[0]: 0, ul[1]: 1})
    df_clean[label_col] = pd.to_numeric(df_clean[label_col], errors='coerce')
    df_clean = df_clean.dropna()

    n = len(df_clean)
    is_priv = df_clean[protected_col].astype(str) == str(privileged_value)
    is_fav = df_clean[label_col] == favorable_label

    p_priv = is_priv.sum() / n
    p_unpriv = (~is_priv).sum() / n
    p_fav = is_fav.sum() / n
    p_unfav = (~is_fav).sum() / n
    p_pf = (is_priv & is_fav).sum() / n
    p_pu = (is_priv & ~is_fav).sum() / n
    p_uf = (~is_priv & is_fav).sum() / n
    p_uu = (~is_priv & ~is_fav).sum() / n

    weights = np.ones(n)
    if p_pf > 0: weights[np.array(is_priv & is_fav)] = (p_priv * p_fav) / p_pf
    if p_pu > 0: weights[np.array(is_priv & ~is_fav)] = (p_priv * p_unfav) / p_pu
    if p_uf > 0: weights[np.array(~is_priv & is_fav)] = (p_unpriv * p_fav) / p_uf
    if p_uu > 0: weights[np.array(~is_priv & ~is_fav)] = (p_unpriv * p_unfav) / p_uu

    pr_b = is_fav[is_priv].mean() if is_priv.sum() > 0 else 0
    ur_b = is_fav[~is_priv].mean() if (~is_priv).sum() > 0 else 0
    spd_b = ur_b - pr_b
    di_b = ur_b / pr_b if pr_b > 0 else 0

    pw = weights[np.array(is_priv)]
    uw = weights[np.array(~is_priv)]
    pr_a = (weights[np.array(is_priv & is_fav)]).sum() / pw.sum() if pw.sum() > 0 else 0
    ur_a = (weights[np.array(~is_priv & is_fav)]).sum() / uw.sum() if uw.sum() > 0 else 0
    spd_a = ur_a - pr_a
    di_a = ur_a / pr_a if pr_a > 0 else 0

    return {
        'method': 'Reweighing',
        'description': 'Assigns sample weights to balance outcomes across protected groups.',
        'before': {'privileged_rate': round(pr_b*100,1), 'unprivileged_rate': round(ur_b*100,1),
                   'spd': round(spd_b,4), 'disparate_impact': round(di_b,4)},
        'after': {'privileged_rate': round(pr_a*100,1), 'unprivileged_rate': round(ur_a*100,1),
                  'spd': round(spd_a,4), 'disparate_impact': round(di_a,4)},
        'improvement': {'spd_reduction': round(abs(spd_b)-abs(spd_a),4)},
        'weights': {'min': round(float(weights.min()),4), 'max': round(float(weights.max()),4),
                    'mean': round(float(weights.mean()),4), 'samples': int(n)}
    }


def apply_sampling(df, label_col, protected_col, privileged_value, favorable_label=1):
    """Apply balanced sampling to equalize representation across groups."""
    dc = df.dropna(subset=[protected_col, label_col]).copy()
    if dc[label_col].dtype == object:
        ul = dc[label_col].unique()
        dc[label_col] = dc[label_col].map({ul[0]: 0, ul[1]: 1})
    dc[label_col] = pd.to_numeric(dc[label_col], errors='coerce').dropna()
    dc = dc.dropna(subset=[label_col])

    is_p = dc[protected_col].astype(str) == str(privileged_value)
    is_f = dc[label_col] == favorable_label
    pr_b = is_f[is_p].mean() if is_p.sum() > 0 else 0
    ur_b = is_f[~is_p].mean() if (~is_p).sum() > 0 else 0

    groups = {}
    for v in dc[protected_col].unique():
        for l in [0, 1]:
            m = (dc[protected_col].astype(str) == str(v)) & (dc[label_col] == l)
            groups[(str(v), l)] = dc[m]
    tc = max(len(g) for g in groups.values())
    parts = [g.sample(tc, replace=True, random_state=42) if len(g) < tc else g for g in groups.values()]
    bd = pd.concat(parts, ignore_index=True)

    is_pa = bd[protected_col].astype(str) == str(privileged_value)
    is_fa = bd[label_col] == favorable_label
    pr_a = is_fa[is_pa].mean() if is_pa.sum() > 0 else 0
    ur_a = is_fa[~is_pa].mean() if (~is_pa).sum() > 0 else 0

    return {
        'method': 'Balanced Sampling',
        'description': 'Oversamples underrepresented group+outcome combinations.',
        'before': {'privileged_rate': round(pr_b*100,1), 'unprivileged_rate': round(ur_b*100,1),
                   'spd': round(ur_b-pr_b,4), 'size': len(dc)},
        'after': {'privileged_rate': round(pr_a*100,1), 'unprivileged_rate': round(ur_a*100,1),
                  'spd': round(ur_a-pr_a,4), 'size': len(bd)},
    }
