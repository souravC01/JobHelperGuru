from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import Mock
import json

import pytest
from backend.storage import StorageService
from tests.test_match_pipeline import Provider, JOB, run
from backend.services.matching.provenance import source_hash


def rubric():
    from backend.services.matching.extraction import extract_requirements
    import time
    return extract_requirements(JOB,engine=Provider(),deadline=time.monotonic()+30).model_dump_json()


def test_sqlite_schema_reopens_and_first_rubric_wins(tmp_path):
    path=str(tmp_path/"s.db"); s=StorageService(path,force_sqlite=True)
    payload=rubric()
    def save(id): s.save_matching_rubric(id=id,user_id="u",job_hash=source_hash(JOB),version_key="v",payload_json=payload)
    with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(save,["first","second"]))
    winner=s.get_matching_rubric(user_id="u",job_hash=source_hash(JOB),version_key="v")
    assert winner["id"] in {"first","second"}
    save("last"); assert s.get_matching_rubric(user_id="u",job_hash=source_hash(JOB),version_key="v")==winner
    assert s.get_matching_rubric(user_id="other",job_hash=source_hash(JOB),version_key="v") is None
    s.close(); s=StorageService(path,force_sqlite=True)
    assert s.get_matching_rubric(user_id="u",job_hash=source_hash(JOB),version_key="v")==winner
    s.close()


def test_storage_rejects_incomplete_rubric(tmp_path):
    s=StorageService(str(tmp_path/"s.db"),force_sqlite=True)
    data=json.loads(rubric()); data["status"]="needs_review"
    with pytest.raises(ValueError):
        s.save_matching_rubric(id="r",user_id="u",job_hash=source_hash(JOB),version_key="v",payload_json=json.dumps(data))
    s.close()


def test_postgres_schema_and_tenant_crud():
    s=object.__new__(StorageService); s.is_postgres=True; c=Mock()
    @contextmanager
    def db(): yield c
    s._get_cursor=db; s._get_immediate_cursor=db
    s._init_db()
    sql="\n".join(call.args[0] for call in c.execute.call_args_list)
    assert "CREATE TABLE IF NOT EXISTS matching_rubrics" in sql and "CREATE TABLE IF NOT EXISTS matching_snapshots" in sql
    s.save_matching_rubric(id="r",user_id="u",job_hash=source_hash(JOB),version_key="v",payload_json=rubric())
    assert "ON CONFLICT" in c.execute.call_args.args[0] and "DO NOTHING" in c.execute.call_args.args[0]
    c.fetchone.return_value={"payload_json":"{}"}
    s.get_matching_rubric(user_id="u",job_hash="h",version_key="v")
    assert c.execute.call_args.args[1]==("u","h","v")
    s.get_matching_snapshot(user_id="u",resume_id="r",job_hash="h",version_key="v",as_of="2026-09-30")
    assert c.execute.call_args.args[1]==("u","r","h","v","2026-09-30")
    s.delete_matching_snapshots_for_resume("r",user_id="u")
    assert c.execute.call_args.args[1]==("r","u")


def test_rubric_removal_invalidates_dependent_snapshots(tmp_path):
    s=StorageService(str(tmp_path/"s.db"),force_sqlite=True)
    r=s.add_resume("R","Projects:\nCut outages by deploying redundant workers.",user_id="u")
    run(s,[r],Provider())
    with s._get_cursor() as c:
        c.execute("SELECT * FROM matching_rubrics"); row=dict(c.fetchone())
    s.delete_matching_rubric(user_id="u",job_hash=row["job_hash"],version_key=row["version_key"],payload_json="different")
    with s._get_cursor() as c:
        c.execute("SELECT COUNT(*) FROM matching_snapshots"); assert c.fetchone()[0]==1
    s.delete_matching_rubric(user_id="u",job_hash=row["job_hash"],version_key=row["version_key"],payload_json=row["payload_json"])
    with s._get_cursor() as c:
        c.execute("SELECT COUNT(*) FROM matching_snapshots"); assert c.fetchone()[0]==0
    s.close()


def test_snapshot_source_lock_and_postgres_upsert(tmp_path):
    s=StorageService(str(tmp_path/"s.db"),force_sqlite=True)
    r=s.add_resume("R","Projects:\nCut outages by deploying redundant workers.",user_id="u")
    run(s,[r],Provider())
    with s._get_cursor() as c:
        c.execute("SELECT * FROM matching_snapshots"); row=dict(c.fetchone())
    kwargs={key:row[key] for key in ["id","user_id","resume_id","job_hash","source_hash","version_key","as_of","payload_json"]}
    pg=object.__new__(StorageService); pg.is_postgres=True; c=Mock()
    @contextmanager
    def db(): yield c
    pg._get_immediate_cursor=db
    c.fetchone.side_effect=[{"content":r.content,"extraction_warnings":"[]"},{"id":"rubric"},{"resume_id":r.id}]
    pg.save_matching_snapshot(**kwargs)
    queries=[call.args[0] for call in c.execute.call_args_list]
    assert "FOR UPDATE" in queries[0] and "FOR UPDATE" in queries[1]
    assert "ON CONFLICT (id) DO UPDATE" in queries[-1] and "%s" in queries[-1]
    s.update_resume(r.id,content="Changed",user_id="u")
    with pytest.raises(ValueError): s.save_matching_snapshot(**kwargs)
    with s._get_cursor() as c:
        c.execute("SELECT COUNT(*) FROM matching_snapshots"); assert c.fetchone()[0]==0
    s.close()


def test_existing_source_snapshot_schema_is_migrated_without_deleting_data(tmp_path):
    import sqlite3
    path=str(tmp_path/"legacy.db")
    with sqlite3.connect(path) as c:
        c.execute("""CREATE TABLE matching_snapshots (id TEXT PRIMARY KEY,user_id TEXT NOT NULL,
            resume_id TEXT NOT NULL,job_hash TEXT NOT NULL,source_hash TEXT NOT NULL,
            version_key TEXT NOT NULL,as_of TEXT NOT NULL,payload_json TEXT NOT NULL,created_at TEXT NOT NULL)""")
        c.execute("INSERT INTO matching_snapshots VALUES (?,?,?,?,?,?,?,?,?)",("old","u","r","j","h","v","2026-09-30","{}","today"))
    s=StorageService(path,force_sqlite=True)
    with s._get_cursor() as c:
        c.execute("SELECT id,rubric_fingerprint FROM matching_snapshots")
        assert tuple(c.fetchone())==("old","")
    s.close()
