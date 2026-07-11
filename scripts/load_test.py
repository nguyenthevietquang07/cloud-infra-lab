from __future__ import annotations

import argparse
import statistics
import time
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser(description="Small HTTP latency smoke test.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--requests", type=int, default=20)
    args = parser.parse_args()

    durations: list[float] = []
    for _ in range(args.requests):
        start = time.perf_counter()
        with urllib.request.urlopen(args.url, timeout=5) as response:
            response.read()
        durations.append((time.perf_counter() - start) * 1000)

    sorted_durations = sorted(durations)
    p95_index = max(0, int(len(sorted_durations) * 0.95) - 1)
    print(
        {
            "requests": args.requests,
            "mean_ms": round(statistics.mean(durations), 2),
            "p95_ms": round(sorted_durations[p95_index], 2),
            "max_ms": round(max(durations), 2),
        }
    )


if __name__ == "__main__":
    main()
