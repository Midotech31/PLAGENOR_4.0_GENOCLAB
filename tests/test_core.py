# tests/test_core.py — PLAGENOR 4.0 Core Unit Tests
# ARCH-07: Uses isolated SQLite database per test class
from __future__ import annotations
import os
import sys
import tempfile
import shutil
import unittest

# Ensure plagenor package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up isolated data dir BEFORE importing config
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="plagenor_test_")
os.environ["PLAGENOR_DATA_DIR"] = _TEST_DATA_DIR

import config  # noqa: E402
config.DATA_DIR = _TEST_DATA_DIR
config.DATABASE_FILE = os.path.join(_TEST_DATA_DIR, "test_plagenor.db")
config.BACKUPS_DIR = os.path.join(_TEST_DATA_DIR, "backups")
os.makedirs(config.BACKUPS_DIR, exist_ok=True)

# Reset thread-local connection to use the test database
import core.repository as repository  # noqa: E402
repository._local = __import__("threading").local()


def _reset_db():
    """Reset the thread-local connection and reinitialise schema."""
    repository._local = __import__("threading").local()
    repository.ensure_data_directory()


from core.exceptions import InvalidTransitionError, BudgetExceededError  # noqa: E402
from core.state_machine import validate_transition, get_allowed_next_states  # noqa: E402


class TestGenerateRequestId(unittest.TestCase):
    """Test readable request ID generation."""

    def setUp(self):
        _reset_db()

    def test_ibtikar_format(self):
        rid = repository.generate_request_id(config.CHANNEL_IBTIKAR)
        self.assertTrue(rid.startswith("IBK-"))
        parts = rid.split("-")
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[2]), 4)  # zero-padded

    def test_genoclab_format(self):
        rid = repository.generate_request_id(config.CHANNEL_GENOCLAB)
        self.assertTrue(rid.startswith("GCL-"))
        parts = rid.split("-")
        self.assertEqual(len(parts), 3)

    def test_auto_increment(self):
        r1 = repository.generate_request_id(config.CHANNEL_IBTIKAR)
        r2 = repository.generate_request_id(config.CHANNEL_IBTIKAR)
        seq1 = int(r1.split("-")[2])
        seq2 = int(r2.split("-")[2])
        self.assertEqual(seq2, seq1 + 1)

    def test_separate_channels(self):
        r1 = repository.generate_request_id(config.CHANNEL_IBTIKAR)
        r2 = repository.generate_request_id(config.CHANNEL_GENOCLAB)
        self.assertEqual(int(r1.split("-")[2]), 1)
        self.assertEqual(int(r2.split("-")[2]), 1)


class TestBudgetChecks(unittest.TestCase):
    """Test IBTIKAR budget validation."""

    def setUp(self):
        _reset_db()

    def test_budget_under_cap(self):
        from core.financial_engine import check_ibtikar_budget
        actor = {"id": "u1", "role": config.ROLE_PLATFORM_ADMIN}
        result = check_ibtikar_budget(1000.0, actor)
        self.assertFalse(result["exceeded"])
        self.assertGreater(result["remaining"], 0)

    def test_budget_over_cap_raises(self):
        from core.financial_engine import check_ibtikar_budget
        actor = {"id": "u1", "role": config.ROLE_PLATFORM_ADMIN}
        with self.assertRaises(BudgetExceededError):
            check_ibtikar_budget(config.IBTIKAR_BUDGET_CAP + 1, actor)

    def test_budget_over_cap_super_admin_allowed(self):
        from core.financial_engine import check_ibtikar_budget
        actor = {"id": "u1", "role": config.ROLE_SUPER_ADMIN}
        result = check_ibtikar_budget(config.IBTIKAR_BUDGET_CAP + 1, actor)
        self.assertTrue(result["exceeded"])
        self.assertTrue(result["override_allowed"])


class TestInvoiceGeneration(unittest.TestCase):
    """Test GENOCLAB invoice generation."""

    def setUp(self):
        _reset_db()

    def test_generate_invoice(self):
        from core.financial_engine import generate_invoice
        request = {
            "id": "req-001",
            "channel": config.CHANNEL_GENOCLAB,
            "title": "Test Service",
            "quote_amount": 10000,
            "client_id": "c1",
        }
        actor = {"id": "u1", "role": config.ROLE_FINANCE}
        invoice = generate_invoice(request, actor)
        self.assertIn("invoice_number", invoice)
        self.assertEqual(invoice["channel"], config.CHANNEL_GENOCLAB)
        self.assertEqual(invoice["subtotal_ht"], 10000)
        self.assertEqual(invoice["vat_amount"], round(10000 * config.VAT_RATE, 2))
        self.assertEqual(invoice["total_ttc"], round(10000 + 10000 * config.VAT_RATE, 2))
        self.assertTrue(invoice["locked"])

    def test_invoice_number_increments(self):
        from core.financial_engine import generate_invoice
        request = {
            "id": "req-001", "channel": config.CHANNEL_GENOCLAB,
            "title": "Test", "quote_amount": 5000, "client_id": "c1",
        }
        actor = {"id": "u1", "role": config.ROLE_FINANCE}
        inv1 = generate_invoice(request, actor)
        request["id"] = "req-002"
        inv2 = generate_invoice(request, actor)
        self.assertNotEqual(inv1["invoice_number"], inv2["invoice_number"])

    def test_invoice_ibtikar_rejected(self):
        from core.financial_engine import generate_invoice
        request = {"id": "req-x", "channel": config.CHANNEL_IBTIKAR}
        actor = {"id": "u1", "role": config.ROLE_FINANCE}
        with self.assertRaises(ValueError):
            generate_invoice(request, actor)


