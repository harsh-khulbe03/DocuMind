import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

# ponytail: in-memory, per-process. Fine for a single-replica deploy (HF Spaces);
# resets on restart and isn't shared across replicas. Swap for Redis if you scale out.
_hits: dict[str, deque] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # Behind the HF Spaces / Vercel proxy the real client is in X-Forwarded-For.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limiter(max_requests: int, window_seconds: int, name: str):
    """FastAPI dependency: sliding-window limit of max_requests per window per IP."""

    async def dependency(request: Request) -> None:
        key = f"{name}:{_client_ip(request)}"
        now = time.monotonic()
        dq = _hits[key]
        while dq and dq[0] <= now - window_seconds:
            dq.popleft()
        if len(dq) >= max_requests:
            retry = int(window_seconds - (now - dq[0])) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {retry}s.",
                headers={"Retry-After": str(retry)},
            )
        dq.append(now)

    return dependency
