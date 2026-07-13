from __future__ import annotations

import json
import re
import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from .jobs import Job, create_job_record, transition_job_record


class JobStore(Protocol):
    def create(self, kind: str, payload: dict[str, object]) -> Job:
        raise NotImplementedError

    def get(self, job_id: str) -> Job | None:
        raise NotImplementedError

    def transition(self, job_id: str, status: str, error: str | None = None) -> Job:
        raise NotImplementedError


@dataclass
class InMemoryJobStore:
    jobs: dict[str, Job] = field(default_factory=dict)

    def create(self, kind: str, payload: dict[str, object]) -> Job:
        job = create_job_record(kind, payload)
        self.jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def transition(self, job_id: str, status: str, error: str | None = None) -> Job:
        existing = self.jobs.get(job_id)
        if existing is None:
            raise KeyError(f"Unknown job id: {job_id}")
        updated = transition_job_record(existing, status, error)
        self.jobs[job_id] = updated
        return updated


class SQLiteJobStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def create(self, kind: str, payload: dict[str, object]) -> Job:
        job = create_job_record(kind, payload)
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO jobs (id, kind, status, payload_json, created_at, updated_at, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.id,
                        job.kind,
                        job.status,
                        json.dumps(job.payload, sort_keys=True),
                        job.created_at,
                        job.updated_at,
                        job.error,
                    ),
                )
        return job

    def get(self, job_id: str) -> Job | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT id, kind, status, payload_json, created_at, updated_at, error
                FROM jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return _job_from_row(row)

    def transition(self, job_id: str, status: str, error: str | None = None) -> Job:
        existing = self.get(job_id)
        if existing is None:
            raise KeyError(f"Unknown job id: {job_id}")
        updated = transition_job_record(existing, status, error)
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    UPDATE jobs
                    SET status = ?, updated_at = ?, error = ?
                    WHERE id = ?
                    """,
                    (updated.status, updated.updated_at, updated.error, updated.id),
                )
        return updated

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    JOBS_TABLE_SQL
                )
                connection.execute(
                    JOBS_STATUS_INDEX_SQL
                )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)


class PostgresJobStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._initialize()

    def create(self, kind: str, payload: dict[str, object]) -> Job:
        job = create_job_record(kind, payload)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO jobs (id, kind, status, payload_json, created_at, updated_at, error)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        job.id,
                        job.kind,
                        job.status,
                        json.dumps(job.payload, sort_keys=True),
                        job.created_at,
                        job.updated_at,
                        job.error,
                    ),
                )
        return job

    def get(self, job_id: str) -> Job | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, kind, status, payload_json, created_at, updated_at, error
                    FROM jobs
                    WHERE id = %s
                    """,
                    (job_id,),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return _job_from_row(row)

    def transition(self, job_id: str, status: str, error: str | None = None) -> Job:
        existing = self.get(job_id)
        if existing is None:
            raise KeyError(f"Unknown job id: {job_id}")
        updated = transition_job_record(existing, status, error)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE jobs
                    SET status = %s, updated_at = %s, error = %s
                    WHERE id = %s
                    """,
                    (updated.status, updated.updated_at, updated.error, updated.id),
                )
        return updated

    def _initialize(self) -> None:
        last_error: Exception | None = None
        for _ in range(10):
            try:
                with self._connect() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(JOBS_TABLE_SQL)
                        cursor.execute(JOBS_STATUS_INDEX_SQL)
                return
            except Exception as error:
                last_error = error
                time.sleep(1.0)
        raise RuntimeError(f"Postgres job store initialization failed: {last_error}")

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)


def build_job_store(database_url: str | None = None) -> JobStore:
    if not database_url:
        return InMemoryJobStore()
    parsed = urlparse(database_url)
    if parsed.scheme in {"postgresql", "postgres"}:
        return PostgresJobStore(database_url)
    if parsed.scheme == "sqlite":
        return SQLiteJobStore(_sqlite_path_from_url(parsed.netloc, parsed.path))
    raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")


def _sqlite_path_from_url(netloc: str, path: str) -> str:
    raw_path = f"{netloc}{path}" if netloc else path
    if re.match(r"^/[A-Za-z]:/", raw_path):
        return raw_path[1:]
    return raw_path


JOBS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    error TEXT
)
"""

JOBS_STATUS_INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_jobs_status_updated ON jobs (status, updated_at DESC)"


def _job_from_row(row: tuple[object, ...]) -> Job:
    return Job(
        id=str(row[0]),
        kind=str(row[1]),
        status=str(row[2]),
        payload=json.loads(str(row[3])),
        created_at=str(row[4]),
        updated_at=str(row[5]),
        error=None if row[6] is None else str(row[6]),
    )
