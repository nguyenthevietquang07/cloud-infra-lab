import unittest

from app.schemas import EventPayload, JobCreateRequest


class SchemaTests(unittest.TestCase):
    def test_event_payload_defaults_attributes(self):
        payload = EventPayload(event_type="Deploy", source="CI")

        self.assertEqual(payload.attributes, {})

    def test_job_create_request_defaults_payload(self):
        request = JobCreateRequest(kind="Export")

        self.assertEqual(request.source, "manual")
        self.assertEqual(request.payload, {})


if __name__ == "__main__":
    unittest.main()
