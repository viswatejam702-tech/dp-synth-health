"""
Clinical Patient Dataset Loader & Synthetic Stand-in Data Generator
===================================================================
Loads or generates realistic clinical patient records (Cardiovascular Disease & Metabolic Risk):
Features:
  - Demographics: age (years), gender (0/1), bmi (kg/m^2), smoking_status (0/1)
  - Vitals: systolic_bp (mmHg), diastolic_bp (mmHg), heart_rate (bpm), blood_glucose (mg/dL)
  - Lab Biomarkers: hba1c (%), total_cholesterol (mg/dL), ldl (mg/dL), hdl (mg/dL), creatinine (mg/dL)
  - Target: cvd_risk (0: Low Risk, 1: High Risk)
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(DATA_DIR, "real_patient_records.csv")


def generate_realistic_clinical_data(n_samples: int = 1000, random_state: int = 42) -> pd.DataFrame:
    """Generates synthetic-safe stand-in clinical data with realistic biological correlations."""
    np.random.seed(random_state)
    
    # Demographics
    age = np.random.normal(loc=54.0, scale=12.0, size=n_samples).clip(21, 88)
    gender = np.random.binomial(n=1, p=0.48, size=n_samples)  # 0: Female, 1: Male
    smoking = np.random.binomial(n=1, p=0.22 + 0.15 * gender, size=n_samples)
    bmi = np.random.normal(loc=26.8 + 0.05 * age, scale=4.5, size=n_samples).clip(16.0, 48.0)
    
    # Vitals (correlated with age & BMI)
    systolic_bp = (105.0 + 0.4 * age + 0.6 * bmi + 8.0 * smoking + np.random.normal(0, 10, n_samples)).clip(90, 210)
    diastolic_bp = (65.0 + 0.2 * age + 0.3 * bmi + 4.0 * smoking + np.random.normal(0, 6, n_samples)).clip(55, 125)
    heart_rate = np.random.normal(loc=74.0 + 4.0 * smoking, scale=9.0, size=n_samples).clip(48, 120)
    blood_glucose = (85.0 + 0.3 * age + 0.8 * bmi + np.random.normal(0, 18, n_samples)).clip(65, 340)
    
    # Biomarkers
    hba1c = (4.8 + 0.015 * blood_glucose + np.random.normal(0, 0.4, n_samples)).clip(4.2, 13.5)
    total_chol = (165.0 + 0.5 * age + 1.2 * bmi + np.random.normal(0, 25, n_samples)).clip(110, 350)
    hdl = (58.0 - 0.3 * bmi + 6.0 * (1 - gender) + np.random.normal(0, 8, n_samples)).clip(25, 95)
    ldl = (total_chol - hdl - 0.2 * blood_glucose + np.random.normal(0, 15, n_samples)).clip(50, 260)
    creatinine = (0.7 + 0.005 * age + 0.25 * gender + np.random.normal(0, 0.18, n_samples)).clip(0.4, 3.8)
    
    # Non-linear clinical CVD risk ground truth score
    logit = (
        -7.5
        + 0.05 * age
        + 0.6 * gender
        + 0.8 * smoking
        + 0.04 * (systolic_bp - 120)
        + 0.02 * (blood_glucose - 100)
        + 0.3 * (hba1c - 5.7)
        + 0.015 * (ldl - 100)
        - 0.03 * (hdl - 50)
        + 0.5 * (creatinine - 1.0)
    )
    prob_cvd = 1.0 / (1.0 + np.exp(-logit))
    cvd_risk = (np.random.uniform(0, 1, n_samples) < prob_cvd).astype(int)
    
    df = pd.DataFrame({
        "age": np.round(age, 1),
        "gender": gender,
        "bmi": np.round(bmi, 2),
        "smoking_status": smoking,
        "systolic_bp": np.round(systolic_bp, 1),
        "diastolic_bp": np.round(diastolic_bp, 1),
        "heart_rate": np.round(heart_rate, 1),
        "blood_glucose": np.round(blood_glucose, 1),
        "hba1c": np.round(hba1c, 2),
        "cholesterol_total": np.round(total_chol, 1),
        "ldl": np.round(ldl, 1),
        "hdl": np.round(hdl, 1),
        "creatinine": np.round(creatinine, 2),
        "cvd_risk": cvd_risk
    })
    
    return df


class ClinicalDataLoader:
    """Manages train/test splitting and standardized preprocessing for dual utility/privacy testing."""
    def __init__(self, test_size: float = 0.25, random_state: int = 42):
        self.test_size = test_size
        self.random_state = random_state
        self.df = self._get_or_create_data()
        
        # Split into D_train_real (used by generator) and D_test_real (held-out gold standard)
        self.train_df, self.test_df = self._split_data()
        
    def _get_or_create_data(self) -> pd.DataFrame:
        if os.path.exists(CSV_PATH):
            return pd.read_csv(CSV_PATH)
        df = generate_realistic_clinical_data(n_samples=1200, random_state=self.random_state)
        try:
            df.to_csv(CSV_PATH, index=False)
        except OSError:
            pass
        return df

    def _split_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        from sklearn.model_selection import train_test_split
        train_df, test_df = train_test_split(
            self.df,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=self.df["cvd_risk"]
        )
        return train_df.reset_index(drop=True), test_df.reset_index(drop=True)

    def get_feature_names(self) -> list:
        return [c for c in self.df.columns if c != "cvd_risk"]

    def get_categorical_features(self) -> list:
        return ["gender", "smoking_status"]

    def get_numerical_features(self) -> list:
        return [c for c in self.get_feature_names() if c not in self.get_categorical_features()]


if __name__ == "__main__":
    loader = ClinicalDataLoader()
    print(f"Loaded Real Dataset: Total={len(loader.df)}, Train={len(loader.train_df)}, Test={len(loader.test_df)}")
    print("Sample Records:")
    print(loader.train_df.head(3))
