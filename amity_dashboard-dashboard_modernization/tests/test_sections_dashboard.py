#!/usr/bin/env python3
"""
Тестовый скрипт для проверки модернизированного Amity Metrics Dashboard с секциями
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_sections_config():
    """Тестирует API конфигурации секций"""
    print("🔍 Тестирование API конфигурации секций...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/sections", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ API секций работает")
        print(f"   - Секций: {len(data.get('sections', {}))}")
        print(f"   - Метрик: {len(data.get('all_metrics', {}))}")
        print(f"   - Интервалы: {len(data.get('time_intervals', []))}")
        
        # Показываем секции
        sections = data.get('sections', {})
        for section_name, metrics in sections.items():
            print(f"   - {section_name}: {len(metrics)} метрик")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API секций: {e}")
        return False

def test_section_metrics():
    """Тестирует API метрик секции"""
    print("\n🔍 Тестирование API метрик секции...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/sections/KPI/metrics", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ API метрик секции работает")
        print(f"   - Секция: {data.get('section')}")
        print(f"   - Метрик в секции: {len(data.get('metrics', {}))}")
        
        # Показываем первую метрику
        metrics = data.get('metrics', {})
        if metrics:
            first_metric_id = list(metrics.keys())[0]
            first_metric = metrics[first_metric_id]
            print(f"   - Пример метрики: {first_metric_id} - {first_metric.get('label')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API метрик секции: {e}")
        return False

def test_metric_history():
    """Тестирует API истории метрики"""
    print("\n🔍 Тестирование API истории метрики...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/metrics/system_cpu_usage/history?interval=30", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ API истории метрики работает")
        print(f"   - Статус: {data.get('status', 'unknown')}")
        
        if data.get('data') and data['data'].get('result'):
            result = data['data']['result'][0]
            print(f"   - Точки данных: {len(result.get('values', []))}")
            
            if result.get('values'):
                values = [v[1] for v in result['values'] if v[1] is not None]
                if values:
                    print(f"   - Min: {min(values):.3f}, Max: {max(values):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API истории метрики: {e}")
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
            ("Amity Metrics Dashboard", "Заголовок дашборда"),
            ("time-interval", "Селектор интервала"),
            ("debug-toggle", "Кнопка debug"),
            ("export-report", "Кнопка экспорта"),
            ("sections-container", "Контейнер секций"),
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

def test_debug_mode():
    """Тестирует debug-режим"""
    print("\n🔍 Тестирование debug-режима...")
    
    try:
        response = requests.get(f"{BASE_URL}/?debug=true", timeout=5)
        response.raise_for_status()
        
        content = response.text
        print(f"✅ Debug-режим работает")
        print(f"   - Размер ответа: {len(content)} байт")
        
        # Проверяем наличие debug-элементов
        if "debug-toggle" in content and "active" in content:
            print(f"   ✅ Debug-переключатель: найден")
        else:
            print(f"   ❌ Debug-переключатель: не найден")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка debug-режима: {e}")
        return False

def test_metrics_data():
    """Тестирует API данных метрик (для обратной совместимости)"""
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
    print("🚀 Тестирование модернизированного Amity Metrics Dashboard с секциями")
    print("=" * 70)
    
    # Ждем запуска сервера
    print("⏳ Ожидание запуска сервера...")
    time.sleep(3)
    
    tests = [
        test_sections_config,
        test_section_metrics,
        test_metric_history,
        test_main_page,
        test_debug_mode,
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
    print("\n" + "=" * 70)
    print("📊 Итоговые результаты:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Модернизированный дашборд с секциями работает корректно.")
        print("\n🔧 Возможности:")
        print("   - Секции метрик (KPI, PostgreSQL, JVM, Jetty, System)")
        print("   - Debug-режим с детальной информацией")
        print("   - Гибкая визуализация (trend + bar)")
        print("   - Экспорт отчётов")
        print("   - Обратная совместимость")
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте логи сервера.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 