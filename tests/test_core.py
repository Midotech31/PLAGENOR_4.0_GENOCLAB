# tests/test_core.py — PLAGENOR 4.0 Core Unit Tests
from __future__ import annotations
import json
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
config.USERS_FILE = os.path.join(_TEST_DATA_DIR, "users.json")
config.MEMBERS_FILE = os.path.join(_TEST_DATA_DIR, "members.json")
config.SERVICES_FILE = os.path.join(_TEST_DATA_DIR, "services.json")
config.ACTIVE_REQUESTS_FILE = os.path.join(_TEST_DATA_DIR, "active_requests.json")
config.ARCHIVED_REQUESTS_FILE = os.path.join(_TEST_DATA_DIR, "archived_requests.json")
config.INVOICES_FILE = os.path.join(_TEST_DATA_DIR, "invoices.json")
config.INVOICE_SEQUENCE_FILE = os.path.join(_TEST_DATA_DIR, "invoice_sequence.json")
config.REQUEST_SEQUENCE_FILE = os.path.join(_TEST_DATA_DIR, "request_sequence.json")
config.REVENUE_ARCHIVES_FILE = os.path.join(_TEST_DATA_DIR, "revenue_archives.json")
config.AUDIT_LOGS_FILE = os.path.join(_TEST_DATA_DIR, "audit_logs.json")
config.DOCUMENTS_FILE = os.path.join(_TEST_DATA_DIR, "documents.json")
config.NOTIFICATIONS_FILE = os.path.join(_TEST_DATA_DIR, "notifications.json")
config.OVERRIDE_LOG_FILE = os.path.join(_TEST_DATA_DIR, "override_logs.json")
config.BACKUPS_DIR = os.path.join(_TEST_DATA_DIR, "backups")
os.makedirs(config.BACKUPS_DIR, exist_ok=True)

# Now import modules that depend on config
from core import repository  # noqa: E402
# Patch repository file paths to match test config
repository.USERS_FILE = config.USERS_FILE
repository.MEMBERS_FILE = config.MEMBERS_FILE
repository.SERVICES_FILE = config.SERVICES_FILE
repository.ACTIVE_REQUESTS_FILE = config.ACTIVE_REQUESTS_FILE
repository.ARCHIVED_REQUESTS_FILE = config.ARCHIVED_REQUESTS_FILE
repository.INVOICES_FILE = config.INVOICES_FILE
repository.INVOICE_SEQUENCE_FILE = config.INVOICE_SEQUENCE_FILE
repository.REQUEST_SEQUENCE_FILE = config.REQUEST_SEQUENCE_FILE
repository.REVENUE_ARCHIVES_FILE = config.REVENUE_ARCHIVES_FILE
repository.AUDIT_LOGS_FILE = config.AUDIT_LOGS_FILE
repository.DOCUMENTS_FILE = config.DOCUMENTS_FILE
repository.NOTIFICATIONS_FILE = config.NOTIFICATIONS_FILE

from core.exceptions import InvalidTransitionError, BudgetExceededError  # noqa: E402
from core.state_machine import validate_transition, get_allowed_next_states  # noqa: E402


class TestGenerateRequestId(unittest.TestCase):
    """Test readable request ID generation."""

    def setUp(self):
        # Reset sequence file
        with open(config.REQUEST_SEQUENCE_FILE, "w") as f:
            json.dump({}, f)

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
        # Both should start at 1 for their channel
        self.assertEqual(int(r1.split("-")[2]), 1)
        self.assertEqual(int(r2.split("-")[2]), 1)


