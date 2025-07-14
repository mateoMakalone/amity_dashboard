import requests
import time
import json

# === прод дебаг ===
DASHBOARD_URL = "http://localhost:5000/dashboard_data"  # Замените на реальный адрес, если нужно
HISTORY_URL = "http://localhost:5000/history"
LOG_FILE = "prod_history_log.json"


def fetch_and_log():
    log = {"dashboard_data": [], "history": []}
    for i in range(10):  # 10 последовательных замеров
        try:
            dash_resp = requests.get(DASHBOARD_URL, timeout=5)
            dash_data = dash_resp.json()
            hist_resp = requests.get(HISTORY_URL, timeout=5)
            hist_data = hist_resp.json()
            log["dashboard_data"].append({
                "timestamp": time.time(),
                "prominent": dash_data.get("prominent", {}),
                "metrics": dash_data.get("metrics", {}),
                "history_keys": list(dash_data.get("history", {}).keys()),
                "error": dash_data.get("error")
            })
            log["history"].append({
                "timestamp": time.time(),
                "history": hist_data
            })
            print(f"Iteration {i+1}/10 complete")
        except Exception as e:
            print(f"Error on iteration {i+1}: {e}")
        time.sleep(5)  # 5 секунд между запросами

    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)
    print(f"Log saved to {LOG_FILE}")

if __name__ == "__main__":
    fetch_and_log() 