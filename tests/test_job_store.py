import tempfile
import unittest
from pathlib import Path

from app.job_store import InMemoryJobStore, PostgresJobStore, SQLiteJobStore, build_job_store


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


class JobStoreFactoryTests(unittest.TestCase):
    def test_build_job_store_defaults_to_memory(self):
        store = build_job_store(None)

        self.assertIsInstance(store, InMemoryJobStore)

    def test_build_job_store_uses_sqlite_url(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.sqlite"
            store = build_job_store(f"sqlite:///{db_path.as_posix()}")

            self.assertIsInstance(store, SQLiteJobStore)

    def test_build_job_store_rejects_unknown_scheme(self):
        with self.assertRaises(ValueError):
            build_job_store("mysql://localhost/demo")

    def test_postgres_store_keeps_database_url(self):
        store = object.__new__(PostgresJobStore)
        store.database_url = "postgresql://portfolio:portfolio@postgres:5432/portfolio"

        self.assertEqual(store.database_url, "postgresql://portfolio:portfolio@postgres:5432/portfolio")


if __name__ == "__main__":
    unittest.main()
