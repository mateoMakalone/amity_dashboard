import time
import threading
import requests
from app.parser import parse_metrics
from app.config import METRIC_HISTORY_SECONDS, SCRAPE_INTERVAL

METRIC_HISTORY = {}

def scrape_metrics():
    while True:
        try:
            resp = requests.get("http://localhost:8000/metrics")
            timestamp = int(time.time())
            parsed = parse_metrics(resp.text)
            for name, value in parsed.items():
                METRIC_HISTORY.setdefault(name, []).append((timestamp, value))
                # Очистка старых значений
                METRIC_HISTORY[name] = [
                    (ts, v) for ts, v in METRIC_HISTORY[name]
                    if ts >= timestamp - METRIC_HISTORY_SECONDS
                ]
        except Exception as e:
            print(f"[ERROR] scrape failed: {e}")
        time.sleep(SCRAPE_INTERVAL)

def start_metrics_collector():
    t = threading.Thread(target=scrape_metrics, daemon=True)
    t.start() 