"""
Test Suite: Phase 20 Recipient Resolution for Circular Notifications
Validates:
  1. Recipient resolution for campus-wide circulars (CIRC-2026-095) resolves at least 1 recipient.
  2. All resolved recipient emails are valid and normalized to lowercase.
  3. Matching users from the users table have their user_id attached.
  4. Publisher is excluded when other recipients exist.
  5. Governance fallback correctly resolves Department HODs and Registrar when no direct match exists.
"""

import os
import sys
import unittest

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.circulars import Circular
from app.models.users import User
from app.models.recipients import Recipient
from app.services.email_service import resolve_circular_recipients, _is_valid_email


class TestPhase20RecipientResolution(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n=======================================================")
        print("  PHASE 20: CIRCULAR RECIPIENT RESOLUTION TEST SUITE    ")
        print("=======================================================")

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_email_validation_helper(self):
        """Test that email validator accepts valid emails and rejects invalid ones."""
        self.assertTrue(_is_valid_email("registrar@vignan.ac.in"))
        self.assertTrue(_is_valid_email("hod.cse@vignan.ac.in"))
        self.assertTrue(_is_valid_email("user.test+label@domain.co.uk"))

        self.assertFalse(_is_valid_email(""))
        self.assertFalse(_is_valid_email(None))
        self.assertFalse(_is_valid_email("notanemail"))
        self.assertFalse(_is_valid_email("@vignan.ac.in"))
        self.assertFalse(_is_valid_email("user@"))

    def test_02_resolve_campus_wide_circular_circ_007(self):
        """Test: CIRC-2026-095 (All Campus Occupants) resolves at least 1 recipient."""
        circ = self.db.query(Circular).filter(Circular.ref_no == "CIRC-2026-095").first()
        if not circ:
            circ = self.db.query(Circular).filter(Circular.id == "circ-007").first()

        self.assertIsNotNone(circ, "Expected CIRC-2026-095 / circ-007 to exist in seeded DB")

        recipients = resolve_circular_recipients(
            self.db,
            circular_id=circ.id,
            circular_ref=circ.ref_no,
            department=circ.department,
            target_audience=circ.target_audience,
            published_by_email="registrar@vignan.ac.in",
        )

        self.assertGreater(len(recipients), 0, "Expected at least 1 recipient resolved for CIRC-2026-095")
        print(f"  [PASS] CIRC-2026-095 resolved {len(recipients)} recipients.")

        # Check all emails are valid and lowercase
        for email, data in recipients.items():
            self.assertTrue(_is_valid_email(email), f"Invalid email: {email}")
            self.assertEqual(email, email.lower(), f"Email not lowercased: {email}")
            self.assertIn("name", data)
            self.assertIn("source", data)

        # Confirm publisher (registrar@vignan.ac.in) was excluded since other recipients exist
        self.assertNotIn("registrar@vignan.ac.in", recipients)

    def test_03_user_joining_populates_user_id(self):
        """Test: Recipients matching a user in the users table have user_id attached."""
        faculty_user = self.db.query(User).filter(User.email == "hod.cse@vignan.ac.in").first()
        self.assertIsNotNone(faculty_user, "Expected hod.cse@vignan.ac.in in users table")

        recipients = resolve_circular_recipients(
            self.db,
            circular_id="test-circ",
            circular_ref="TEST-001",
            department="Computer Science & Engineering",
            target_audience=["All Faculty"],
            published_by_email=None,
        )

        self.assertIn("hod.cse@vignan.ac.in", recipients)
        self.assertEqual(
            recipients["hod.cse@vignan.ac.in"]["user_id"],
            faculty_user.id,
            "Expected user_id to match faculty_user.id",
        )
        print("  [PASS] User joining successfully attached user_id to matched recipient.")

    def test_04_governance_fallback_when_no_direct_match(self):
        """Test: Governance fallback resolves Department HODs + Registrar when no match exists."""
        recipients = resolve_circular_recipients(
            self.db,
            circular_id="test-empty",
            circular_ref="TEST-EMPTY-001",
            department="Nonexistent Department XYZ",
            target_audience=["Nonexistent Audience 123"],
            published_by_email=None,
        )

        self.assertGreater(len(recipients), 0, "Expected fallback to resolve at least 1 recipient")
        # Check that at least one HOD or Registrar is in the resolved list
        hod_emails = {
            r.email.lower() for r in self.db.query(Recipient).filter(Recipient.role == "HOD").all()
        }
        matched_hods = set(recipients.keys()) & hod_emails
        self.assertGreater(len(matched_hods), 0, "Expected at least 1 HOD in fallback recipients")
        print(f"  [PASS] Governance fallback resolved {len(recipients)} recipients including {len(matched_hods)} HODs.")


if __name__ == "__main__":
    unittest.main()
