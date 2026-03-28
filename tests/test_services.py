# tests/test_services.py — PLAGENOR 4.0 Services Unit Tests
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
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="plagenor_test_svc_")
os.environ["PLAGENOR_DATA_DIR"] = _TEST_DATA_DIR

import config  # noqa: E402
config.DATA_DIR = _TEST_DATA_DIR
config.DATABASE_FILE = os.path.join(_TEST_DATA_DIR, "test_plagenor_svc.db")
config.BACKUPS_DIR = os.path.join(_TEST_DATA_DIR, "backups")
os.makedirs(config.BACKUPS_DIR, exist_ok=True)

# Reset thread-local connection to use the test database
import core.repository as repository  # noqa: E402
repository._local = __import__("threading").local()


def _reset_db():
    """Reset the thread-local connection and reinitialise schema."""
    repository._local = __import__("threading").local()
    repository.ensure_data_directory()


class TestPricingEngine(unittest.TestCase):
    """Test pricing calculations."""

    def test_per_sample_fixed(self):
        from services.pricing_engine import calculate_price
        service_def = {
            "service_code": "SVC001",
            "pricing": {
                "model": "per_sample_fixed",
                "unit_price": 5000,
                "currency": "DZD",
            },
        }
        samples = [{"name": "S1"}, {"name": "S2"}, {"name": "S3"}]
        result = calculate_price(service_def, {}, samples)
        self.assertEqual(result["pricing_model"], "per_sample_fixed")
        self.assertEqual(result["number_of_units"], 3)
        self.assertEqual(result["unit_price"], 5000)
        self.assertEqual(result["total"], 15000)
        self.assertEqual(result["currency"], "DZD")

    def test_per_sample_with_multiplier(self):
        from services.pricing_engine import calculate_price
        service_def = {
            "service_code": "SVC002",
            "pricing": {
                "model": "per_sample_table_row_with_multiplier",
                "base_price": {"non_pathogenic": 3000, "pathogenic": 5000},
                "multipliers": {"standard": 1.0, "premium": 1.5},
                "currency": "DZD",
            },
        }
        samples = [{"name": "S1"}, {"name": "S2"}]
        params = {"analysis_mode": "premium", "pathogenic": True}
        result = calculate_price(service_def, params, samples)
        self.assertEqual(result["unit_price"], 7500)
        self.assertEqual(result["total"], 15000)

    def test_empty_samples_raises(self):
        from services.pricing_engine import calculate_price
        service_def = {
            "service_code": "SVC001",
            "pricing": {"model": "per_sample_fixed", "unit_price": 5000},
        }
        with self.assertRaises(ValueError):
            calculate_price(service_def, {}, [])

    def test_no_pricing_raises(self):
        from services.pricing_engine import calculate_price
        with self.assertRaises(ValueError):
            calculate_price({"service_code": "X"}, {}, [{"name": "S1"}])

    def test_unsupported_model_raises(self):
        from services.pricing_engine import calculate_price
        service_def = {
            "service_code": "SVC",
            "pricing": {"model": "unknown_model"},
        }
        with self.assertRaises(ValueError):
            calculate_price(service_def, {}, [{"name": "S1"}])

    def test_format_price(self):
        from services.pricing_engine import format_price
        self.assertEqual(format_price(10000), "10,000 DZD")
        self.assertEqual(format_price(500, "EUR"), "500 EUR")


class TestNotificationService(unittest.TestCase):
    """Test notification creation and retrieval."""

    def setUp(self):
        _reset_db()

    def test_create_notification(self):
        notif = repository.create_notification({
            "user_id": "u1",
            "title": "Test Notification",
            "message": "Something happened",
        })
        self.assertIn("id", notif)
        self.assertIn("created_at", notif)
        self.assertFalse(notif["read"])

    def test_get_all_notifications(self):
        repository.create_notification({"user_id": "u1", "title": "N1"})
        repository.create_notification({"user_id": "u2", "title": "N2"})
        notifs = repository.get_all_notifications()
        self.assertEqual(len(notifs), 2)

    def test_mark_notification_read(self):
        notif = repository.create_notification({"user_id": "u1", "title": "Test"})
        repository.mark_notification_read(notif["id"])
        all_notifs = repository.get_all_notifications()
        found = [n for n in all_notifs if n["id"] == notif["id"]]
        self.assertTrue(found[0]["read"])


try:
    import streamlit  # noqa: F401
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False


@unittest.skipUnless(_HAS_STREAMLIT, "Streamlit not installed — skipping form_renderer tests")
class TestFormRenderer(unittest.TestCase):
    """Test form renderer utilities (non-UI parts)."""

    def test_validate_required_fields_pass(self):
        from services.form_renderer import validate_required_fields
        service_def = {
            "parameters": [
                {"name": "name", "required": True, "label": "Nom"},
                {"name": "email", "required": True, "label": "Email"},
            ],
        }
        params = {"name": "John", "email": "john@test.com"}
        errors = validate_required_fields(params, service_def)
        self.assertEqual(len(errors), 0)

    def test_validate_required_fields_missing(self):
        from services.form_renderer import validate_required_fields
        service_def = {
            "parameters": [
                {"name": "name", "required": True, "label": "Nom"},
                {"name": "email", "required": True, "label": "Email"},
            ],
        }
        params = {"name": "John"}
        errors = validate_required_fields(params, service_def)
        self.assertGreater(len(errors), 0)


class TestServicesCRUD(unittest.TestCase):
    """Test service CRUD operations."""

    def setUp(self):
        _reset_db()

    def test_save_and_get_service(self):
        svc = repository.save_service({
            "name": "Test Service", "service_code": "TST001",
            "channel": config.CHANNEL_IBTIKAR, "base_price": 5000,
        })
        self.assertIn("id", svc)
        all_svcs = repository.get_all_services()
        self.assertEqual(len(all_svcs), 1)

    def test_delete_service(self):
        svc = repository.save_service({
            "name": "To Delete", "service_code": "DEL001",
        })
        repository.delete_service(svc["id"])
        all_svcs = repository.get_all_services()
        self.assertEqual(len(all_svcs), 0)

    def test_get_services_for_channel(self):
        repository.save_service({
            "name": "IBK Service", "channel": config.CHANNEL_IBTIKAR,
            "channels": [config.CHANNEL_IBTIKAR],
        })
        repository.save_service({
            "name": "GCL Service", "channel": config.CHANNEL_GENOCLAB,
            "channels": [config.CHANNEL_GENOCLAB],
        })
        ibk = repository.get_services_for_channel(config.CHANNEL_IBTIKAR)
        self.assertEqual(len(ibk), 1)
        self.assertEqual(ibk[0]["name"], "IBK Service")


def tearDownModule():
    if os.path.exists(_TEST_DATA_DIR):
        shutil.rmtree(_TEST_DATA_DIR, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
