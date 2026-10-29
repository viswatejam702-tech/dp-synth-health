"""
Membership Inference Attack (MIA) & Empirical Privacy Auditor
=============================================================
Evaluates whether a generator memorizes and regurgitates real patient records:
1. Shadow Model Membership Inference Attack (Distinguishing D_train vs D_test).
2. Distance to Closest Record (DCR) & 5th-percentile proximity analysis.
3. Nearest Neighbor Distance Ratio (NNDR).
4. Attack Success Target: ~50.0% (Random Guessing) for provably private generators.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist


class MembershipInferenceAttacker:
    """
    Simulates adversarial membership inference and memorization leakage attacks.
    """
    def __init__(self, random_state: int = 42):
        self.random_state = random_state

    def _normalize(self, train_df: pd.DataFrame, test_df: pd.DataFrame, syn_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        cols = [c for c in train_df.columns if c != "cvd_risk"]
        scaler = StandardScaler()
        X_train = scaler.fit_transform(train_df[cols].values)
        X_test = scaler.transform(test_df[cols].values)
        X_syn = scaler.transform(syn_df[cols].values)
        return X_train, X_test, X_syn

    def compute_dcr_metrics(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        X_syn: np.ndarray
    ) -> Dict[str, float]:
        """
        Computes Distance to Closest Record (DCR) from synthetic records to training vs test sets.
        """
        # Distance from synthetic to training members
        dists_to_train = cdist(X_syn, X_train, metric="euclidean")
        min_dists_train = np.min(dists_to_train, axis=1)

        # Distance from synthetic to held-out test non-members
        dists_to_test = cdist(X_syn, X_test, metric="euclidean")
        min_dists_test = np.min(dists_to_test, axis=1)

        # 5th percentile nearest neighbor distance (identifies potential exact/near-duplicates)
        p5_train = np.percentile(min_dists_train, 5)
        p5_test = np.percentile(min_dists_test, 5)
        median_dcr_train = np.median(min_dists_train)
        median_dcr_test = np.median(min_dists_test)

        # Nearest Neighbor Distance Ratio (NNDR): ratio of closest to 2nd closest
        sorted_train_dists = np.sort(dists_to_train, axis=1)
        nndr = np.mean(sorted_train_dists[:, 0] / np.maximum(1e-6, sorted_train_dists[:, 1]))

        # Memorization ratio: fraction of synthetic points significantly closer to training than test
        memorization_ratio = np.mean(min_dists_train < min_dists_test)

        return {
            "median_dcr_to_train": round(float(median_dcr_train), 4),
            "median_dcr_to_test": round(float(median_dcr_test), 4),
            "p5_min_distance_train": round(float(p5_train), 4),
            "p5_min_distance_test": round(float(p5_test), 4),
            "nndr_score": round(float(nndr), 4),
            "memorization_bias_ratio": round(float(memorization_ratio), 4)
        }

    def run_shadow_mia_attack(
        self,
        train_real_df: pd.DataFrame,
        test_real_df: pd.DataFrame,
        synthetic_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Executes a shadow classifier membership inference attack.
        Features extracted: minimum distance to synthetic dataset and density distribution.
        """
        X_train, X_test, X_syn = self._normalize(train_real_df, test_real_df, synthetic_df)
        
        # Attack feature for each real record: Distance to closest synthetic sample + mean distance
        dists_train_to_syn = cdist(X_train, X_syn, metric="euclidean")
        dists_test_to_syn = cdist(X_test, X_syn, metric="euclidean")

        min_d_train = np.min(dists_train_to_syn, axis=1).reshape(-1, 1)
        mean_d_train = np.mean(dists_train_to_syn, axis=1).reshape(-1, 1)
        std_d_train = np.std(dists_train_to_syn, axis=1).reshape(-1, 1)
        feats_train = np.hstack([min_d_train, mean_d_train, std_d_train])

        min_d_test = np.min(dists_test_to_syn, axis=1).reshape(-1, 1)
        mean_d_test = np.mean(dists_test_to_syn, axis=1).reshape(-1, 1)
        std_d_test = np.std(dists_test_to_syn, axis=1).reshape(-1, 1)
        feats_test = np.hstack([min_d_test, mean_d_test, std_d_test])

        # Balanced attack dataset: Members (1) vs Non-members (0)
        n_members = min(len(feats_train), len(feats_test))
        X_attack = np.vstack([feats_train[:n_members], feats_test[:n_members]])
        y_attack = np.array([1] * n_members + [0] * n_members)

        # 5-fold cross validation for attack model
        from sklearn.model_selection import StratifiedKFold
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.random_state)
        
        acc_scores = []
        auc_scores = []

        for train_idx, val_idx in skf.split(X_attack, y_attack):
            shadow_clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=self.random_state)
            shadow_clf.fit(X_attack[train_idx], y_attack[train_idx])
            probs = shadow_clf.predict_proba(X_attack[val_idx])[:, 1]
            preds = (probs >= 0.5).astype(int)

            acc_scores.append(accuracy_score(y_attack[val_idx], preds))
            auc_scores.append(roc_auc_score(y_attack[val_idx], probs))

        mean_attack_acc = round(float(np.mean(acc_scores)), 4)
        mean_attack_auc = round(float(np.mean(auc_scores)), 4)
        
        # Privacy advantage over random guessing (0.5)
        mia_advantage = round(max(0.0, (mean_attack_auc - 0.5) * 2.0), 4)

        dcr_metrics = self.compute_dcr_metrics(X_train, X_test, X_syn)

        return {
            "mia_attack_accuracy": mean_attack_acc,
            "mia_attack_auc": mean_attack_auc,
            "mia_privacy_advantage": mia_advantage,
            "privacy_risk_level": self._classify_privacy_risk(mean_attack_auc),
            "dcr_metrics": dcr_metrics,
            "random_guess_baseline": 0.50
        }

    def _classify_privacy_risk(self, attack_auc: float) -> str:
        if attack_auc <= 0.53:
            return "MINIMAL_RISK (Near-Random Defense / Robust Anonymization)"
        if attack_auc <= 0.60:
            return "LOW_RISK (Strong Generalization)"
        if attack_auc <= 0.72:
            return "MODERATE_RISK (Mild Proximity Leakage)"
        return "HIGH_RISK (Overfitted / Memorization Vulnerability)"
