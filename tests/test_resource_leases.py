import pytest
from fastapi import HTTPException
from backend import main
from backend.services.resource_leases import ResourceLeases


def test_resource_lease_lifecycle():
    leases = ResourceLeases(main.storage)
    lease_id = leases.acquire(user_id="user_1", kind="test_op", ttl_seconds=60)
    assert lease_id is not None
    leases.release(lease_id)

    # Releasing an empty or already released lease is safe and idempotent
    leases.release(lease_id)
    leases.release("")


def test_user_concurrency_limit():
    leases = ResourceLeases(main.storage)
    lease1 = leases.acquire(user_id="user_concurrent", kind="test_op", ttl_seconds=60, max_user_leases=2)
    lease2 = leases.acquire(user_id="user_concurrent", kind="test_op", ttl_seconds=60, max_user_leases=2)

    with pytest.raises(HTTPException) as exc_info:
        leases.acquire(user_id="user_concurrent", kind="test_op", ttl_seconds=60, max_user_leases=2)

    assert exc_info.value.status_code == 429
    assert "Too many concurrent" in exc_info.value.detail
    assert exc_info.value.headers.get("Retry-After") == "5"

    leases.release(lease1)
    leases.release(lease2)


def test_global_concurrency_limit():
    leases = ResourceLeases(main.storage)
    active = []
    try:
        for i in range(5):
            lid = leases.acquire(user_id=f"user_{i}", kind="global_op", ttl_seconds=60, max_global_leases=5)
            active.append(lid)

        with pytest.raises(HTTPException) as exc_info:
            leases.acquire(user_id="another_user", kind="global_op", ttl_seconds=60, max_global_leases=5)

        assert exc_info.value.status_code == 429
        assert "Global concurrency capacity reached" in exc_info.value.detail
    finally:
        for lid in active:
            leases.release(lid)


def test_expired_leases_are_cleaned_up():
    leases = ResourceLeases(main.storage)
    # Acquire with past timestamp (expired)
    lid = leases.acquire(
        user_id="user_expired",
        kind="test_op",
        ttl_seconds=10,
        now_epoch=1000.0,
        max_user_leases=1,
    )

    # At t=1020.0, the lease is expired. New acquisition at t=1020.0 must succeed.
    lid2 = leases.acquire(
        user_id="user_expired",
        kind="test_op",
        ttl_seconds=10,
        now_epoch=1020.0,
        max_user_leases=1,
    )
    assert lid2 is not None
    leases.release(lid2)
