import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.security import require_api_key


class SecurityTests(unittest.TestCase):
    def test_api_key_is_optional_for_local_development(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(require_api_key(None))

    def test_configured_api_key_accepts_matching_header(self):
        with patch.dict(os.environ, {"API_KEY": "secret"}, clear=True):
            self.assertIsNone(require_api_key("secret"))

    def test_configured_api_key_rejects_missing_header(self):
        with patch.dict(os.environ, {"API_KEY": "secret"}, clear=True):
            with self.assertRaises(HTTPException) as context:
                require_api_key(None)

        self.assertEqual(context.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
