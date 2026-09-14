from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock

import pytest

from backend import main
from backend.services.rate_limiter import RateLimiter


@pytest.mark.parametrize('seed', [0, 1])
def test_concurrent_requests_obey_exact_budget(seed):
    limiter = RateLimiter(main.storage)
    if seed:
        limiter.check('race', 'user', 3, 60)
    start = Barrier(12)
    def check(_):
        start.wait()
        return limiter.check('race', 'user', 3, 60)[0]
    with ThreadPoolExecutor(max_workers=12) as workers:
        assert sum(workers.map(check, range(12))) == 3 - seed


def test_authenticated_analysis_exhaustion_never_calls_scraper(client, monkeypatch):
    user = main.storage.create_user('budget@example.test', None, 'Budget', email_verified=True)
    main.app.dependency_overrides[main.get_optional_user] = lambda: user
    scrape = Mock()
    monkeypatch.setattr("backend.services.scraper.ScraperService.scrape_url", scrape)
    try:
        for _ in range(30):
            RateLimiter(main.storage).check('user_ai_ops', user.id, 30, 60)
        response = client.post('/api/analyze/job', json={'url': 'https://example.test/job'})
        assert response.status_code == 429
        assert int(response.headers['retry-after']) >= 1
        scrape.assert_not_called()
    finally:
        main.app.dependency_overrides.pop(main.get_optional_user, None)


def test_google_exhaustion_never_calls_verifier(client, monkeypatch):
    from backend.routers import auth
    verify = Mock(side_effect=ValueError('synthetic invalid token'))
    monkeypatch.setattr(auth, 'verify_google_id_token', verify)
    for _ in range(10):
        assert client.post('/api/auth/google', json={'credential': 'synthetic'}).status_code == 401
    verify.reset_mock()
    response = client.post('/api/auth/google', json={'credential': 'synthetic'})
    assert response.status_code == 429
    assert int(response.headers['retry-after']) >= 1
    verify.assert_not_called()


def test_concurrent_uploads_cannot_exceed_storage_quota():
    from backend.services.resume_files import ResumeFileManager
    from backend.services.object_storage import ObjectStorageService

    user = main.storage.create_user("quota_race@example.test", None, "Quota Race", email_verified=True)
    obj_storage = ObjectStorageService(endpoint_url=None)
    manager = ResumeFileManager(main.storage, obj_storage)

    max_quota = 100
    file_bytes = b"A" * 70
    start = Barrier(2)

    def upload_task(idx):
        start.wait()
        try:
            resume = manager.reserve_and_upload(
                user_id=user.id,
                filename=f"resume_{idx}.txt",
                content_type="text/plain",
                content_bytes=file_bytes,
                resume_name=f"Resume {idx}",
                text_content=f"Content {idx}",
                max_storage_bytes=max_quota,
            )
            return ("success", resume)
        except Exception as e:
            return ("error", str(e))

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(upload_task, range(2)))

    successes = [r for r in results if r[0] == "success"]
    errors = [r for r in results if r[0] == "error"]

    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {results}"
    assert len(errors) == 1, f"Expected exactly 1 error, got {len(errors)}: {results}"
    assert "storage limit" in errors[0][1].lower()

    total_bytes = main.storage.get_user_upload_bytes(user.id)
    assert total_bytes == 70
    assert total_bytes <= max_quota


def test_concurrent_password_reset_confirm_only_succeeds_once(client):
    import secrets
    import hashlib
    from datetime import datetime, timezone, timedelta

    user = main.storage.create_user("reset_race@example.test", "OldPassword1!", "Reset Race", email_verified=True)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    main.storage.create_auth_token(user.id, token_hash, "reset_password", expires_at)

    start = Barrier(2)

    def confirm_task(idx):
        start.wait()
        res = client.post(
            "/api/auth/password-reset/confirm",
            json={"token": raw_token, "new_password": f"NewPassword{idx}!"},
        )
        return res.status_code, res.json()

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(confirm_task, range(2)))

    status_codes = [r[0] for r in results]
    assert status_codes.count(200) == 1, f"Expected exactly one 200, got {results}"
    assert status_codes.count(400) == 1, f"Expected exactly one 400, got {results}"
    error_res = next(r[1] for r in results if r[0] == 400)
    assert "invalid or expired" in error_res["detail"].lower()
