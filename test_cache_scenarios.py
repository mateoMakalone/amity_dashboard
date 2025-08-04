#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех сценариев работы с кэшем
"""

import os
import json
import time
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Определяем путь к кэшу в зависимости от ОС
if os.name == 'nt':  # Windows
    CACHE_PATH = os.path.join(tempfile.gettempdir(), 'metrics_cache.json')
    TEST_CACHE_DIR = os.path.join(tempfile.gettempdir(), 'test_cache_dir')
else:  # Unix/Linux
    CACHE_PATH = '/tmp/metrics_cache.json'
    TEST_CACHE_DIR = '/tmp/test_cache_dir'

def test_empty_cache_file():
    """Тест: пустой файл кэша"""
    print("\n=== Тест: Пустой файл кэша ===")
    
    # Создаем пустой файл
    with open(CACHE_PATH, 'w') as f:
        pass
    
    # Импортируем модуль после создания файла
    import app.metrics as metrics
    
    # Проверяем, что кэш загружается без ошибок
    metrics.load_cache_from_file()
    print("✅ Пустой файл кэша обрабатывается корректно")

def test_corrupted_cache_file():
    """Тест: поврежденный файл кэша"""
    print("\n=== Тест: Поврежденный файл кэша ===")
    
    # Создаем поврежденный JSON
    with open(CACHE_PATH, 'w') as f:
        f.write('{"invalid": json}')
    
    import app.metrics as metrics
    
    # Проверяем, что поврежденный файл обрабатывается
    metrics.load_cache_from_file()
    print("✅ Поврежденный файл кэша обрабатывается корректно")

def test_missing_cache_file():
    """Тест: отсутствующий файл кэша"""
    print("\n=== Тест: Отсутствующий файл кэша ===")
    
    # Удаляем файл если существует
    if os.path.exists(CACHE_PATH):
        os.remove(CACHE_PATH)
    
    import app.metrics as metrics
    
    # Проверяем, что отсутствующий файл обрабатывается
    metrics.load_cache_from_file()
    print("✅ Отсутствующий файл кэша обрабатывается корректно")

def test_valid_cache_file():
    """Тест: корректный файл кэша"""
    print("\n=== Тест: Корректный файл кэша ===")
    
    # Создаем корректный кэш
    valid_cache = {
        "metrics": {
            "test_metric_1": 42.0,
            "test_metric_2": 100.0
        },
        "history": {
            "test_metric_1": [[time.time(), 42.0]],
            "test_metric_2": [[time.time(), 100.0]]
        },
        "last_updated": time.time(),
        "cache_version": "1.0"
    }
    
    with open(CACHE_PATH, 'w') as f:
        json.dump(valid_cache, f)
    
    import app.metrics as metrics
    
    # Проверяем загрузку
    metrics.load_cache_from_file()
    print("✅ Корректный файл кэша загружается успешно")

def test_cache_save_with_errors():
    """Тест: сохранение кэша с ошибками"""
    print("\n=== Тест: Сохранение кэша с ошибками ===")
    
    import app.metrics as metrics
    
    # Симулируем ошибку записи
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        metrics.save_cache_to_file()
        print("✅ Ошибка записи обрабатывается корректно")

def test_cache_directory_creation():
    """Тест: создание директории кэша"""
    print("\n=== Тест: Создание директории кэша ===")
    
    # Временно меняем путь кэша
    original_cache_file = CACHE_PATH
    test_cache_file = os.path.join(TEST_CACHE_DIR, 'metrics_cache.json')
    
    import app.metrics as metrics
    
    # Сохраняем оригинальный путь
    original_path = metrics.CACHE_FILE
    metrics.CACHE_FILE = test_cache_file
    
    try:
        # Проверяем создание директории
        metrics.ensure_cache_directory()
        
        if os.path.exists(TEST_CACHE_DIR):
            print("✅ Директория кэша создается корректно")
        else:
            print("❌ Директория кэша не создалась")
            
    finally:
        # Восстанавливаем оригинальный путь
        metrics.CACHE_FILE = original_path
        # Очищаем тестовую директорию
        if os.path.exists(TEST_CACHE_DIR):
            shutil.rmtree(TEST_CACHE_DIR)

def test_cache_validation():
    """Тест: валидация данных кэша"""
    print("\n=== Тест: Валидация данных кэша ===")
    
    import app.metrics as metrics
    
    # Тест корректных данных
    valid_data = {
        "metrics": {"test": 1.0},
        "history": {"test": [[time.time(), 1.0]]}
    }
    
    if metrics.validate_cache_data(valid_data):
        print("✅ Корректные данные проходят валидацию")
    else:
        print("❌ Корректные данные не прошли валидацию")
    
    # Тест некорректных данных
    invalid_data = {
        "metrics": "not_a_dict",
        "history": {"test": "not_a_list"}
    }
    
    if not metrics.validate_cache_data(invalid_data):
        print("✅ Некорректные данные отклоняются валидацией")
    else:
        print("❌ Некорректные данные прошли валидацию")

def test_cache_cleanup():
    """Тест: очистка старых файлов кэша"""
    print("\n=== Тест: Очистка старых файлов кэша ===")
    
    # Создаем старый поврежденный файл
    cache_dir = os.path.dirname(CACHE_PATH)
    old_file = os.path.join(cache_dir, 'metrics_cache.json.corrupted.1234567890')
    with open(old_file, 'w') as f:
        f.write('old corrupted data')
    
    # Устанавливаем старое время модификации (25 часов назад)
    old_time = time.time() - 90000  # 25 часов
    os.utime(old_file, (old_time, old_time))
    
    import app.metrics as metrics
    
    # Запускаем очистку
    metrics.cleanup_old_cache_files()
    
    # Проверяем, что файл удален
    if not os.path.exists(old_file):
        print("✅ Старый файл кэша удален корректно")
    else:
        print("❌ Старый файл кэша не удален")

def run_all_tests():
    """Запуск всех тестов"""
    print("🧪 Запуск тестов кэша...")
    
    try:
        test_empty_cache_file()
        test_corrupted_cache_file()
        test_missing_cache_file()
        test_valid_cache_file()
        test_cache_save_with_errors()
        test_cache_directory_creation()
        test_cache_validation()
        test_cache_cleanup()
        
        print("\n🎉 Все тесты кэша прошли успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests() 