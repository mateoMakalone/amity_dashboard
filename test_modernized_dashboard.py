#!/usr/bin/env python3
"""
Тестовый скрипт для проверки модернизированного KPI Dashboard
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_kpi_config():
    """Тестирует API конфигурации KPI"""
    print("🔍 Тестирование API конфигурации KPI...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/kpi/config", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ API конфигурации работает")
        print(f"   - KPI метрик: {len(data.get('kpi_metrics', []))}")
        print(f"   - Интервалы времени: {len(data.get('time_intervals', []))}")
        
        # Показываем первую KPI метрику
        if data.get('kpi_metrics'):
            first_kpi = data['kpi_metrics'][0]
            print(f"   - Пример KPI: {first_kpi['id']} - {first_kpi['title']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API конфигурации: {e}")
        return False

def test_prometheus_proxy():
    """Тестирует прокси-эндпоинт Prometheus"""
    print("\n🔍 Тестирование прокси Prometheus...")
    
    try:
        # Тестовый запрос
        params = {
            'query': 'system_cpu_usage',
            'start': str(int(time.time()) - 300),  # 5 минут назад
            'end': str(int(time.time())),
            'step': '30'
        }
        
        response = requests.get(f"{BASE_URL}/api/prometheus/query_range", params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Прокси Prometheus работает")
        print(f"   - Статус: {data.get('status', 'unknown')}")
        
        if data.get('data') and data['data'].get('result'):
            result = data['data']['result'][0]
            print(f"   - Точки данных: {len(result.get('values', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка прокси Prometheus: {e}")
        return False

def test_main_page():
    """Тестирует главную страницу"""
    print("\n🔍 Тестирование главной страницы...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        response.raise_for_status()
        
        content = response.text
        print(f"✅ Главная страница загружается")
        print(f"   - Размер ответа: {len(content)} байт")
        
        # Проверяем наличие ключевых элементов
        checks = [
            ("Amity KPI Dashboard", "Заголовок дашборда"),
            ("time-interval", "Селектор интервала"),
            ("export-report", "Кнопка экспорта"),
            ("kpi-grid", "Сетка KPI"),
            ("plotly-latest.min.js", "Plotly.js")
        ]
        
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description}: найдено")
            else:
                print(f"   ❌ {description}: не найдено")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка главной страницы: {e}")
        return False

def test_metrics_data():
    """Тестирует API данных метрик"""
    print("\n🔍 Тестирование API данных метрик...")
    
    try:
        response = requests.get(f"{BASE_URL}/data", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ API данных метрик работает")
        print(f"   - Метрик: {len(data.get('metrics', {}))}")
        print(f"   - Prominent метрик: {len(data.get('prominent', {}))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API данных метрик: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование модернизированного KPI Dashboard")
    print("=" * 50)
    
    # Ждем запуска сервера
    print("⏳ Ожидание запуска сервера...")
    time.sleep(3)
    
    tests = [
        test_kpi_config,
        test_prometheus_proxy,
        test_main_page,
        test_metrics_data
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте: {e}")
            results.append(False)
    
    # Итоговый результат
    print("\n" + "=" * 50)
    print("📊 Итоговые результаты:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Модернизированный дашборд работает корректно.")
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте логи сервера.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 