import unittest

from app.status_cache import InMemoryStatusCache, RedisStatusCache, build_status_cache


class StatusCacheTests(unittest.TestCase):
    def test_in_memory_status_cache_round_trips_status(self):
        cache = InMemoryStatusCache()

        cache.set_job_status("job-1", "queued")

        self.assertEqual(cache.get_job_status("job-1"), "queued")
        self.assertTrue(cache.ping())

    def test_build_status_cache_defaults_to_memory(self):
        cache = build_status_cache(None)

        self.assertIsInstance(cache, InMemoryStatusCache)

    def test_build_status_cache_rejects_unknown_scheme(self):
        with self.assertRaises(ValueError):
            build_status_cache("memcached://localhost:11211")

    def test_redis_status_cache_key_is_namespaced(self):
        cache = RedisStatusCache("redis://redis:6379/0", prefix="demo")

        self.assertEqual(cache._key("abc"), "demo:abc")


if __name__ == "__main__":
    unittest.main()
