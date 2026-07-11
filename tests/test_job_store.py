import tempfile
import unittest
from pathlib import Path

from app.job_store import SQLiteJobStore


class SQLiteJobStoreTests(unittest.TestCase):
    def test_sqlite_store_persists_jobs_across_instances(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.sqlite"
            first_store = SQLiteJobStore(db_path)
            created = first_store.create("export", {"format": "json"})
            first_store.transition(created.id, "succeeded")

            second_store = SQLiteJobStore(db_path)
            fetched = second_store.get(created.id)

            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.status, "succeeded")
            self.assertEqual(fetched.payload["format"], "json")

    def test_sqlite_store_rejects_unknown_transition(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SQLiteJobStore(Path(temp_dir) / "jobs.sqlite")

            with self.assertRaises(KeyError):
                store.transition("missing", "succeeded")


if __name__ == "__main__":
    unittest.main()
