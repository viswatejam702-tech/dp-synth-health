"""
Abstract Base Synthesizer Interface
===================================
Defines the contract for synthetic tabular data generators.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional


class BaseSynthesizer(ABC):
    def __init__(self, name: str, epsilon: Optional[float] = None, delta: float = 1e-5):
        self.name = name
        self.epsilon = epsilon
        self.delta = delta
        self.is_fitted = False
        self.feature_columns = []
        self.target_column = "cvd_risk"

    @abstractmethod
    def fit(self, df: pd.DataFrame, categorical_cols: list = None) -> "BaseSynthesizer":
        """Fits generator model on input dataset."""
        pass

    @abstractmethod
    def sample(self, n_samples: int, random_state: int = 42) -> pd.DataFrame:
        """Samples synthetic patient records from the trained distribution."""
        pass

    def get_privacy_guarantee(self) -> Dict[str, Any]:
        """Returns mathematical differential privacy parameters."""
        return {
            "model_name": self.name,
            "is_differentially_private": self.epsilon is not None and self.epsilon < float("inf"),
            "epsilon": self.epsilon if self.epsilon is not None else float("inf"),
            "delta": self.delta if self.epsilon is not None else 0.0,
            "privacy_tier": self._classify_tier()
        }

    def _classify_tier(self) -> str:
        if self.epsilon is None or self.epsilon == float("inf"):
            return "NON_PRIVATE (Overfitting / Memorization Risk)"
        if self.epsilon <= 0.5:
            return "ULTRA_STRONG_DP (Provable Privacy / Cryptographic Strength)"
        if self.epsilon <= 2.0:
            return "STRONG_DP (Standard Production Benchmark)"
        if self.epsilon <= 5.0:
            return "MODERATE_DP (Practical Trade-off)"
        return "RELAXED_DP (Higher Utility, Moderate Leakage Resistance)"
