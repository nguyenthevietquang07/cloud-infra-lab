import unittest

from app.jobs import InMemoryJobStore, serialize_job
from app.service import build_health_payload, normalize_event


class ServiceTests(unittest.TestCase):
    def test_health_payload_has_operational_checks(self):
        payload = build_health_payload("demo")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "demo")
        self.assertIn("database", payload["checks"])
        self.assertIn("cache", payload["checks"])

    def test_event_normalization_is_deterministic(self):
        payload = normalize_event({"event_type": " Deploy ", "source": " CI "})

        self.assertEqual(payload["event_type"], "deploy")
        self.assertEqual(payload["source"], "ci")
        self.assertTrue(payload["accepted"])

    def test_job_store_tracks_status_transitions(self):
        store = InMemoryJobStore()
        job = store.create("Report Export", {"format": "json"})
        updated = store.transition(job.id, "succeeded")
        serialized = serialize_job(updated)

        self.assertEqual(job.status, "queued")
        self.assertEqual(updated.status, "succeeded")
        self.assertEqual(serialized["kind"], "report_export")

    def test_job_store_rejects_invalid_status(self):
        store = InMemoryJobStore()
        job = store.create("event", {})

        with self.assertRaises(ValueError):
            store.transition(job.id, "maybe")


if __name__ == "__main__":
    unittest.main()
