"""
Statistical Fidelity and Distributional Distance Metrics
=========================================================
Computes statistical similarity between Real and Synthetic patient populations:
1. Wasserstein Distance (Earth Mover's Distance)
2. Jensen-Shannon Divergence (JSD)
3. Correlation Matrix Frobenius Norm Difference
4. Kolmogorov-Smirnov (KS) 2-Sample Test
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from scipy.stats import wasserstein_distance, ks_2samp
from scipy.spatial.distance import jensenshannon


class FidelityEvaluator:
    """
    Computes statistical similarity and distributional drift between real and synthetic data.
    """
    def __init__(self, continuous_cols: List[str] = None):
        self.continuous_cols = continuous_cols or [
            "age", "bmi", "systolic_bp", "diastolic_bp", "heart_rate",
            "blood_glucose", "hba1c", "cholesterol_total", "ldl", "hdl", "creatinine"
        ]

    def evaluate_fidelity(self, real_df: pd.DataFrame, syn_df: pd.DataFrame) -> Dict[str, Any]:
        wasserstein_scores = {}
        ks_stats = {}
        jsd_scores = {}

        for col in self.continuous_cols:
            if col in real_df.columns and col in syn_df.columns:
                r_vals = real_df[col].dropna().values
                s_vals = syn_df[col].dropna().values
                
                # 1. Wasserstein Distance (normalized by real std)
                std_r = max(1e-4, np.std(r_vals))
                w_dist = wasserstein_distance(r_vals, s_vals) / std_r
                wasserstein_scores[col] = round(float(w_dist), 4)

                # 2. Kolmogorov-Smirnov 2-Sample Test
                ks_res = ks_2samp(r_vals, s_vals)
                ks_stats[col] = {
                    "statistic": round(float(ks_res.statistic), 4),
                    "p_value": round(float(ks_res.pvalue), 4)
                }

                # 3. Jensen-Shannon Divergence on 30-bin histograms
                r_hist, bin_edges = np.histogram(r_vals, bins=30, density=True)
                s_hist, _ = np.histogram(s_vals, bins=bin_edges, density=True)
                # Add small epsilon for stability
                r_hist = (r_hist + 1e-6) / np.sum(r_hist + 1e-6)
                s_hist = (s_hist + 1e-6) / np.sum(s_hist + 1e-6)
                js_div = jensenshannon(r_hist, s_hist)
                jsd_scores[col] = round(float(js_div), 4)

        # 4. Correlation Matrix Frobenius Norm Difference
        common_cols = [c for c in self.continuous_cols if c in real_df.columns and c in syn_df.columns]
        corr_real = real_df[common_cols].corr().values
        corr_syn = syn_df[common_cols].corr().values
        frob_diff = np.linalg.norm(corr_real - corr_syn, ord='fro')
        norm_frob_diff = frob_diff / np.linalg.norm(corr_real, ord='fro')

        mean_w_dist = round(float(np.mean(list(wasserstein_scores.values()))), 4)
        mean_jsd = round(float(np.mean(list(jsd_scores.values()))), 4)

        return {
            "mean_normalized_wasserstein_distance": mean_w_dist,
            "mean_jensen_shannon_divergence": mean_jsd,
            "correlation_matrix_frobenius_drift": round(float(norm_frob_diff), 4),
            "feature_wasserstein_distances": wasserstein_scores,
            "feature_jsd_divergences": jsd_scores,
            "ks_test_results": ks_stats,
            "overall_fidelity_score_pct": round(max(0.0, (1.0 - (mean_w_dist * 0.4 + mean_jsd * 0.4 + norm_frob_diff * 0.2)) * 100.0), 2)
        }
