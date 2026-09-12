import pytest
from starlette.testclient import TestClient
from backend.main import app, SPAStaticFiles
from pathlib import Path


def test_spa_fallback_serves_index_for_deep_links(tmp_path):
    # Create fake dist directory with index.html and an asset
    dist = tmp_path / "dist"
    dist.mkdir()
    index_file = dist / "index.html"
    index_file.write_text("<!DOCTYPE html><html><body><div id='root'>SPA Root</div></body></html>", encoding="utf-8")
    asset_file = dist / "style.css"
    asset_file.write_text("body { color: red; }", encoding="utf-8")

    from fastapi import FastAPI
    test_app = FastAPI()

    @test_app.get("/api/data")
    def get_data():
        return {"ok": True}

    test_app.mount("/", SPAStaticFiles(directory=str(dist), html=True), name="frontend")
    client = TestClient(test_app)

    # Direct asset returns asset
    assert client.get("/style.css").status_code == 200
    assert client.get("/style.css").text == "body { color: red; }"

    # Root returns index.html
    assert client.get("/").status_code == 200
    assert "SPA Root" in client.get("/").text

    # Deep links return index.html
    resp_verify = client.get("/verify-email?token=abc123xyz")
    assert resp_verify.status_code == 200
    assert "SPA Root" in resp_verify.text

    resp_reset = client.get("/reset-password?token=def456uvw")
    assert resp_reset.status_code == 200
    assert "SPA Root" in resp_reset.text

    # API 404 does not return index.html
    resp_api = client.get("/api/not-found")
    assert resp_api.status_code == 404
