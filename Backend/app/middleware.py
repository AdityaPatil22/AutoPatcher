"""Security middleware: rate limiting, XSS/clickjacking headers, and API key scrubbing."""

import asyncio
import re
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

import app.config as config

_API_KEY_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),          # Gemini
    re.compile(r"sk-[0-9A-Za-z_-]{20,}"),           # OpenAI
    re.compile(r"nvapi-[0-9A-Za-z_-]{20,}"),        # NVIDIA NIM
]

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter per client IP.

    Applies a stricter limit to LLM endpoints (generate-fix, refine-fix)
    and a more generous global limit to everything else.
    """

    LLM_PATHS = {
        "/api/generate-fix",
        "/api/refine-fix",
        "/api/generate-prompt",
        "/api/refine-prompt",
    }

    def __init__(self, app, global_rpm: int = 60, llm_rpm: int = 10):
        super().__init__(app)
        self.global_rpm = global_rpm
        self.llm_rpm = llm_rpm
        self._window = 60
        self._cleanup_interval = 60

        self._global_hits: dict[str, list[float]] = defaultdict(list)
        self._llm_hits: dict[str, list[float]] = defaultdict(list)

        self._cleanup_task: asyncio.Task | None = None

    def _prune(
        self,
        bucket: dict[str, list[float]],
        ip: str,
        now: float,
    ) -> list[float]:
        entries = [t for t in bucket[ip] if now - t < self._window]

        if entries:
            bucket[ip] = entries
        else:
            bucket.pop(ip, None)

        return entries

    def _cleanup_bucket(
        self,
        bucket: dict[str, list[float]],
        cutoff: float,
    ) -> None:
        """Remove expired timestamps and stale IP entries."""
        stale_ips = []

        for ip, timestamps in bucket.items():
            timestamps[:] = [t for t in timestamps if t > cutoff]

            if not timestamps:
                stale_ips.append(ip)

        for ip in stale_ips:
            bucket.pop(ip, None)

    def _cleanup_once(self) -> None:
        """Remove expired entries from all rate-limit buckets."""
        cutoff = time.monotonic() - self._window

        self._cleanup_bucket(self._global_hits, cutoff)
        self._cleanup_bucket(self._llm_hits, cutoff)

    async def _cleanup_loop(self) -> None:
        """Periodically remove stale IPs from rate-limit buckets."""
        while True:
            await asyncio.sleep(self._cleanup_interval)
            self._cleanup_once()

    async def dispatch(self, request: Request, call_next):
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        path = request.url.path

        global_hits = self._prune(self._global_hits, ip, now)

        if len(global_hits) >= self.global_rpm:
            retry = max(1, int(self._window - (now - global_hits[0])))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={"Retry-After": str(retry)},
            )

        if path in self.LLM_PATHS:
            llm_hits = self._prune(self._llm_hits, ip, now)

            if len(llm_hits) >= self.llm_rpm:
                retry = max(1, int(self._window - (now - llm_hits[0])))
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "LLM rate limit exceeded. "
                            "Max 10 requests per minute."
                        )
                    },
                    headers={"Retry-After": str(retry)},
                )

            self._llm_hits[ip].append(now)

        self._global_hits[ip].append(now)

        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject headers that mitigate XSS, clickjacking, and MIME-type sniffing."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path.startswith("/api"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'"
            )
        return response


class APIKeyScrubMiddleware(BaseHTTPMiddleware):
    """Defence-in-depth: scrub API keys from JSON error responses.

    Only inspects API responses with 4xx/5xx status codes to keep the
    overhead near-zero for normal requests.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        is_api = request.url.path.startswith("/api")
        is_error = response.status_code >= 400
        is_json = "application/json" in response.headers.get("content-type", "")

        if not (is_api and is_error and is_json):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk if isinstance(chunk, bytes) else chunk.encode()

        body_str = body.decode()

        if config.API_KEY and config.API_KEY in body_str:
            body_str = body_str.replace(config.API_KEY, "[REDACTED]")

        for pattern in _API_KEY_PATTERNS:
            body_str = pattern.sub("[REDACTED]", body_str)

        return Response(
            content=body_str,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
