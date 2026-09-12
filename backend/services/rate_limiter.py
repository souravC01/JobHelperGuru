import hashlib
import random
import threading
import time
from typing import Optional, Tuple
from fastapi import Request
from backend.storage import StorageService


class RateLimiter:
    """Database-backed atomic rate limiter with sliding window reset."""
    _lock = threading.Lock()

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

        # Probabilistic cleanup of expired rate limit entries (approx 1 in 50 checks)
        # to prevent unbounded storage growth in the database
        if random.random() < 0.02:
            try:
                self.cleanup_expired(now)
            except Exception:
                pass

        with self._lock:
            if self.storage.is_postgres:
                with self.storage._get_cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO rate_limits (bucket, subject, count, reset_at)
                        VALUES (%s, %s, 0, %s)
                        ON CONFLICT (bucket, subject) DO NOTHING
                        """,
                        (bucket, subject, now + window_seconds),
                    )
                    cursor.execute(
                        "SELECT count, reset_at FROM rate_limits WHERE bucket = %s AND subject = %s FOR UPDATE",
                        (bucket, subject),
                    )
                    row = cursor.fetchone()
                    r = dict(row)
                    count = int(r["count"])
                    reset_at = float(r["reset_at"])

                    if count == 0 or now >= reset_at:
                        new_reset_at = now + window_seconds
                        cursor.execute(
                            "UPDATE rate_limits SET count = 1, reset_at = %s WHERE bucket = %s AND subject = %s",
                            (new_reset_at, bucket, subject),
                        )
                        return True, max(0, limit - 1), 0.0

                    if count < limit:
                        new_count = count + 1
                        cursor.execute(
                            "UPDATE rate_limits SET count = %s WHERE bucket = %s AND subject = %s",
                            (new_count, bucket, subject),
                        )
                        return True, max(0, limit - new_count), 0.0
                    else:
                        retry_after = max(1.0, reset_at - now)
                        return False, 0, retry_after
            else:
                with self.storage._get_immediate_cursor() as cursor:
                    cursor.execute(
                        "SELECT count, reset_at FROM rate_limits WHERE bucket = ? AND subject = ?",
                        (bucket, subject),
                    )
                    row = cursor.fetchone()
                    if not row:
                        reset_at = now + window_seconds
                        cursor.execute(
                            "INSERT INTO rate_limits (bucket, subject, count, reset_at) VALUES (?, ?, 1, ?)",
                            (bucket, subject, reset_at),
                        )
                        return True, max(0, limit - 1), 0.0

                    r = dict(row)
                    count = int(r["count"])
                    reset_at = float(r["reset_at"])

                    if now >= reset_at:
                        new_reset_at = now + window_seconds
                        cursor.execute(
                            "UPDATE rate_limits SET count = 1, reset_at = ? WHERE bucket = ? AND subject = ?",
                            (new_reset_at, bucket, subject),
                        )
                        return True, max(0, limit - 1), 0.0

                    if count < limit:
                        new_count = count + 1
                        cursor.execute(
                            "UPDATE rate_limits SET count = ?, reset_at = ? WHERE bucket = ? AND subject = ?",
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
        render_client_ip = request.headers.get("render-proxy-client-ip")
        if render_client_ip and render_client_ip.strip():
            return render_client_ip.strip()
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            first_ip = forwarded.split(",")[0].strip()
            if first_ip:
                return first_ip
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def get_email_hash(email: str) -> str:
    """Computes SHA-256 hash of normalized email for rate limits."""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
