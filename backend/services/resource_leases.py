import time
import uuid
from typing import Optional
from fastapi import HTTPException
from backend.storage import StorageService


class ResourceLeases:
    """Manages expiring in-flight operation leases across workers to bound concurrency."""

    def __init__(self, storage: StorageService):
        self.storage = storage

    def acquire(
        self,
        user_id: str,
        kind: str,
        ttl_seconds: int = 30,
        max_user_leases: int = 2,
        max_global_leases: int = 8,
        now_epoch: Optional[float] = None,
    ) -> str:
        """Acquires a resource lease. Raises HTTPException(429) if capacity is exhausted."""
        now = now_epoch if now_epoch is not None else time.time()
        expires_at = now + ttl_seconds

        # Clean expired leases before checking
        self.cleanup_expired(now)

        with self.storage._get_immediate_cursor() as cursor:
            # Check user active leases
            cursor.execute(
                self.storage._format_sql(
                    "SELECT COUNT(*) as count FROM resource_leases WHERE user_id = ? AND expires_at > ?"
                ),
                (user_id, now),
            )
            row = cursor.fetchone()
            user_count = int(row["count"]) if row else 0
            if user_count >= max_user_leases:
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many concurrent {kind} operations for this user. Please wait for in-flight tasks to complete.",
                    headers={"Retry-After": "5"},
                )

            # Check global active leases
            cursor.execute(
                self.storage._format_sql(
                    "SELECT COUNT(*) as count FROM resource_leases WHERE kind = ? AND expires_at > ?"
                ),
                (kind, now),
            )
            row = cursor.fetchone()
            global_count = int(row["count"]) if row else 0
            if global_count >= max_global_leases:
                raise HTTPException(
                    status_code=429,
                    detail=f"Global concurrency capacity reached for {kind}. Please retry shortly.",
                    headers={"Retry-After": "5"},
                )

            lease_id = str(uuid.uuid4())
            cursor.execute(
                self.storage._format_sql(
                    "INSERT INTO resource_leases (lease_id, user_id, kind, expires_at) VALUES (?, ?, ?, ?)"
                ),
                (lease_id, user_id, kind, expires_at),
            )
            return lease_id

    def release(self, lease_id: str) -> None:
        """Releases an active lease."""
        if not lease_id:
            return
        with self.storage._get_immediate_cursor() as cursor:
            cursor.execute(
                self.storage._format_sql("DELETE FROM resource_leases WHERE lease_id = ?"),
                (lease_id,),
            )

    def cleanup_expired(self, now_epoch: Optional[float] = None) -> int:
        """Purges expired leases from storage."""
        now = now_epoch if now_epoch is not None else time.time()
        with self.storage._get_immediate_cursor() as cursor:
            cursor.execute(
                self.storage._format_sql("DELETE FROM resource_leases WHERE expires_at <= ?"),
                (now,),
            )
            return cursor.rowcount if hasattr(cursor, "rowcount") else 0
