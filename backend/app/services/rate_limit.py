"""Bounded per-process limiter for public abuse-sensitive endpoints."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException

_lock = threading.Lock()
_events: dict[str, deque[float]] = defaultdict(deque)


def enforce(key: str, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        bucket = _events[key]
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            retry = max(1, int(window_seconds - (now - bucket[0])))
            raise HTTPException(status_code=429, detail="Too many requests; try again later",
                                headers={"Retry-After": str(retry)})
        bucket.append(now)
        if len(_events) > 10000:
            stale = [name for name, values in _events.items() if not values or values[-1] <= cutoff]
            for name in stale[:1000]:
                _events.pop(name, None)


def client_key(request, action: str, identity: str = "") -> str:
    host = request.client.host if request.client else "unknown"
    return f"{action}:{host}:{identity.strip().lower()}"
