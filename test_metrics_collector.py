#!/usr/bin/env python3
import os
import sys
import requests

def main():
    # Определяем endpoint метрик
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = os.getenv("METRICS_ENDPOINT") or os.getenv("METRICS_URL") or "http://127.0.0.1:8000/metrics"
    print(f"Fetching metrics from {url}")
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to fetch metrics: {e}")
        sys.exit(1)
    text = resp.text
    lines = text.splitlines()
    success = []
    errors = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            errors.append(line)
            continue
        key = parts[0]
        val_str = parts[-1]
        try:
            float(val_str)
            success.append(key)
        except Exception:
            errors.append(key)
    print(f"Total metrics parsed: {len(success)}")
    if success:
        print("Successful metrics:")
        for key in success:
            print(f"  {key}")
    if errors:
        print("Erroneous metrics:")
        for key in errors:
            print(f"  {key}")

if __name__ == "__main__":
    main() 