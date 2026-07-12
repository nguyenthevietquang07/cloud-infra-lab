import unittest

from app.job_store import InMemoryJobStore
from app.jobs import serialize_job
from app.ops_pipeline import build_ops_pipeline_report, workflow_run_to_event
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

    def test_workflow_run_maps_to_operational_event(self):
        event = workflow_run_to_event(
            {
                "id": 123,
                "name": "ci",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
                "repository": {"full_name": "demo/repo"},
            }
        )

        self.assertEqual(event.event_type, "github_actions_completed")
        self.assertEqual(event.source, "demo/repo")
        self.assertEqual(event.attributes["conclusion"], "success")

    def test_ops_pipeline_report_contains_latency_measurements(self):
        report = build_ops_pipeline_report(
            source_url="fixture://demo/repo",
            processed_runs=2,
            event_latencies_ms=[1.0, 2.0],
            job_latencies_ms=[2.0, 3.0],
            fetch_job_latencies_ms=[3.0, 4.0],
        )

        self.assertEqual(report["processed_runs"], 2)
        self.assertEqual(report["operation_count"], 6)
        self.assertEqual(report["measurements"]["event_ingest_latency"]["p95_ms"], 2.0)


if __name__ == "__main__":
    unittest.main()
