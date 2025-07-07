import requests
import threading
import time
from collections import defaultdict, deque
from .parser import parse_metrics, should_display_metric
from .config import METRICS_URL, REQUEST_TIMEOUT, UPDATE_INTERVAL, HISTORY_LENGTH, METRICS_CONFIG, PROMINENT_METRICS

HISTORY_SECONDS = 3600  # 1 час
HISTORY_POINTS = int(HISTORY_SECONDS / UPDATE_INTERVAL)

metrics_data = {
    "metrics": {},
    # history: {metric_name: deque([(timestamp, value), ...], maxlen=HISTORY_POINTS)}
    "history": defaultdict(lambda: deque(maxlen=HISTORY_POINTS)),
    "last_updated": 0,
    "last_error": None
}

lock = threading.Lock()

def update_metrics():
    while True:
        try:
            start_time = time.time()
            response = requests.get(METRICS_URL, timeout=REQUEST_TIMEOUT)
            parsed = parse_metrics(response.text)

            now = time.time()
            with lock:
                for name, value in parsed.items():
                    if should_display_metric(name, METRICS_CONFIG):
                        metrics_data["metrics"][name] = value
                        metrics_data["history"][name].append((now, value))
                metrics_data["last_updated"] = now
                metrics_data["last_error"] = None
        except Exception as e:
            with lock:
                metrics_data["last_error"] = str(e)
        time.sleep(max(0, UPDATE_INTERVAL - (time.time() - start_time)))

def get_metrics_data():
    with lock:
        metrics = metrics_data["metrics"].copy()

        post_count = metrics.get('jetty_server_requests_seconds_count{method="POST",outcome="SUCCESS",status="200",}')
        post_sum = metrics.get('jetty_server_requests_seconds_sum{method="POST",outcome="SUCCESS",status="200",}')
        if post_count and post_sum and post_count > 0:
            metrics['jetty_post_avg_time'] = post_sum / post_count

        get_count = metrics.get('jetty_server_requests_seconds_count{method="GET",outcome="SUCCESS",status="200",}')
        get_sum = metrics.get('jetty_server_requests_seconds_sum{method="GET",outcome="SUCCESS",status="200",}')
        if get_count and get_sum and get_count > 0:
            metrics['jetty_get_avg_time'] = get_sum / get_count

        return {
            "metrics": metrics,
            "config": METRICS_CONFIG,
            "prominent": PROMINENT_METRICS,
            "last_updated": metrics_data["last_updated"],
            "error": metrics_data["last_error"]
        }

def get_metrics_history():
    with lock:
        # Возвращаем историю для всех метрик: {name: [(timestamp, value), ...], ...}
        return {name: list(history) for name, history in metrics_data["history"].items()}

def start_metrics_thread():
    thread = threading.Thread(target=update_metrics, daemon=True)
    thread.start()
