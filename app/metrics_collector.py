import os
import time
import threading
import requests
from app.parser import parse_prometheus_text

METRICS_ENDPOINT = os.getenv("METRICS_ENDPOINT", "http://127.0.0.1:8000/metrics")
MOCK_MODE = os.getenv("MOCK_MODE", "False").lower() == "true"
HISTORY_SECONDS = int(os.getenv("METRIC_HISTORY_SECONDS", 3600))
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", 1))

metrics_data = {"history": {}}

def fetch_metrics_text():
    if MOCK_MODE:
        with open("mock_metrics.txt", "r", encoding="utf-8") as f:
            return f.read()
    resp = requests.get(METRICS_ENDPOINT)
    resp.raise_for_status()
    return resp.text

def collect_history():
    while True:
        try:
            text = fetch_metrics_text()
            data = parse_prometheus_text(text)
            now = int(time.time())
            for key, value in data.items():
                if key not in metrics_data["history"]:
                    metrics_data["history"][key] = []
                metrics_data["history"][key].append({"ts": now, "value": value})
                # sliding window 60 минут
                metrics_data["history"][key] = [d for d in metrics_data["history"][key] if d["ts"] >= now - HISTORY_SECONDS]
        except Exception as e:
            print(f"[ERROR] collect_history: {e}")
        time.sleep(SCRAPE_INTERVAL)

def start_metrics_collector():
    t = threading.Thread(target=collect_history, daemon=True)
    t.start() 