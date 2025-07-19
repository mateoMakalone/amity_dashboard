import requests
import json
from app.metrics import MetricsService, get_metrics_history
import time

try:
    r = requests.get('http://localhost:5000/dashboard_data')
    data = r.json()
    
    print("=== Prominent metrics ===")
    for k, v in data['prominent'].items():
        if 'avg' in k:
            print(f"  {k}: {v}")
    
    print("\n=== All prominent keys ===")
    for k in data['prominent'].keys():
        print(f"  {k}")
        
    print(f"\n=== Total prominent metrics: {len(data['prominent'])} ===")
    
except Exception as e:
    print(f"Error: {e}") 

def test_history_and_values_keys_match():
    # Дать время на сбор метрик, если поток уже работает
    time.sleep(2)
    data = MetricsService.get_metrics_data()
    history = get_metrics_history()

    # Проверяем, что для каждого ключа из values есть история
    for key in data["metrics"]:
        assert key in history, f"History missing for key: {key}"

    # Проверяем, что для каждого ключа из истории есть значение
    for key in history:
        assert key in data["metrics"], f"Value missing for key: {key}" 