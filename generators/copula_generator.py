"""
Gaussian Copula Tabular Synthesizer
===================================
Models marginal distributions and joint dependencies via parametric Copulas.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Optional
from generators.base_generator import BaseSynthesizer


class GaussianCopulaSynthesizer(BaseSynthesizer):
    def __init__(self, random_state: int = 42):
        super().__init__(name="Gaussian Copula (Parametric Baseline)", epsilon=float("inf"), delta=0.0)
        self.random_state = random_state
        self.marginals = {}
        self.corr_matrix = None

    def fit(self, df: pd.DataFrame, categorical_cols: list = None) -> "GaussianCopulaSynthesizer":
        np.random.seed(self.random_state)
        self.feature_columns = list(df.columns)
        cat_cols = categorical_cols or ["gender", "smoking_status", "cvd_risk"]

        transformed_cols = []
        for col in self.feature_columns:
            data = df[col].values
            if col in cat_cols:
                # Empirical discrete CDF
                vals, counts = np.unique(data, return_counts=True)
                probs = counts / len(data)
                cum_probs = np.cumsum(probs)
                self.marginals[col] = {"type": "discrete", "vals": vals, "cum_probs": cum_probs}
                
                # Transform to Uniform (0, 1) and standard normal
                u = np.array([cum_probs[np.where(vals == v)[0][0]] - (probs[np.where(vals == v)[0][0]] / 2.0) for v in data])
                z = stats.norm.ppf(np.clip(u, 1e-4, 1 - 1e-4))
            else:
                # Continuous normal distribution fitting
                mean, std = np.mean(data), max(1e-4, np.std(data))
                self.marginals[col] = {"type": "continuous", "mean": mean, "std": std}
                z = (data - mean) / std

            transformed_cols.append(z.reshape(-1, 1))

        Z = np.hstack(transformed_cols)
        self.corr_matrix = np.corrcoef(Z, rowvar=False) + 1e-5 * np.eye(len(self.feature_columns))
        self.is_fitted = True
        return self

    def sample(self, n_samples: int, random_state: int = 42) -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError("Synthesizer must be fitted before sampling.")

        np.random.seed(random_state)
        Z_syn = np.random.multivariate_normal(
            mean=np.zeros(len(self.feature_columns)),
            cov=self.corr_matrix,
            size=n_samples
        )

        out_cols = {}
        for idx, col in enumerate(self.feature_columns):
            z = Z_syn[:, idx]
            info = self.marginals[col]
            if info["type"] == "discrete":
                u = stats.norm.cdf(z)
                vals = info["vals"]
                cum_probs = info["cum_probs"]
                cat_sampled = np.searchsorted(cum_probs, u)
                cat_sampled = np.clip(cat_sampled, 0, len(vals) - 1)
                out_cols[col] = vals[cat_sampled]
            else:
                recovered = (z * info["std"]) + info["mean"]
                out_cols[col] = np.round(recovered, 2)

        df_syn = pd.DataFrame(out_cols)
        return df_syn[self.feature_columns]