class TestPointsSystem(unittest.TestCase):
    """Test points and cheers for members."""

    def setUp(self):
        _reset_db()
        repository.save_member({
            "id": "m1", "name": "Test Member", "total_points": 0,
            "points_history": [], "cheers": [],
        })

    def test_add_points(self):
        actor = {"id": "admin1", "username": "admin", "full_name": "Admin User"}
        result = repository.add_points_to_member("m1", 25, "Bon travail", actor)
        self.assertIsNotNone(result)
        self.assertEqual(result["total_points"], 25)
        self.assertEqual(len(result["points_history"]), 1)

    def test_add_points_accumulates(self):
        actor = {"id": "admin1", "username": "admin"}
        repository.add_points_to_member("m1", 10, "Raison 1", actor)
        result = repository.add_points_to_member("m1", 15, "Raison 2", actor)
        self.assertEqual(result["total_points"], 25)
        self.assertEqual(len(result["points_history"]), 2)

    def test_add_cheer(self):
        actor = {"id": "admin1", "username": "admin", "full_name": "Admin"}
        result = repository.add_cheer_to_member("m1", "Excellent travail!", actor)
        self.assertIsNotNone(result)
        self.assertEqual(len(result["cheers"]), 1)
        self.assertEqual(result["cheers"][0]["message"], "Excellent travail!")

    def test_get_member_points(self):
        actor = {"id": "admin1", "username": "admin"}
        repository.add_points_to_member("m1", 50, "Test", actor)
        data = repository.get_member_points("m1")
        self.assertEqual(data["total_points"], 50)
        self.assertIsInstance(data["points_history"], list)
        self.assertIsInstance(data["cheers"], list)

    def test_nonexistent_member(self):
        actor = {"id": "admin1", "username": "admin"}
        result = repository.add_points_to_member("nonexistent", 10, "Test", actor)
        self.assertIsNone(result)


class TestWorkflowTransitions(unittest.TestCase):
    """Test state machine transitions."""

    def test_ibtikar_valid_transition(self):
        result = validate_transition(config.CHANNEL_IBTIKAR, "SUBMITTED", "VALIDATION_PEDAGOGIQUE")
        self.assertTrue(result)

    def test_ibtikar_rejection_valid(self):
        result = validate_transition(config.CHANNEL_IBTIKAR, "SUBMITTED", "REJECTED")
        self.assertTrue(result)

    def test_ibtikar_invalid_transition_raises(self):
        with self.assertRaises(InvalidTransitionError):
            validate_transition(config.CHANNEL_IBTIKAR, "SUBMITTED", "COMPLETED")

    def test_genoclab_valid_transition(self):
        result = validate_transition(config.CHANNEL_GENOCLAB, "REQUEST_CREATED", "QUOTE_DRAFT")
        self.assertTrue(result)

    def test_genoclab_invalid_transition_raises(self):
        with self.assertRaises(InvalidTransitionError):
            validate_transition(config.CHANNEL_GENOCLAB, "REQUEST_CREATED", "COMPLETED")

    def test_terminal_state_no_transitions(self):
        allowed = get_allowed_next_states(config.CHANNEL_IBTIKAR, "REJECTED")
        self.assertEqual(len(allowed), 0)

    def test_full_ibtikar_path(self):
        """Test that the entire IBTIKAR workflow path is valid."""
        path = ["DRAFT", "SUBMITTED", "VALIDATION_PEDAGOGIQUE", "VALIDATION_FINANCE",
                "PLATFORM_NOTE_GENERATED", "ASSIGNED", "SAMPLE_RECEIVED",
                "ANALYSIS_STARTED", "ANALYSIS_FINISHED", "REPORT_UPLOADED",
                "REPORT_VALIDATED", "COMPLETED", "CLOSED"]
        for i in range(len(path) - 1):
            result = validate_transition(config.CHANNEL_IBTIKAR, path[i], path[i + 1])
            self.assertTrue(result, f"Failed: {path[i]} -> {path[i+1]}")


class TestArchiveRequest(unittest.TestCase):
    """Test request archiving."""

    def setUp(self):
        _reset_db()
        repository.save_request({
            "id": "r1", "title": "Test Request", "status": "COMPLETED",
            "channel": config.CHANNEL_IBTIKAR, "archived": 0,
        })
        repository.save_request({
            "id": "r2", "title": "Other Request", "status": "IN_PROGRESS",
            "channel": config.CHANNEL_IBTIKAR, "archived": 0,
        })

    def test_archive_moves_request(self):
        result = repository.archive_request("r1")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "r1")

        active = repository.get_all_active_requests()
        active_ids = [r["id"] for r in active]
        self.assertNotIn("r1", active_ids)
        self.assertIn("r2", active_ids)

    def test_archive_nonexistent_returns_none(self):
        result = repository.archive_request("nonexistent")
        self.assertIsNone(result)


def tearDownModule():
    """Clean up test data directory."""
    if os.path.exists(_TEST_DATA_DIR):
        shutil.rmtree(_TEST_DATA_DIR, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
