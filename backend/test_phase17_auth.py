"""
Test Suite: Phase 17 Authentication & Role-Based Access Control
Validates:
  A. Valid Registrar login
  B. Valid Faculty login
  C. Valid Student login
  D. Invalid password handling (401)
  E. Invalid email handling (401)
  F. /api/v1/auth/me with valid JWT token (200)
  G. /api/v1/auth/me without token (401)
  H. /api/v1/auth/me with malformed / expired token (401)
  I. No password or password_hash leaked in response payloads
  J. /api/v1/agent/chat works with and without authentication token
  K. Direct PostgreSQL connectivity & bcrypt hash verification
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.db.database import SessionLocal
from app.models.users import User
from app.auth.security import verify_password, create_access_token

client = TestClient(app)


class TestPhase17Authentication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n=======================================================")
        print("  CIRCULARFLOW AI - PHASE 17 AUTHENTICATION TEST SUITE  ")
        print("=======================================================")

    def test_01_db_users_have_password_hashes(self):
        """Test K: Database connection and presence of bcrypt password_hash."""
        db = SessionLocal()
        try:
            users = db.query(User).all()
            self.assertGreaterEqual(len(users), 3, "Expected at least 3 seeded users")
            for u in users:
                self.assertIsNotNone(u.password_hash, f"User {u.email} missing password_hash")
                self.assertTrue(u.password_hash.startswith("$2b$"), f"User {u.email} hash is not bcrypt")
            print("  [PASS] Test K: PostgreSQL users table contains valid bcrypt hashes.")
        finally:
            db.close()

    def test_02_valid_registrar_login(self):
        """Test A: Valid Registrar login returns JWT and correct role."""
        payload = {"email": "registrar@vignan.ac.in", "password": "registrar@123"}
        response = client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["email"], "registrar@vignan.ac.in")
        self.assertEqual(data["role"], "Registrar")
        self.assertEqual(data["user_id"], "usr-reg-01")
        # Ensure password_hash is not in response
        self.assertNotIn("password_hash", str(data))
        self.assertNotIn("password", str(data).lower().split("access_token")[0])
        print("  [PASS] Test A: Valid Registrar login successful.")

    def test_03_valid_faculty_login(self):
        """Test B: Valid Faculty login returns JWT and correct role."""
        payload = {"email": "hod.cse@vignan.ac.in", "password": "faculty@123"}
        response = client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["role"], "Faculty")
        self.assertEqual(data["user_id"], "usr-fac-01")
        print("  [PASS] Test B: Valid Faculty login successful.")

    def test_04_valid_student_login(self):
        """Test C: Valid Student login returns JWT and correct role."""
        payload = {"email": "vikram.22cse088@vignan.ac.in", "password": "student@123"}
        response = client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["role"], "Student")
        self.assertEqual(data["user_id"], "usr-stu-01")
        print("  [PASS] Test C: Valid Student login successful.")

    def test_05_invalid_password(self):
        """Test D: Invalid password returns 401 Unauthorized."""
        payload = {"email": "registrar@vignan.ac.in", "password": "WrongPassword999!"}
        response = client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid email/username or password", response.json()["detail"])
        print("  [PASS] Test D: Invalid password correctly rejected with HTTP 401.")

    def test_06_invalid_email(self):
        """Test E: Non-existent email returns 401 Unauthorized."""
        payload = {"email": "ghost.user@vignan.ac.in", "password": "AnyPassword123"}
        response = client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(response.status_code, 401)
        print("  [PASS] Test E: Non-existent email correctly rejected with HTTP 401.")

    def test_07_auth_me_with_valid_token(self):
        """Test F: /api/v1/auth/me with valid Bearer token returns current user."""
        # 1. Login
        login_res = client.post("/api/v1/auth/login", json={
            "email": "registrar@vignan.ac.in",
            "password": "registrar@123"
        })
        token = login_res.json()["access_token"]

        # 2. Call /auth/me
        headers = {"Authorization": f"Bearer {token}"}
        me_res = client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        user_data = me_res.json()
        self.assertEqual(user_data["id"], "usr-reg-01")
        self.assertEqual(user_data["email"], "registrar@vignan.ac.in")
        self.assertEqual(user_data["role"], "Registrar")
        self.assertNotIn("password_hash", user_data)
        print("  [PASS] Test F: /auth/me succeeds with valid Bearer token.")

    def test_08_auth_me_without_token(self):
        """Test G: /api/v1/auth/me without token returns 401 Unauthorized."""
        me_res = client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, 401)
        print("  [PASS] Test G: /auth/me rejected without token.")

    def test_09_auth_me_with_invalid_token(self):
        """Test H: /api/v1/auth/me with invalid or tampered token returns 401."""
        headers = {"Authorization": "Bearer invalid.tampered.token"}
        me_res = client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 401)
        print("  [PASS] Test H: /auth/me rejected with invalid token.")

    def test_10_agent_chat_with_and_without_token(self):
        """Test J: Existing /api/v1/agent/chat works with and without authentication."""
        # Call without token
        res_unauth = client.post(
            "/api/v1/agent/chat",
            json={"message": "which circular is active?"}
        )
        self.assertEqual(res_unauth.status_code, 200)
        self.assertIn("answer", res_unauth.json())

        # Call with token
        login_res = client.post("/api/v1/auth/login", json={
            "email": "hod.cse@vignan.ac.in",
            "password": "faculty@123"
        })
        token = login_res.json()["access_token"]
        res_auth = client.post(
            "/api/v1/agent/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "who has not acknowledged the latest circular?", "user_role": "Faculty"}
        )
        self.assertEqual(res_auth.status_code, 200)
        self.assertIn("answer", res_auth.json())
        print("  [PASS] Test J: /api/v1/agent/chat works seamlessly with and without auth.")


if __name__ == "__main__":
    unittest.main()