class TestBudgetChecks(unittest.TestCase):
    """Test IBTIKAR budget validation."""

    def setUp(self):
        # Clear request files
        for path in [config.ACTIVE_REQUESTS_FILE, config.ARCHIVED_REQUESTS_FILE,
                     config.INVOICES_FILE, config.AUDIT_LOGS_FILE]:
            with open(path, "w") as f:
                json.dump([], f)

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
        for path in [config.INVOICES_FILE, config.AUDIT_LOGS_FILE]:
            with open(path, "w") as f:
                json.dump([], f)
        with open(config.INVOICE_SEQUENCE_FILE, "w") as f:
            json.dump({"last": 0}, f)

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
        # Check totals: subtotal = 10000, vat = 10000 * 0.19 = 1900
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
        # Second invoice should have different number
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
        with open(config.MEMBERS_FILE, "w") as f:
            json.dump([{"id": "m1", "name": "Test Member", "total_points": 0,
                        "points_history": [], "cheers": []}], f)

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
        with open(config.ACTIVE_REQUESTS_FILE, "w") as f:
            json.dump([
                {"id": "r1", "title": "Test Request", "status": "COMPLETED"},
                {"id": "r2", "title": "Other Request", "status": "IN_PROGRESS"},
            ], f)
        with open(config.ARCHIVED_REQUESTS_FILE, "w") as f:
            json.dump([], f)

    def test_archive_moves_request(self):
        result = repository.archive_request("r1")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "r1")
        self.assertIn("archived_at", result)

        # Active should only have r2
        active = repository.get_all_active_requests()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["id"], "r2")

        # Archived should have r1
        archived = repository.get_all_archived_requests()
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0]["id"], "r1")

    def test_archive_nonexistent_returns_none(self):
        result = repository.archive_request("nonexistent")
        self.assertIsNone(result)


class TestMigrations(unittest.TestCase):
    """Test schema migration logic."""

    def setUp(self):
        # Clear schema version
        version_file = os.path.join(_TEST_DATA_DIR, "schema_version.json")
        if os.path.exists(version_file):
            os.remove(version_file)

    def test_run_migrations_creates_version_file(self):
        from core.migrations import run_migrations, SCHEMA_VERSION_FILE, CURRENT_SCHEMA_VERSION
        # Ensure data files exist
        for path in [config.ACTIVE_REQUESTS_FILE, config.ARCHIVED_REQUESTS_FILE,
                     config.MEMBERS_FILE, config.SERVICES_FILE]:
            if not os.path.exists(path):
                with open(path, "w") as f:
                    json.dump([], f)
        run_migrations()
        self.assertTrue(os.path.exists(SCHEMA_VERSION_FILE))
        with open(SCHEMA_VERSION_FILE) as f:
            data = json.load(f)
        self.assertEqual(data["version"], CURRENT_SCHEMA_VERSION)

    def test_migration_adds_missing_fields(self):
        from core.migrations import run_migrations, SCHEMA_VERSION_FILE
        # Write a request without display_id or urgency
        with open(config.ACTIVE_REQUESTS_FILE, "w") as f:
            json.dump([{"id": "r1", "title": "Old request"}], f)
        with open(config.MEMBERS_FILE, "w") as f:
            json.dump([{"id": "m1", "name": "Old member"}], f)
        with open(config.SERVICES_FILE, "w") as f:
            json.dump([{"id": "s1", "name": "Old service", "channel": "IBTIKAR"}], f)
        with open(config.ARCHIVED_REQUESTS_FILE, "w") as f:
            json.dump([], f)
        # Remove version file to trigger migration
        if os.path.exists(SCHEMA_VERSION_FILE):
            os.remove(SCHEMA_VERSION_FILE)

        run_migrations()

        # Check requests got display_id and urgency
        with open(config.ACTIVE_REQUESTS_FILE) as f:
            reqs = json.load(f)
        self.assertIn("display_id", reqs[0])
        self.assertIn("urgency", reqs[0])
        self.assertEqual(reqs[0]["urgency"], "Normal")

        # Check members got points fields
        with open(config.MEMBERS_FILE) as f:
            members = json.load(f)
        self.assertEqual(members[0]["total_points"], 0)
        self.assertIsInstance(members[0]["cheers"], list)

        # Check services got channel fields
        with open(config.SERVICES_FILE) as f:
            services = json.load(f)
        self.assertIn("channel_availability", services[0])
        self.assertIn("ibtikar_price", services[0])


def tearDownModule():
    """Clean up test data directory."""
    if os.path.exists(_TEST_DATA_DIR):
        shutil.rmtree(_TEST_DATA_DIR, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
