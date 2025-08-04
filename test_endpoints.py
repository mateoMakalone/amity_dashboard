#!/usr/bin/env python3
"""
Скрипт для тестирования endpoints дашборда
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, description):
    """Тестирует endpoint и выводит результат"""
    try:
        print(f"\n🔍 Тестируем {description}...")
        print(f"URL: {BASE_URL}{endpoint}")
        
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Успешно! Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            except json.JSONDecodeError:
                print(f"⚠️ Ответ не является JSON: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Ошибка! Статус: {response.status_code}")
            print(f"Текст ответа: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Ошибка подключения к {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование endpoints дашборда")
    print("=" * 50)
    
    endpoints = [
        ("/", "Главная страница"),
        ("/api/test", "Тестовый endpoint"),
        ("/api/debug", "Диагностический endpoint"),
        ("/api/sections", "Конфигурация секций"),
        ("/api/kpi/config", "Конфигурация KPI"),
        ("/data", "Данные метрик"),
        ("/dashboard_data", "Данные дашборда"),
        ("/api/metrics/batch", "Batch метрики"),
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        success = test_endpoint(endpoint, description)
        results.append((endpoint, success))
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    
    for endpoint, success in results:
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        print(f"{status}: {endpoint}")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nИтого: {successful}/{total} endpoints работают")
    
    if successful == total:
        print("🎉 Все endpoints работают корректно!")
    else:
        print("⚠️ Есть проблемы с некоторыми endpoints")

if __name__ == "__main__":
    main() 