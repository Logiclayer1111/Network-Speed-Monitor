"""
End-to-end integration test: starts poller and API, inserts data, verifies dashboard.
Requires running services or will start them in subprocess.
"""

import pytest
import subprocess
import time
import requests
import sqlite3
import os
import signal
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000/api"
POLLER_SCRIPT = Path(__file__).parent / "backend" / "poller" / "main.py"
API_SCRIPT = Path(__file__).parent / "backend" / "api" / "main.py"

@pytest.fixture(scope="module")
def services():
    """Start API and poller as subprocesses for the test session"""
    api_proc = subprocess.Popen(
        [sys.executable, str(API_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    poller_proc = subprocess.Popen(
        [sys.executable, str(POLLER_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for API to be ready
    for _ in range(30):
        try:
            r = requests.get("http://localhost:8000/api/health", timeout=1)
            if r.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
    else:
        api_proc.terminate()
        poller_proc.terminate()
        pytest.fail("API did not start in time")
    
    yield
    
    # Cleanup
    api_proc.terminate()
    poller_proc.terminate()
    api_proc.wait(timeout=5)
    poller_proc.wait(timeout=5)

def test_health_endpoint(services):
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_poller_inserts_data(services):
    # Wait for at least one poll cycle (max 6 minutes)
    for _ in range(36):  # 36 * 10 seconds = 6 minutes
        stats = requests.get(f"{BASE_URL}/stats").json()
        if stats["total_samples"] > 0:
            break
        time.sleep(10)
    else:
        pytest.fail("No samples inserted after 6 minutes")
    
    assert stats["total_samples"] >= 1

def test_daily_endpoint_returns_data(services):
    # Get today's date
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    response = requests.get(f"{BASE_URL}/daily/{today}?resolution=minute")
    assert response.status_code == 200
    data = response.json()
    # May be empty if no samples today yet, but at least it's a list
    assert isinstance(data, list)

def test_weekly_chart_data(services):
    response = requests.get(f"{BASE_URL}/week")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # If there are any days, each day should have a list of windows
    for day, windows in data.items():
        assert isinstance(windows, list)

def test_worst_times_analysis(services):
    response = requests.get(f"{BASE_URL}/worst-times?days=7&window_minutes=15")
    assert response.status_code == 200
    result = response.json()
    assert "worst_periods" in result
    # It may be empty if insufficient data, but structure is correct
    assert isinstance(result["worst_periods"], list)

def test_csv_export(services):
    from datetime import datetime, timedelta
    end = datetime.now()
    start = end - timedelta(days=1)
    params = {
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d")
    }
    response = requests.get(f"{BASE_URL}/export", params=params)
    # Even if no data, should return CSV with headers
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    content = response.text
    assert "Download (Mbps)" in content or "Datetime" in content