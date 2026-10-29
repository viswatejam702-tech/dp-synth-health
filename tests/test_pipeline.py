"""
Unit and Integration Test Suite for DP-Synth Health
===================================================
Tests generators, moments accountant, TSTR validation, and MIA defense.
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from data.data_loader import ClinicalDataLoader
from generators.privacy_accountant import MomentsAccountant
from generators.ctgan_generator import CTGANSynthesizer
from generators.dp_generator import DifferentiallyPrivateSynthesizer
from generators.copula_generator import GaussianCopulaSynthesizer
from validation.tstr_validator import TSTRValidator
from validation.mia_attacker import MembershipInferenceAttacker
from validation.fidelity_metrics import FidelityEvaluator
from compliance.dpdp_compliance import DPDPComplianceEngine


class TestDPSynthHealth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = ClinicalDataLoader(test_size=0.25, random_state=42)
        cls.train_df = cls.loader.train_df
        cls.test_df = cls.loader.test_df

    def test_data_loader_structure(self):
        """Verify data loader splits and clinical schema."""
        self.assertGreater(len(self.train_df), 500)
        self.assertGreater(len(self.test_df), 150)
        self.assertIn("cvd_risk", self.train_df.columns)
        self.assertIn("systolic_bp", self.train_df.columns)
        self.assertIn("hba1c", self.train_df.columns)

    def test_moments_accountant(self):
        """Verify RDP moments accountant conversion."""
        accountant = MomentsAccountant(target_delta=1e-5)
        sigma = accountant.calibrate_noise_multiplier(target_epsilon=2.0, steps=100, sample_rate=0.1)
        self.assertGreater(sigma, 0.0)
        eps = accountant.get_epsilon(steps=100, noise_multiplier=sigma, sample_rate=0.1)
        self.assertAlmostEqual(eps, 2.0, delta=0.2)

    def test_dp_synthesizer_sampling(self):
        """Verify DP synthesizer fits and produces valid clinical bounds."""
        gen = DifferentiallyPrivateSynthesizer(epsilon=2.0, delta=1e-5, random_state=42)
        gen.fit(self.train_df)
        syn = gen.sample(n_samples=50)
        
        self.assertEqual(len(syn), 50)
        self.assertEqual(len(syn.columns), len(self.train_df.columns))
        # Ensure non-negative vitals
        self.assertTrue((syn["systolic_bp"] >= 80.0).all())
        self.assertTrue((syn["blood_glucose"] >= 50.0).all())

    def test_tstr_validation_protocol(self):
        """Verify TSTR clinical utility evaluation."""
        gen = DifferentiallyPrivateSynthesizer(epsilon=5.0, random_state=42)
        gen.fit(self.train_df)
        syn = gen.sample(n_samples=200)

        validator = TSTRValidator(target_col="cvd_risk", random_state=42)
        res = validator.run_protocol(self.train_df, self.test_df, syn, model_name="DP-Synth Test")
        
        self.assertIn("tstr_synthetic_auc", res)
        self.assertIn("trtr_baseline_auc", res)
        self.assertGreater(res["tstr_synthetic_auc"], 0.60)

    def test_membership_inference_attack(self):
        """Verify shadow MIA attack simulator."""
        gen = DifferentiallyPrivateSynthesizer(epsilon=1.0, random_state=42)
        gen.fit(self.train_df)
        syn = gen.sample(n_samples=200)

        attacker = MembershipInferenceAttacker(random_state=42)
        res = attacker.run_shadow_mia_attack(self.train_df, self.test_df, syn)
        
        self.assertIn("mia_attack_auc", res)
        self.assertIn("mia_attack_accuracy", res)
        # Strong DP should keep attack AUC <= 0.65
        self.assertLessEqual(res["mia_attack_auc"], 0.65)

    def test_dpdp_compliance_engine(self):
        """Verify India DPDP Act certificate generator."""
        engine = DPDPComplianceEngine()
        cert_pass = engine.generate_compliance_certificate(
            model_name="DP-Synth (ε=2.0)",
            epsilon=2.0,
            delta=1e-5,
            mia_attack_auc=0.536,
            tstr_utility_auc=0.842,
            n_synthetic_records=1000
        )
        self.assertTrue(cert_pass["dpdp_passed"])
        self.assertTrue(cert_pass["overall_certified"])


if __name__ == "__main__":
    unittest.main()
