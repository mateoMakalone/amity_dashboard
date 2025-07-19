import subprocess
import requests
import time
import os
import json

LOG_FILE = "debug_metrics_log.txt"


def run_and_log_metrics():
    # Запустить Flask-приложение в фоне
    proc = subprocess.Popen(["python", "run.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        # Дать время на запуск
        time.sleep(4)
        # Собрать данные с бэка
        dashboard = requests.get("http://127.0.0.1:5000/dashboard_data", timeout=5).json()
        history = dashboard.get("history", {})
        metrics = dashboard.get("metrics", {})
        prominent = dashboard.get("prominent", {})
        # Сформировать компактный лог
        log = {
            "history_keys": list(history.keys()),
            "metrics_keys": list(metrics.keys()),
            "prominent_keys": list(prominent.keys()),
            "history_last": {k: v[-1] if v else None for k, v in history.items()},
            "metrics_sample": {k: metrics[k] for k in list(metrics)[:10]},
            "prominent_sample": {k: prominent[k] for k in list(prominent)[:10]},
        }
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(json.dumps(log, ensure_ascii=False, indent=2))
    except Exception as e:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"ERROR: {e}\n")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_and_log_metrics() 