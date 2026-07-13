from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse


class StatusCache(Protocol):
    def set_job_status(self, job_id: str, status: str) -> None:
        raise NotImplementedError

    def get_job_status(self, job_id: str) -> str | None:
        raise NotImplementedError

    def ping(self) -> bool:
        raise NotImplementedError


@dataclass
class InMemoryStatusCache:
    statuses: dict[str, str] = field(default_factory=dict)

    def set_job_status(self, job_id: str, status: str) -> None:
        self.statuses[job_id] = status

    def get_job_status(self, job_id: str) -> str | None:
        return self.statuses.get(job_id)

    def ping(self) -> bool:
        return True


class RedisStatusCache:
    def __init__(self, redis_url: str, prefix: str = "cloud-infra-lab:job-status") -> None:
        self.redis_url = redis_url
        self.prefix = prefix

    def set_job_status(self, job_id: str, status: str) -> None:
        self._client().set(self._key(job_id), status, ex=3600)

    def get_job_status(self, job_id: str) -> str | None:
        value = self._client().get(self._key(job_id))
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    def ping(self) -> bool:
        return bool(self._client().ping())

    def _key(self, job_id: str) -> str:
        return f"{self.prefix}:{job_id}"

    def _client(self):
        import redis

        return redis.Redis.from_url(self.redis_url)


def build_status_cache(redis_url: str | None = None) -> StatusCache:
    if not redis_url:
        return InMemoryStatusCache()
    parsed = urlparse(redis_url)
    if parsed.scheme == "redis":
        return RedisStatusCache(redis_url)
    raise ValueError(f"Unsupported REDIS_URL scheme: {parsed.scheme}")
