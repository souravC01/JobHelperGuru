import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app, storage
from backend.models import JobAnalysisResult


def test_upload_resume_with_content_override_persists_edited_text(client):
    # 1. Register a user
    res = client.post(
        "/api/auth/register",
        json={"email": "resumetest@example.test", "password": "Password123!", "name": "Resume Editor"},
    )
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. File with initial content
    initial_text = "Software Engineer with generic experience."
    file_bytes = io.BytesIO(initial_text.encode("utf-8"))

    # User edited text in the UI before submitting
    edited_text = "Senior Distributed Systems Engineer. Expert in Python, FastAPI, Docker, and Kubernetes."

    response = client.post(
        "/api/resumes/upload",
        headers=headers,
        data={"name": "My Tailored Resume", "content_override": edited_text},
        files={"file": ("resume.txt", file_bytes, "text/plain")},
    )
    assert response.status_code == 200, response.text
    created = response.json()
    assert created["content"] == edited_text
    assert created["name"] == "My Tailored Resume"
    resume_id = created["id"]

    # 3. Reload from server
    resumes = client.get("/api/resumes", headers=headers).json()
    matching = [r for r in resumes if r["id"] == resume_id]
    assert len(matching) == 1
    assert matching[0]["content"] == edited_text

    # 4. Verify ATS matching consumes edited text, not raw initial file text
    job_payload = {
        "job": {
            "title": "Distributed Systems Engineer",
            "company": "Tech Corp",
            "required_skills": ["Kubernetes", "FastAPI"],
            "raw_text": "Need engineer with Kubernetes and FastAPI experience",
        }
    }
    match_res = client.post("/api/resumes/match", headers=headers, json=job_payload)
    assert match_res.status_code == 200
    ranked = match_res.json()
    assert len(ranked) >= 1
    # Edited text contains Kubernetes and FastAPI, so match score should reflect it
    assert ranked[0]["resume_id"] == resume_id
    assert "Kubernetes" in ranked[0]["matched_keywords"]


def test_upload_resume_without_content_override_uses_extracted_text(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "resumedefault@example.test", "password": "Password123!", "name": "Resume Default"},
    )
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    original_text = "Full Stack Developer specializing in React and PostgreSQL."
    file_bytes = io.BytesIO(original_text.encode("utf-8"))

    response = client.post(
        "/api/resumes/upload",
        headers=headers,
        data={"name": "Auto Extracted Resume"},
        files={"file": ("extracted.txt", file_bytes, "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["content"] == original_text


def test_rtf_parsing_extracts_clean_text_without_rtf_control_codes(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "rtfuser@example.test", "password": "Password123!", "name": "RTF User"},
    )
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    rtf_content = (
        r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\f0\fs24 "
        r"{\info{\author Test Author}}"
        r"\b Jane Doe\b0\par "
        r"Staff Software Architect with extensive Python and AWS experience.\par "
        r"}"
    )
    file_bytes = io.BytesIO(rtf_content.encode("utf-8"))

    parse_res = client.post(
        "/api/resumes/parse-file",
        headers=headers,
        files={"file": ("sample.rtf", file_bytes, "application/rtf")},
    )
    assert parse_res.status_code == 200, parse_res.text
    parsed_text = parse_res.json()["text"]

    # Verify control codes are stripped
    assert r"\rtf" not in parsed_text
    assert r"\fonttbl" not in parsed_text
    assert r"\fs24" not in parsed_text
    assert "Jane Doe" in parsed_text
    assert "Staff Software Architect" in parsed_text


def test_markdown_file_supported_in_upload_and_parse(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "mduser@example.test", "password": "Password123!", "name": "MD User"},
    )
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    md_content = "# John Developer\n\n- Skill: Python\n- Skill: Go\n- Experience: 5 years"
    file_bytes = io.BytesIO(md_content.encode("utf-8"))

    parse_res = client.post(
        "/api/resumes/parse-file",
        headers=headers,
        files={"file": ("resume.md", file_bytes, "text/markdown")},
    )
    assert parse_res.status_code == 200
    assert "John Developer" in parse_res.json()["text"]


def test_legacy_doc_binary_rejected_with_clear_message(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "docuser@example.test", "password": "Password123!", "name": "Doc User"},
    )
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Binary junk simulating corrupt or legacy binary OLE doc
    binary_junk = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 100 + b"BinaryWordDocumentJunk"

    parse_res = client.post(
        "/api/resumes/parse-file",
        headers=headers,
        files={"file": ("legacy.doc", io.BytesIO(binary_junk), "application/msword")},
    )
    assert parse_res.status_code == 422
    assert "docx" in parse_res.text.lower() or "pdf" in parse_res.text.lower()


def test_upload_content_override_too_long_rejected(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "longcontent@example.test", "password": "Password123!", "name": "Long Content"},
    )
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    huge_override = "a" * 100_001
    response = client.post(
        "/api/resumes/upload",
        headers=headers,
        data={"name": "Too Long", "content_override": huge_override},
        files={"file": ("resume.txt", io.BytesIO(b"Small content"), "text/plain")},
    )
    assert response.status_code == 422
    assert "100,000" in response.text
