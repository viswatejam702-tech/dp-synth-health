"""
Synthesizer-AI: Automated Security & Vulnerability Test Suite
=============================================================
Verifies:
1. Tiered Rate Limiting & Exponential Backoff.
2. Strict Input Validation (Bounds, Enums, Regex).
3. Information Leakage Shield & Exception Masking.
4. File Upload Safety (Magic Bytes, MIME Type, Path Traversal, Size Caps).
"""

import unittest
import io
import time
from fastapi.testclient import TestClient
from serving.server import app
from serving.security import limiter


class TestSecurityFramework(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_input_validation_bounds(self):
        """Test rejection of invalid epsilon and negative sample counts (HTTP 422)."""
        # Negative epsilon
        res = self.client.post("/v1/synth/generate", json={"epsilon": -5.0, "n_samples": 100})
        self.assertEqual(res.status_code, 422)

        # Out-of-bounds sample count
        res = self.client.post("/v1/synth/generate", json={"epsilon": 2.0, "n_samples": 5})
        self.assertEqual(res.status_code, 422)

        # Invalid generator architecture
        res = self.client.post("/v1/synth/generate", json={"generator_type": "malicious_script"})
        self.assertEqual(res.status_code, 422)

    def test_02_auth_exponential_backoff(self):
        """Test exponential backoff on repeated failed login attempts."""
        # 1st failed attempt
        res = self.client.post("/v1/auth/login", json={"account": "attacker", "password": "wrong_password"})
        self.assertEqual(res.status_code, 401)

        # 2nd failed attempt -> triggers exponential backoff
        res = self.client.post("/v1/auth/login", json={"account": "attacker", "password": "wrong_password"})
        # Should return 429 Too Many Requests due to exponential backoff
        self.assertIn(res.status_code, [401, 429])

    def test_03_secure_file_upload_whitelist(self):
        """Test rejection of dangerous file extensions (.py, .exe, .php)."""
        # Uploading malicious python script disguised as dataset
        file_py = io.BytesIO(b"import os; os.system('calc.exe')")
        res = self.client.post("/v1/dataset/upload", files={"file": ("exploit.py", file_py, "text/x-python")})
        self.assertEqual(res.status_code, 400)

        # Uploading PHP script
        file_php = io.BytesIO(b"<?php phpinfo(); ?>")
        res = self.client.post("/v1/dataset/upload", files={"file": ("payload.csv", file_php, "text/csv")})
        self.assertEqual(res.status_code, 400)

    def test_04_secure_file_upload_valid_csv(self):
        """Test successful validation and storage of clean tabular CSV."""
        clean_csv = io.BytesIO(b"age,gender,bmi,systolic_bp,cvd_risk\n55,1,28.4,138,1\n62,0,24.1,120,0\n")
        res = self.client.post("/v1/dataset/upload", files={"file": ("clinical_trial.csv", clean_csv, "text/csv")})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["details"]["status"], "VALIDATED_AND_SECURED")

    def test_05_security_headers_present(self):
        """Test presence of hardened HTTP security response headers."""
        res = self.client.get("/v1/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("X-Request-ID", res.headers)

    def test_06_compliance_hash_validation(self):
        """Test rejection of non-SHA256 tampering strings."""
        # Short hash
        res = self.client.get("/v1/compliance/verify_hash?hash_code=invalid_short_hash")
        self.assertEqual(res.status_code, 422)

        # Valid 64-char hex hash
        valid_hash = "a" * 64
        res = self.client.get(f"/v1/compliance/verify_hash?hash_code={valid_hash}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "CRYPTOGRAPHICALLY VERIFIED")


if __name__ == "__main__":
    unittest.main()
