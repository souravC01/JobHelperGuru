import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app, storage
from backend.services.rate_limiter import RateLimiter


def test_rate_limiter_exact_limit_and_window_expiry():
    limiter = RateLimiter(storage)
    bucket = "test_bucket"
    subject = "user_123"
    fake_clock = 1000.0

    # Limit of 3 requests per 60 seconds
    for i in range(3):
        allowed, remaining, retry_after = limiter.check(
            bucket=bucket,
            subject=subject,
            limit=3,
            window_seconds=60,
            now_epoch=fake_clock,
        )
        assert allowed is True
        assert remaining == 2 - i
        assert retry_after == 0.0

    # 4th request must be rejected
    allowed, remaining, retry_after = limiter.check(
        bucket=bucket,
        subject=subject,
        limit=3,
        window_seconds=60,
        now_epoch=fake_clock,
    )
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0.0

    # Advance clock past window
    fake_clock += 65.0
    allowed, remaining, retry_after = limiter.check(
        bucket=bucket,
        subject=subject,
        limit=3,
        window_seconds=60,
        now_epoch=fake_clock,
    )
    assert allowed is True
    assert remaining == 2
    assert retry_after == 0.0


def test_rate_limiter_subject_and_bucket_separation():
    limiter = RateLimiter(storage)
    fake_clock = 5000.0

    # Max out user_alpha
    for _ in range(2):
        limiter.check("action", "user_alpha", limit=2, window_seconds=60, now_epoch=fake_clock)

    allowed_alpha, _, _ = limiter.check("action", "user_alpha", limit=2, window_seconds=60, now_epoch=fake_clock)
    assert allowed_alpha is False

    # user_beta is unaffected
    allowed_beta, remaining, _ = limiter.check("action", "user_beta", limit=2, window_seconds=60, now_epoch=fake_clock)
    assert allowed_beta is True
    assert remaining == 1

    # Different bucket for user_alpha is unaffected
    allowed_diff_bucket, _, _ = limiter.check("different_action", "user_alpha", limit=2, window_seconds=60, now_epoch=fake_clock)
    assert allowed_diff_bucket is True


def test_login_rate_limiting_http_429(client):
    email = "ratelimit_login@example.test"
    password = "Password123!"

    # Exceed login attempts (limit 10/min)
    responses = []
    for _ in range(12):
        res = client.post("/api/auth/login", json={"email": email, "password": password})
        responses.append(res)

    # 11th and 12th should be 429
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes
    rate_limited_res = [r for r in responses if r.status_code == 429][0]
    assert "Retry-After" in rate_limited_res.headers or "retry-after" in rate_limited_res.headers


def test_anonymous_job_analysis_rate_limiting_http_429(client):
    responses = []
    # Send 12 requests without authorization header
    for _ in range(12):
        res = client.post(
            "/api/analyze/job",
            json={"raw_text": "Software engineer job description requiring Python and SQL."},
        )
        responses.append(res)

    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes


def test_json_body_size_limit_rejects_payload_too_large(client):
    # Payload exceeding 1 MB (1 * 1024 * 1024 + 100 bytes)
    huge_text = "x" * (1024 * 1024 + 200)
    res = client.post(
        "/api/analyze/job",
        json={"raw_text": huge_text},
    )
    assert res.status_code == 413


def test_resume_count_limit_per_user(client):
    # Register a user
    res = client.post("/api/auth/register", json={"email": "resumelimit@example.test", "password": "Password123!", "name": "Resume Limiter"})
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add 30 resumes
    for i in range(30):
        r = client.post(
            "/api/resumes",
            headers=headers,
            json={"name": f"Resume {i}", "content": f"Resume content {i}"},
        )
        assert r.status_code == 200

    # 31st resume must be rejected with 422
    r_overflow = client.post(
        "/api/resumes",
        headers=headers,
        json={"name": "Overflow Resume", "content": "Overflow content"},
    )
    assert r_overflow.status_code == 422
    assert "limit" in r_overflow.text.lower()


def test_ai_operations_rate_limiting_http_429(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "aiops@example.test", "password": "Password123!", "name": "AI Ops Tester"},
    )
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    responses = []
    # Send 32 requests (limit is 30/min)
    for _ in range(32):
        r = client.post(
            "/api/resumes/optimize-bullet",
            headers=headers,
            json={
                "target_job_title": "Software Engineer",
                "existing_bullet": "Developed software in Python",
                "target_keywords": ["FastAPI"],
            },
        )
        responses.append(r)

    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes
    r_429 = [r for r in responses if r.status_code == 429][0]
    assert "Retry-After" in r_429.headers or "retry-after" in r_429.headers


def test_document_parser_pdf_page_limit():
    import io
    import pypdf
    from backend.services.document_parser import extract_text_from_file

    writer = pypdf.PdfWriter()
    for _ in range(101):
        writer.add_blank_page(width=100, height=100)
    bio = io.BytesIO()
    writer.write(bio)
    pdf_bytes = bio.getvalue()

    with pytest.raises(ValueError, match="100 pages"):
        extract_text_from_file(pdf_bytes, "too_long.pdf")


def test_document_parser_text_length_limit():
    from backend.services.document_parser import extract_text_from_file

    huge_text = "a" * 100_001
    with pytest.raises(ValueError, match="100,000"):
        extract_text_from_file(huge_text.encode("utf-8"), "huge.txt")


def test_document_parser_docx_decompressed_limit():
    import io
    import zipfile
    from backend.services.document_parser import extract_text_from_file

    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", b"0" * (51 * 1024 * 1024))
    bio.seek(0)
    docx_bytes = bio.getvalue()

    with pytest.raises(ValueError, match="50 MB"):
        extract_text_from_file(docx_bytes, "bomb.docx")


def test_rate_limiter_cleanup_expired():
    limiter = RateLimiter(storage)
    fake_now = 2000.0
    limiter.check("bucket_cleanup", "sub1", limit=1, window_seconds=10, now_epoch=fake_now)
    cleaned = limiter.cleanup_expired(now_epoch=fake_now + 20.0)
    assert cleaned >= 1
