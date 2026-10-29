"""
Synthesizer-AI: Enterprise Security & Rate Limiting Module
==========================================================
Provides:
1. Configurable Tiered Token-Bucket & Sliding-Window Rate Limiter.
2. Per-IP and Per-Account Auth Rate Limiting with Exponential Backoff.
3. Global Information Leakage Shield & Exception Masking.
4. Cryptographic Request ID Tracing.
"""

import os
import time
import math
import logging
import uuid
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

load_dotenv()

# Logger setup
logger = logging.getLogger("synthesizer_ai.security")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [SECURITY] %(message)s"))
    logger.addHandler(ch)

# Configuration from Environment Variables (Strictly non-hardcoded)
RATE_LIMIT_AUTH_PER_MIN = int(os.getenv("RATE_LIMIT_AUTH_PER_MIN", "5"))
RATE_LIMIT_PUBLIC_PER_MIN = int(os.getenv("RATE_LIMIT_PUBLIC_PER_MIN", "60"))
RATE_LIMIT_COMPUTE_PER_MIN = int(os.getenv("RATE_LIMIT_COMPUTE_PER_MIN", "20"))
RATE_LIMIT_BACKOFF_FACTOR = float(os.getenv("RATE_LIMIT_BACKOFF_FACTOR", "2.0"))


class TieredRateLimiter:
    """
    Tiered Sliding-Window Rate Limiter with Exponential Backoff for Authentication routes.
    """
    def __init__(self):
        # Map: key -> list of timestamps
        self.request_history: Dict[str, list] = {}
        # Map: key (account/ip) -> (failed_attempts_count, lock_until_timestamp)
        self.auth_backoff: Dict[str, Tuple[int, float]] = {}

    def _clean_old_requests(self, key: str, window_seconds: float = 60.0):
        now = time.time()
        if key in self.request_history:
            self.request_history[key] = [t for t in self.request_history[key] if now - t < window_seconds]

    def check_rate_limit(self, key: str, max_requests: int, window_seconds: float = 60.0) -> Tuple[bool, int, float]:
        """
        Returns (is_allowed, remaining_requests, retry_after_seconds).
        """
        now = time.time()
        self._clean_old_requests(key, window_seconds)
        history = self.request_history.get(key, [])

        if len(history) >= max_requests:
            oldest = history[0]
            retry_after = max(1.0, window_seconds - (now - oldest))
            return False, 0, retry_after

        history.append(now)
        self.request_history[key] = history
        remaining = max_requests - len(history)
        return True, remaining, 0.0

    def check_auth_backoff(self, ip: str, account: Optional[str] = None) -> Tuple[bool, float]:
        """
        Checks exponential backoff for authentication attempts.
        """
        now = time.time()
        keys_to_check = [f"ip:{ip}"]
        if account:
            keys_to_check.append(f"acct:{account}")

        for k in keys_to_check:
            if k in self.auth_backoff:
                fails, lock_until = self.auth_backoff[k]
                if now < lock_until:
                    return False, lock_until - now

        return True, 0.0

    def record_auth_failure(self, ip: str, account: Optional[str] = None):
        """
        Increments failure counter and applies exponential backoff: lock = backoff_factor ^ fails.
        """
        now = time.time()
        keys_to_update = [f"ip:{ip}"]
        if account:
            keys_to_update.append(f"acct:{account}")

        for k in keys_to_update:
            fails, _ = self.auth_backoff.get(k, (0, 0.0))
            new_fails = fails + 1
            delay = math.pow(RATE_LIMIT_BACKOFF_FACTOR, min(new_fails, 6))  # Cap backoff at ~64s
            self.auth_backoff[k] = (new_fails, now + delay)
            logger.warning(f"Auth failure recorded for {k}. Failed attempts: {new_fails}. Locked for {delay:.1f}s.")

    def record_auth_success(self, ip: str, account: Optional[str] = None):
        """
        Clears exponential backoff on successful login.
        """
        for k in [f"ip:{ip}", f"acct:{account}" if account else None]:
            if k and k in self.auth_backoff:
                del self.auth_backoff[k]


limiter = TieredRateLimiter()


class SecurityShieldMiddleware(BaseHTTPMiddleware):
    """
    Middleware applying:
    1. Tiered rate limiting based on path classification.
    2. Global Information Leakage Protection (masking raw stack traces & internal server paths).
    3. Secure HTTP Response Headers.
    """
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract client IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        path = request.url.path

        # 1. Tier: Authentication Routes (Strict)
        if path.startswith("/v1/auth"):
            allowed, backoff_remaining = limiter.check_auth_backoff(client_ip)
            if not allowed:
                logger.warning(f"Auth rate limit (backoff) exceeded for IP: {client_ip}. Retry in {backoff_remaining:.1f}s")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Too Many Failed Authentication Attempts",
                        "message": f"Exponential backoff in effect. Please retry in {int(backoff_remaining)} seconds.",
                        "retry_after": int(backoff_remaining),
                        "request_id": request_id
                    },
                    headers={"Retry-After": str(int(backoff_remaining))}
                )
            
            allowed, remaining, retry_after = limiter.check_rate_limit(f"auth:{client_ip}", RATE_LIMIT_AUTH_PER_MIN)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate Limit Exceeded on Auth Endpoint",
                        "message": f"Maximum of {RATE_LIMIT_AUTH_PER_MIN} attempts per minute reached.",
                        "retry_after": int(retry_after),
                        "request_id": request_id
                    },
                    headers={"Retry-After": str(int(retry_after))}
                )

        # 2. Tier: Heavy Synthesis & Computation Routes (Moderate)
        elif path.startswith("/v1/synth") or path.startswith("/v1/cluster"):
            allowed, remaining, retry_after = limiter.check_rate_limit(f"compute:{client_ip}", RATE_LIMIT_COMPUTE_PER_MIN)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Compute Resource Rate Limit Exceeded",
                        "message": f"Synthesis and validation limited to {RATE_LIMIT_COMPUTE_PER_MIN} requests per minute.",
                        "retry_after": int(retry_after),
                        "request_id": request_id
                    },
                    headers={"Retry-After": str(int(retry_after))}
                )

        # 3. Tier: Public & Informational Endpoints (Standard)
        elif path.startswith("/v1/"):
            allowed, remaining, retry_after = limiter.check_rate_limit(f"public:{client_ip}", RATE_LIMIT_PUBLIC_PER_MIN)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "API Rate Limit Exceeded",
                        "message": f"Public API limited to {RATE_LIMIT_PUBLIC_PER_MIN} requests per minute.",
                        "retry_after": int(retry_after),
                        "request_id": request_id
                    },
                    headers={"Retry-After": str(int(retry_after))}
                )

        # Process request through application with Information Leakage Shield
        try:
            response = await call_next(request)
            
            # Security Headers Injection
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["X-Request-ID"] = request_id
            return response

        except HTTPException as http_exc:
            # Re-raise standard HTTP exceptions
            raise http_exc
        except Exception as exc:
            # Internal error shielding: Log server-side full trace, return clean sanitized message to user
            logger.error(f"[SHIELD] Internal server exception on {request.method} {path} (Request ID: {request_id}): {str(exc)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred while processing your scientific request. Our systems have logged this event.",
                    "request_id": request_id
                },
                headers={"X-Request-ID": request_id}
            )
