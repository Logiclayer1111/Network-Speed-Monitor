"""
Unit tests for FastAPI endpoints
Run with: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from api.main import app
from db.db_manager import DatabaseManager

client = TestClient(app)

# Use a temporary in-memory database for testing
@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Replace database with in-memory instance for each test"""
    test_db = DatabaseManager(":memory:")
    monkeypatch.setattr("api.main.db", test_db)
    monkeypatch.setattr("db.db_manager.DatabaseManager", lambda *args, **kwargs: test_db)
    return test_db

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "samples_collected" in data

def test_daily_invalid_date():
    response = client.get("/api/daily/2025-99-99")
    assert response.status_code == 400
    assert "Invalid date format" in response.text

def test_daily_empty():
    response = client.get("/api/daily/2025-01-01")
    assert response.status_code == 200
    assert response.json() == []

def test_week():
    response = client.get("/api/week")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_worst_times():
    response = client.get("/api/worst-times?days=7&window_minutes=15")
    assert response.status_code == 200
    data = response.json()
    assert "worst_periods" in data
    assert isinstance(data["worst_periods"], list)

def test_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_samples" in data
    assert "avg_download" in data

def test_adapters():
    response = client.get("/api/adapters")
    assert response.status_code == 200
    data = response.json()
    assert "adapters" in data
    assert "selected_adapter" in data