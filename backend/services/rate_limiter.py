import hashlib
import time
from typing import Optional, Tuple
from fastapi import Request
from backend.storage import StorageService


class RateLimiter:
    """Database-backed atomic rate limiter with sliding window reset."""

    def __init__(self, storage: StorageService):
        self.storage = storage

    def check(
        self,
        bucket: str,
        subject: str,
        limit: int,
        window_seconds: int,
        now_epoch: Optional[float] = None,
    ) -> Tuple[bool, int, float]:
        """Atomically checks and increments rate limit counter.

        Returns:
            (allowed: bool, remaining: int, retry_after: float)
        """
        now = now_epoch if now_epoch is not None else time.time()
        with self.storage._get_cursor() as cursor:
            cursor.execute(
                self.storage._format_sql(
                    "SELECT count, reset_at FROM rate_limits WHERE bucket = ? AND subject = ?"
                ),
                (bucket, subject),
            )
            row = cursor.fetchone()
            if not row:
                reset_at = now + window_seconds
                cursor.execute(
                    self.storage._format_sql(
                        "INSERT INTO rate_limits (bucket, subject, count, reset_at) VALUES (?, ?, ?, ?)"
                    ),
                    (bucket, subject, 1, reset_at),
                )
                return True, max(0, limit - 1), 0.0

            r = dict(row)
            count = int(r["count"])
            reset_at = float(r["reset_at"])

            if now >= reset_at:
                new_reset_at = now + window_seconds
                cursor.execute(
                    self.storage._format_sql(
                        "UPDATE rate_limits SET count = 1, reset_at = ? WHERE bucket = ? AND subject = ?"
                    ),
                    (new_reset_at, bucket, subject),
                )
                return True, max(0, limit - 1), 0.0

            if count < limit:
                new_count = count + 1
                cursor.execute(
                    self.storage._format_sql(
                        "UPDATE rate_limits SET count = ?, reset_at = ? WHERE bucket = ? AND subject = ?"
                    ),
                    (new_count, reset_at, bucket, subject),
                )
                return True, max(0, limit - new_count), 0.0
            else:
                retry_after = max(1.0, reset_at - now)
                return False, 0, retry_after

    def cleanup_expired(self, now_epoch: Optional[float] = None) -> int:
        """Removes expired rate limit records."""
        now = now_epoch if now_epoch is not None else time.time()
        with self.storage._get_cursor() as cursor:
            cursor.execute(
                self.storage._format_sql("DELETE FROM rate_limits WHERE reset_at < ?"),
                (now,),
            )
            return cursor.rowcount if hasattr(cursor, "rowcount") else 0


def get_client_ip(request: Request, trust_proxy_headers: bool = False) -> str:
    """Returns the remote client IP safely."""
    if trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def get_email_hash(email: str) -> str:
    """Computes SHA-256 hash of normalized email for rate limits."""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
