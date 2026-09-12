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
