"""
Train on Synthetic, Test on Real (TSTR) Clinical Utility Validation Protocol
===========================================================================
Gold standard empirical validation:
1. TRTR (Train Real, Test Real): Baseline upper bound trained on real patient data.
2. TSTR (Train Synthetic, Test Real): Downstream models trained strictly on synthetic data,
   evaluated against the IDENTICAL held-out real test set.
3. Quantifies Utility Gap: AUC(TRTR) - AUC(TSTR) as epsilon changes.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, precision_score, recall_score, brier_score_loss
from sklearn.preprocessing import StandardScaler


class TSTRValidator:
    """
    Executes the TSTR clinical utility validation protocol across multiple downstream classifiers.
    """
    def __init__(self, target_col: str = "cvd_risk", random_state: int = 42):
        self.target_col = target_col
        self.random_state = random_state

    def _prepare_xy(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, list]:
        feature_cols = [c for c in df.columns if c != self.target_col]
        X = df[feature_cols].values
        y = df[self.target_col].values.astype(int)
        return X, y, feature_cols

    def evaluate_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_type: str = "gradient_boosting"
    ) -> Dict[str, float]:
        """Trains a classifier on (X_train, y_train) and evaluates on (X_test, y_test)."""
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        if model_type == "gradient_boosting":
            clf = HistGradientBoostingClassifier(random_state=self.random_state, max_iter=100)
        elif model_type == "random_forest":
            clf = RandomForestClassifier(n_estimators=100, random_state=self.random_state, max_depth=8)
        else:
            clf = LogisticRegression(random_state=self.random_state, max_iter=500)

        # Fit model
        clf.fit(X_train_scaled, y_train)

        # Predict probabilities and classes
        probs = clf.predict_proba(X_test_scaled)[:, 1]
        preds = (probs >= 0.5).astype(int)

        acc = accuracy_score(y_test, preds)
        auc = roc_auc_score(y_test, probs) if len(np.unique(y_test)) > 1 else 0.5
        f1 = f1_score(y_test, preds, zero_division=0)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        brier = brier_score_loss(y_test, probs)

        return {
            "accuracy": round(float(acc), 4),
            "roc_auc": round(float(auc), 4),
            "f1_score": round(float(f1), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "brier_score": round(float(brier), 4)
        }

    def run_protocol(
        self,
        train_real_df: pd.DataFrame,
        test_real_df: pd.DataFrame,
        synthetic_df: pd.DataFrame,
        model_name: str = "Synthesizer"
    ) -> Dict[str, Any]:
        """
        Runs comprehensive TRTR vs TSTR protocol on Real and Synthetic datasets.
        """
        X_real_train, y_real_train, feats = self._prepare_xy(train_real_df)
        X_real_test, y_real_test, _ = self._prepare_xy(test_real_df)
        X_syn_train, y_syn_train, _ = self._prepare_xy(synthetic_df)

        models = ["gradient_boosting", "random_forest", "logistic_regression"]
        results = {}

        for m in models:
            trtr_metrics = self.evaluate_model(X_real_train, y_real_train, X_real_test, y_real_test, model_type=m)
            tstr_metrics = self.evaluate_model(X_syn_train, y_syn_train, X_real_test, y_real_test, model_type=m)
            
            utility_gap_auc = round(trtr_metrics["roc_auc"] - tstr_metrics["roc_auc"], 4)
            utility_gap_acc = round(trtr_metrics["accuracy"] - tstr_metrics["accuracy"], 4)
            relative_utility_pct = round((tstr_metrics["roc_auc"] / max(1e-4, trtr_metrics["roc_auc"])) * 100.0, 2)

            results[m] = {
                "trtr_real_baseline": trtr_metrics,
                "tstr_synthetic_evaluated": tstr_metrics,
                "utility_gap_auc": utility_gap_auc,
                "utility_gap_accuracy": utility_gap_acc,
                "relative_utility_pct": relative_utility_pct
            }

        # Overall summary based on primary Gradient Boosting classifier
        primary = results["gradient_boosting"]
        return {
            "model_evaluated": model_name,
            "sample_size_syn": len(synthetic_df),
            "sample_size_test_real": len(test_real_df),
            "primary_classifier": "HistGradientBoosting",
            "trtr_baseline_auc": primary["trtr_real_baseline"]["roc_auc"],
            "tstr_synthetic_auc": primary["tstr_synthetic_evaluated"]["roc_auc"],
            "utility_gap_auc": primary["utility_gap_auc"],
            "relative_utility_pct": primary["relative_utility_pct"],
            "detailed_models": results
        }
