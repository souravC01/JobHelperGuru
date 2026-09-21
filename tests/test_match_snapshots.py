"""Tests for matching snapshot persistence, tenant isolation, and cache invalidation."""

from __future__ import annotations

import json

from backend.services.resume_files import ResumeFileManager
from backend.storage import StorageService


def test_snapshot_crud_and_tenant_isolation(tmp_path):
    db_path = str(tmp_path / "test_snapshots.db")
    storage = StorageService(db_path=db_path)

    # Save a snapshot for user-1
    storage.save_matching_snapshot(
        id="snap-1",
        user_id="user-1",
        resume_id="res-1",
        job_hash="job-hash-1",
        source_hash="source-hash-1",
        version_key="vkey-1",
        as_of="2026-09-17",
        payload_json=json.dumps({"match_score": 85}),
    )

    # Retrieve snapshot as user-1 -> hit
    snap = storage.get_matching_snapshot(
        user_id="user-1",
        resume_id="res-1",
        job_hash="job-hash-1",
        version_key="vkey-1",
        as_of="2026-09-17",
    )
    assert snap is not None
    assert snap["id"] == "snap-1"
    assert json.loads(snap["payload_json"])["match_score"] == 85

    # Cross-tenant isolation: user-2 cannot access user-1's snapshot
    cross_tenant = storage.get_matching_snapshot(
        user_id="user-2",
        resume_id="res-1",
        job_hash="job-hash-1",
        version_key="vkey-1",
        as_of="2026-09-17",
    )
    assert cross_tenant is None

    # Cache miss on altered inputs
    assert storage.get_matching_snapshot(
        user_id="user-1",
        resume_id="res-1",
        job_hash="job-hash-different",
        version_key="vkey-1",
        as_of="2026-09-17",
    ) is None

    assert storage.get_matching_snapshot(
        user_id="user-1",
        resume_id="res-1",
        job_hash="job-hash-1",
        version_key="vkey-different",
        as_of="2026-09-17",
    ) is None

    assert storage.get_matching_snapshot(
        user_id="user-1",
        resume_id="res-1",
        job_hash="job-hash-1",
        version_key="vkey-1",
        as_of="2026-10-01",
    ) is None


def test_resume_deletion_cascades_to_snapshots(tmp_path):
    db_path = str(tmp_path / "test_cascade.db")
    storage = StorageService(db_path=db_path)

    resume = storage.add_resume(
        name="Backend Resume",
        content="Python developer",
        user_id="user-1",
    )

    storage.save_matching_snapshot(
        id="snap-cascade-1",
        user_id="user-1",
        resume_id=resume.id,
        job_hash="job-hash",
        source_hash="source-hash",
        version_key="vkey",
        as_of="2026-09-17",
        payload_json=json.dumps({"match_score": 90}),
    )

    # Verify snapshot exists
    assert storage.get_matching_snapshot(
        user_id="user-1",
        resume_id=resume.id,
        job_hash="job-hash",
        version_key="vkey",
        as_of="2026-09-17",
    ) is not None

    # Delete resume via storage
    storage.delete_resume(resume.id, user_id="user-1")

    # Snapshot should be gone
    assert storage.get_matching_snapshot(
        user_id="user-1",
        resume_id=resume.id,
        job_hash="job-hash",
        version_key="vkey",
        as_of="2026-09-17",
    ) is None


def test_resume_file_manager_deletion_cleans_snapshots(tmp_path):
    from backend.services.object_storage import ObjectStorageService
    db_path = str(tmp_path / "test_rfm_cascade.db")
    storage = StorageService(db_path=db_path)
    obj_storage = ObjectStorageService(endpoint_url=None)
    rfm = ResumeFileManager(storage, obj_storage)


    resume = storage.add_resume(
        name="Engineer Resume",
        content="Distributed systems engineer",
        user_id="user-2",
    )

    storage.save_matching_snapshot(
        id="snap-rfm-1",
        user_id="user-2",
        resume_id=resume.id,
        job_hash="job-hash-2",
        source_hash="source-hash-2",
        version_key="vkey-2",
        as_of="2026-09-17",
        payload_json=json.dumps({"match_score": 75}),
    )

    # Delete via ResumeFileManager
    deleted = rfm.delete_resume(user_id="user-2", resume_id=resume.id)
    assert deleted is True

    # Snapshot deleted
    assert storage.get_matching_snapshot(
        user_id="user-2",
        resume_id=resume.id,
        job_hash="job-hash-2",
        version_key="vkey-2",
        as_of="2026-09-17",
    ) is None
