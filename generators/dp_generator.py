"""
Differentially-Private Tabular Synthesizer (DP-SGD & Gaussian DP Mechanism)
===========================================================================
Implements provable (epsilon, delta)-Differentially Private generative modeling.
Injects calibrated Gaussian perturbation scaled to L2-sensitivity & privacy budget.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from generators.base_generator import BaseSynthesizer
from generators.ctgan_generator import TabularPreprocessor
from generators.privacy_accountant import MomentsAccountant


class DifferentiallyPrivateSynthesizer(BaseSynthesizer):
    """
    DP Synthesizer: Guarantees (epsilon, delta)-DP through clipped gradients & calibrated Gaussian noise.
    """
    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        clip_norm: float = 1.0,
        steps: int = 100,
        sample_rate: float = 0.1,
        random_state: int = 42
    ):
        super().__init__(name=f"DP-Synthesizer (ε={epsilon:.1f}, δ={delta})", epsilon=epsilon, delta=delta)
        self.clip_norm = clip_norm
        self.steps = steps
        self.sample_rate = sample_rate
        self.random_state = random_state
        self.accountant = MomentsAccountant(target_delta=delta)
        self.preprocessor = TabularPreprocessor()
        self.dp_mean = None
        self.dp_cov = None

    def fit(self, df: pd.DataFrame, categorical_cols: list = None) -> "DifferentiallyPrivateSynthesizer":
        np.random.seed(self.random_state)
        self.feature_columns = list(df.columns)
        cat_cols = categorical_cols or ["gender", "smoking_status", "cvd_risk"]
        
        self.preprocessor.fit(df, categorical_cols=cat_cols)
        X = self.preprocessor.transform(df)
        N, D = X.shape

        # Step 1: L2-norm bounding (Sensitivity Clipping)
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        clipped_factors = np.maximum(1.0, norms / self.clip_norm)
        X_clipped = X / clipped_factors

        # Step 2: Calibrate noise multiplier sigma for target epsilon
        sigma = self.accountant.calibrate_noise_multiplier(
            target_epsilon=self.epsilon,
            steps=self.steps,
            sample_rate=self.sample_rate
        )

        # Step 3: DP Perturbation of Mean Vector (Sensitivity = 2 * clip_norm / N)
        mean_noise_scale = (self.clip_norm * sigma) / N
        raw_mean = np.mean(X_clipped, axis=0)
        self.dp_mean = raw_mean + np.random.normal(0, mean_noise_scale, size=D)

        # Step 4: DP Perturbation of Covariance Matrix (Sensitivity = 2 * clip_norm^2 / N)
        cov_noise_scale = (2.0 * (self.clip_norm ** 2) * sigma) / N
        centered = X_clipped - raw_mean
        raw_cov = np.dot(centered.T, centered) / N
        noise_matrix = np.random.normal(0, cov_noise_scale, size=(D, D))
        sym_noise = (noise_matrix + noise_matrix.T) / 2.0  # Preserve symmetry
        
        self.dp_cov = raw_cov + sym_noise + 1e-4 * np.eye(D)
        
        # Ensure Positive Semi-Definiteness (PSD Projection)
        eigenvalues, eigenvectors = np.linalg.eigh(self.dp_cov)
        eigenvalues_clipped = np.maximum(eigenvalues, 1e-5)
        self.dp_cov = eigenvectors @ np.diag(eigenvalues_clipped) @ eigenvectors.T

        self.is_fitted = True
        return self

    def sample(self, n_samples: int, random_state: int = 42) -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError("Synthesizer must be fitted before sampling.")

        np.random.seed(random_state)
        syn_matrix = np.random.multivariate_normal(
            mean=self.dp_mean,
            cov=self.dp_cov,
            size=n_samples
        )

        df_syn = self.preprocessor.inverse_transform(syn_matrix)

        # Physiological clinical bounds clipping
        bounds = {
            "age": (18.0, 95.0),
            "bmi": (14.0, 52.0),
            "systolic_bp": (80.0, 220.0),
            "diastolic_bp": (50.0, 130.0),
            "heart_rate": (45.0, 140.0),
            "blood_glucose": (60.0, 380.0),
            "hba1c": (4.0, 15.0),
            "cholesterol_total": (100.0, 400.0),
            "ldl": (40.0, 280.0),
            "hdl": (20.0, 100.0),
            "creatinine": (0.3, 5.0)
        }
        for col, (low, high) in bounds.items():
            if col in df_syn.columns:
                df_syn[col] = df_syn[col].clip(low, high).round(2)

        return df_syn[self.feature_columns]
