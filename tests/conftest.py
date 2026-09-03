import os
import pytest


@pytest.fixture(autouse=True)
def isolate_test_database(monkeypatch):
    """Ensure test suite runs in isolated local SQLite databases and never mutates cloud Neon database."""
    monkeypatch.setenv("DATABASE_URL", "")
