import time
import app.config as config

# Speed up and avoid real network requests
config.METRICS_URL = "http://127.0.0.1:9/metrics"
config.REQUEST_TIMEOUT = 0.1
config.UPDATE_INTERVAL = 0.2

from app import create_app

import pytest

@pytest.fixture(scope="module")
def client():
    app = create_app()
    with app.test_client() as client:
        # give the background metrics thread a moment
        time.sleep(0.3)
        yield client

def test_dashboard_data_history(client):
    resp = client.get("/dashboard_data")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert isinstance(data.get("history"), dict)

def test_postgres_dead_rows_history(client):
    resp = client.get("/api/metrics/postgres_dead_rows/history")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("status") == "success"
    assert "data" in data and "result" in data["data"]
