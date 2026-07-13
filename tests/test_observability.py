import io
import json
import logging
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.observability import ACCESS_LOGGER_NAME, REQUEST_ID_HEADER, build_access_log


class ObservabilityTests(unittest.TestCase):
    def test_access_log_uses_safe_structured_fields(self):
        event = build_access_log(
            request_id="req-1",
            method="GET",
            path="/health",
            status_code=200,
            duration_ms=1.23456,
        )

        self.assertEqual(event["event"], "http_request")
        self.assertEqual(event["duration_ms"], 1.2346)
        self.assertNotIn("headers", event)
        self.assertNotIn("body", event)

    def test_request_id_is_echoed_and_logged(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger(ACCESS_LOGGER_NAME)
        previous_level = logger.level
        previous_propagate = logger.propagate
        logger.setLevel(logging.INFO)
        logger.propagate = False
        logger.addHandler(handler)
        try:
            client = TestClient(app)
            response = client.get("/health", headers={REQUEST_ID_HEADER: "test-request-id"})
        finally:
            logger.removeHandler(handler)
            logger.setLevel(previous_level)
            logger.propagate = previous_propagate

        self.assertEqual(response.headers[REQUEST_ID_HEADER], "test-request-id")
        log_line = stream.getvalue().strip().splitlines()[-1]
        parsed = json.loads(log_line)
        self.assertEqual(parsed["request_id"], "test-request-id")
        self.assertEqual(parsed["method"], "GET")
        self.assertEqual(parsed["path"], "/health")
        self.assertEqual(parsed["status_code"], 200)


if __name__ == "__main__":
    unittest.main()
