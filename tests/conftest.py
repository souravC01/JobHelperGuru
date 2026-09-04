import os
import pytest

# Ensure test suite runs in isolated local SQLite databases and never mutates cloud Neon database
os.environ["DATABASE_URL"] = ""


@pytest.fixture(autouse=True)
def isolate_test_database(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
