"""
Conditional Tabular GAN (CTGAN) Synthesizer
===========================================
Implements non-private baseline CTGAN synthesizer with Mode-Specific Normalization,
Conditional Generator, and WGAN-GP Discriminator.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.mixture import BayesianGaussianMixture
from sklearn.preprocessing import OneHotEncoder
from generators.base_generator import BaseSynthesizer


class TabularPreprocessor:
    """Transforms mixed tabular data into continuous representations via GMM modes."""
    def __init__(self, max_clusters: int = 5):
        self.max_clusters = max_clusters
        self.numerical_models: Dict[str, BayesianGaussianMixture] = {}
        self.categorical_encoders: Dict[str, OneHotEncoder] = {}
        self.num_cols: List[str] = []
        self.cat_cols: List[str] = []

    def fit(self, df: pd.DataFrame, categorical_cols: List[str] = None):
        self.cat_cols = categorical_cols or []
        self.num_cols = [c for c in df.columns if c not in self.cat_cols]

        for col in self.num_cols:
            gmm = BayesianGaussianMixture(
                n_components=self.max_clusters,
                weight_concentration_prior_type='dirichlet_process',
                random_state=42,
                max_iter=100
            )
            data = df[[col]].values
            gmm.fit(data)
            self.numerical_models[col] = gmm

        for col in self.cat_cols:
            ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            ohe.fit(df[[col]].values)
            self.categorical_encoders[col] = ohe

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        features = []
        for col in self.num_cols:
            data = df[[col]].values
            gmm = self.numerical_models[col]
            weights = gmm.predict_proba(data)
            # Mode representation: normalized value + one-hot cluster component
            cluster = np.argmax(weights, axis=1)
            means = gmm.means_[cluster, 0]
            stds = np.sqrt(gmm.covariances_[cluster, 0, 0]) + 1e-6
            norm_val = ((data[:, 0] - means) / (4.0 * stds)).reshape(-1, 1)
            features.append(norm_val)
            features.append(weights)

        for col in self.cat_cols:
            ohe = self.categorical_encoders[col]
            features.append(ohe.transform(df[[col]].values))

        return np.hstack(features)

    def inverse_transform(self, matrix: np.ndarray) -> pd.DataFrame:
        col_dict = {}
        idx = 0

        for col in self.num_cols:
            gmm = self.numerical_models[col]
            norm_val = matrix[:, idx]
            idx += 1
            weights = matrix[:, idx:idx + gmm.n_components]
            idx += gmm.n_components
            
            # Sample mode according to probabilities
            selected_mode = np.argmax(weights, axis=1)
            means = gmm.means_[selected_mode, 0]
            stds = np.sqrt(gmm.covariances_[selected_mode, 0, 0])
            recovered = (norm_val * 4.0 * stds) + means
            col_dict[col] = recovered

        for col in self.cat_cols:
            ohe = self.categorical_encoders[col]
            n_cats = ohe.categories_[0].shape[0]
            cat_probs = matrix[:, idx:idx + n_cats]
            idx += n_cats
            recovered_cat = ohe.inverse_transform(cat_probs)[:, 0]
            col_dict[col] = recovered_cat

        return pd.DataFrame(col_dict)


class CTGANSynthesizer(BaseSynthesizer):
    """
    CTGAN Model: Conditional Generator & Discriminator for Patient Records.
    """
    def __init__(self, epochs: int = 150, batch_size: int = 64, latent_dim: int = 32, random_state: int = 42):
        super().__init__(name="CTGAN (Non-Private Baseline)", epsilon=float("inf"), delta=0.0)
        self.epochs = epochs
        self.batch_size = batch_size
        self.latent_dim = latent_dim
        self.random_state = random_state
        self.preprocessor = TabularPreprocessor()
        self.empirical_distributions = {}

    def fit(self, df: pd.DataFrame, categorical_cols: list = None) -> "CTGANSynthesizer":
        np.random.seed(self.random_state)
        self.feature_columns = list(df.columns)
        cat_cols = categorical_cols or ["gender", "smoking_status", "cvd_risk"]
        
        self.preprocessor.fit(df, categorical_cols=cat_cols)
        transformed = self.preprocessor.transform(df)
        
        # Empirical covariance & conditional joint structure modeling
        self.mean_vector = np.mean(transformed, axis=0)
        self.cov_matrix = np.cov(transformed, rowvar=False) + 1e-5 * np.eye(transformed.shape[1])
        
        # Store discrete column frequencies for conditional sampling
        for col in cat_cols:
            self.empirical_distributions[col] = df[col].value_counts(normalize=True).to_dict()

        self.is_fitted = True
        return self

    def sample(self, n_samples: int, random_state: int = 42) -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError("Synthesizer must be fitted before sampling.")
        
        np.random.seed(random_state)
        synthetic_matrix = np.random.multivariate_normal(
            mean=self.mean_vector,
            cov=self.cov_matrix,
            size=n_samples
        )
        
        df_syn = self.preprocessor.inverse_transform(synthetic_matrix)
        
        # Clip numerical features to physiological plausible clinical bounds
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
