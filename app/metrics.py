
import json, os, time
from collections import deque

# Определяем путь кэша в зависимости от ОС
if os.name == 'nt':  # Windows
    CACHE_FILE = os.path.join(os.getcwd(), 'metrics_cache.json')
else:  # Unix/Linux
    CACHE_FILE = '/tmp/metrics_cache.json'
SAVE_INTERVAL = 60
last_save_time = 0

def load_cache_from_file():
    """
    Загружает кэш из файла с полной обработкой ошибок
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(CACHE_FILE):
            print(f"[DEBUG] Cache file {CACHE_FILE} does not exist, starting with empty cache")
            return
        
        # Проверяем размер файла
        file_size = os.path.getsize(CACHE_FILE)
        if file_size == 0:
            print(f"[DEBUG] Cache file {CACHE_FILE} is empty, starting with empty cache")
            return
        
        # Читаем файл
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # Проверяем, что файл не пустой после чтения
        if not content:
            print(f"[DEBUG] Cache file {CACHE_FILE} is empty after reading, starting with empty cache")
            return
            
        # Парсим JSON
        data = json.loads(content)
        
        # Валидируем данные кэша
        if not validate_cache_data(data):
            print(f"[WARNING] Cache file {CACHE_FILE} contains invalid data structure, starting with empty cache")
            return
            
        metrics = data.get("metrics", {})
        history = data.get("history", {})
        
        # Загружаем данные в глобальную структуру
        with lock:
            metrics_data["metrics"] = metrics
            # Создаем deque для каждой метрики с правильным maxlen
            for name, vals in history.items():
                if isinstance(vals, list):
                    # Конвертируем список в deque с ограничением размера
                    deq = deque(vals, maxlen=HISTORY_POINTS)
                    metrics_data["history"][name] = deq
                else:
                    print(f"[WARNING] Invalid history data for {name}, skipping")
                    
        print(f"[DEBUG] Cache loaded from {CACHE_FILE}: {len(metrics)} metrics, {len(history)} history entries")
        
    except FileNotFoundError:
        print(f"[DEBUG] Cache file {CACHE_FILE} not found, starting with empty cache")
    except PermissionError as e:
        print(f"[WARNING] Permission error reading cache file {CACHE_FILE}: {e}")
    except json.JSONDecodeError as e:
        print(f"[WARNING] Invalid JSON in cache file {CACHE_FILE}: {e}")
        # Пытаемся создать резервную копию поврежденного файла
        try:
            backup_file = f"{CACHE_FILE}.corrupted.{int(time.time())}"
            os.rename(CACHE_FILE, backup_file)
            print(f"[INFO] Corrupted cache file moved to {backup_file}")
        except Exception as backup_error:
            print(f"[ERROR] Failed to backup corrupted cache file: {backup_error}")
    except Exception as e:
        print(f"[ERROR] Unexpected error loading cache from {CACHE_FILE}: {e}")

def save_cache_to_file():
    """
    Сохраняет кэш в файл с полной обработкой ошибок
    """
    global last_save_time
    now = time.time()
    
    # Проверяем интервал сохранения
    if now - last_save_time < SAVE_INTERVAL:
        return
        
    try:
        # Подготавливаем данные для сохранения
        with lock:
            data = {
                "metrics": metrics_data["metrics"],
                "history": {name: list(deq) for name, deq in metrics_data["history"].items()},
                "last_updated": metrics_data["last_updated"],
                "cache_version": "1.0"  # Для будущей совместимости
            }
        
        # Создаем временный файл для атомарной записи
        temp_file = f"{CACHE_FILE}.tmp"
        
        # Записываем во временный файл
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Атомарно перемещаем временный файл в целевой
        os.replace(temp_file, CACHE_FILE)
        
        last_save_time = now
        print(f"[DEBUG] Cache saved to {CACHE_FILE}: {len(data['metrics'])} metrics, {len(data['history'])} history entries")
        
    except PermissionError as e:
        print(f"[WARNING] Permission error saving cache to {CACHE_FILE}: {e}")
    except OSError as e:
        print(f"[WARNING] OS error saving cache to {CACHE_FILE}: {e}")
        # Пытаемся создать кэш в альтернативном месте
        try:
            alt_cache_file = os.path.join(os.getcwd(), 'metrics_cache.json')
            with open(alt_cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Cache saved to alternative location: {alt_cache_file}")
        except Exception as alt_error:
            print(f"[ERROR] Failed to save cache to alternative location: {alt_error}")
    except Exception as e:
        print(f"[ERROR] Unexpected error saving cache to {CACHE_FILE}: {e}")

def ensure_cache_directory():
    """
    Убеждается, что директория для кэша существует и доступна для записи
    """
    global CACHE_FILE
    try:
        cache_dir = os.path.dirname(CACHE_FILE)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            print(f"[DEBUG] Created cache directory: {cache_dir}")
        
        # Проверяем права на запись
        if os.path.exists(cache_dir):
            test_file = os.path.join(cache_dir, '.test_write')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"[DEBUG] Cache directory {cache_dir} is writable")
            except Exception as e:
                print(f"[WARNING] Cache directory {cache_dir} is not writable: {e}")
                # Пытаемся использовать альтернативную директорию
                alt_dir = os.getcwd()
                CACHE_FILE = os.path.join(alt_dir, 'metrics_cache.json')
                print(f"[INFO] Using alternative cache location: {CACHE_FILE}")
                
    except Exception as e:
        print(f"[ERROR] Failed to ensure cache directory: {e}")

import threading
import time
import os
import requests
from collections import defaultdict, deque
from .parser import parse_metrics, should_display_metric, filter_metric, sum_metric, get_metric, eval_formula
from .config import METRICS_URL, REQUEST_TIMEOUT, UPDATE_INTERVAL, KPI_METRICS_CONFIG, ALL_METRICS, INITIAL_METRICS, SECTIONS
from app.utils_metric_key import MetricKeyHelper

HISTORY_SECONDS = 3600  # 1 час
HISTORY_POINTS = int(HISTORY_SECONDS / UPDATE_INTERVAL)

metrics_data = {
    "metrics": {},
    "history": defaultdict(lambda: deque(maxlen=HISTORY_POINTS)),
    "last_updated": 0,
    "last_error": None
}

lock = threading.Lock()

_cache = {}

def get_cached_data(fn, ttl=0.5, cache_key=None):
    now = time.time()
    key = cache_key or fn.__name__
    if key in _cache:
        value, ts = _cache[key]
        if now - ts < ttl:
            return value
    value = fn()
    _cache[key] = (value, now)
    return value

def find_metric_value(metrics, key):
    # Точное совпадение по ключу
    if key in metrics:
        return metrics[key]
    # Если ключ с лейблами — ищем по base_name и лейблам
    if '{' in key:
        base = key.split('{')[0]
        label_str = key[key.find('{')+1:key.find('}')]
        labels = dict(pair.split('=') for pair in label_str.split(',') if '=' in pair)
        labels = {k.strip(): v.strip().strip('"') for k, v in labels.items()}
        for k, v in metrics.items():
            if k.startswith(base + '{'):
                k_label_str = k[k.find('{')+1:k.find('}')]
                k_labels = dict(pair.split('=') for pair in k_label_str.split(',') if '=' in pair)
                k_labels = {kk.strip(): vv.strip().strip('"') for kk, vv in k_labels.items()}
                if labels == k_labels:
                    return v
    # Fallback на base_name
    base = key.split('{')[0]
    return metrics.get(base, 0)

class MetricsService:
    @staticmethod
    def normalize_metrics(raw_metrics):
        """
        Парсит строки, фильтрует комментарии, преобразует значения в float, нормализует ключи
        """
        parsed = parse_metrics(raw_metrics)
        metrics = {}
        for name, value in parsed.items():
            metrics[name] = value
            # Нормализация: postgres_locks{...} и postgres_locks → в одну мапу
            base = name.split('{')[0]
            if base not in metrics:
                metrics[base] = value
        return metrics

    @staticmethod
    def get_metrics_data():
        # Получаем текущие метрики и ошибку из глобальных данных
        with lock:
            current_metrics = dict(metrics_data["metrics"])
            error = metrics_data["last_error"]
        # Вычисляем среднее время ответа (get/post)
        get_count = current_metrics.get('jetty_server_requests_seconds_count{method="GET",outcome="SUCCESS",status="200"}', 0.0)
        post_count = current_metrics.get('jetty_server_requests_seconds_count{method="POST",outcome="SUCCESS",status="200"}', 0.0)
        total_count = get_count + post_count
        get_sum = current_metrics.get('jetty_server_requests_seconds_sum{method="GET",outcome="SUCCESS",status="200"}', 0.0)
        post_sum = current_metrics.get('jetty_server_requests_seconds_sum{method="POST",outcome="SUCCESS",status="200"}', 0.0)
        total_sum = get_sum + post_sum
        if total_count > 0:
            current_metrics['jetty_server_requests_seconds_avg'] = total_sum / total_count
        if get_count > 0:
            current_metrics['jetty_get_avg_time'] = get_sum / get_count
        if post_count > 0:
            current_metrics['jetty_post_avg_time'] = post_sum / post_count

        # Составляем KPI-метрики на основе конфигурации
        prominent = {}
        for config in KPI_METRICS_CONFIG:
            name = config["id"]
            norm_name = MetricKeyHelper.normalize(name)
            if norm_name in current_metrics:
                value = current_metrics[norm_name]
            elif "formula" in config:
                value = eval_formula(config["formula"], current_metrics)
            else:
                value = get_metric(current_metrics, norm_name)
            if value is None:
                value = 0.0
            prominent[name] = value
        return {"metrics": current_metrics, "prominent": prominent, "error": error}

    @staticmethod
    def get_metrics_history():
        with lock:
            return {name: list(history) for name, history in metrics_data["history"].items()}
        
    @classmethod
    def get_all_metrics(cls):
        """
        Возвращает последние значения и историю для всех метрик.
        """
        with lock:
            data = {}
            for name, value in metrics_data["metrics"].items():
                history = metrics_data["history"].get(name, [])
                data[name] = {
                    "current": value,
                    "history": list(history)
                }
            return data

    @classmethod
    def get_metrics_history(cls):
        """
        Возвращает историю всех метрик.
        """
        with lock:
            return {name: list(history) for name, history in metrics_data["history"].items()}

def update_metrics():
    print("[DEBUG] update_metrics: поток сбора метрик стартовал")
    
    while True:
        try:
            start_time = time.time()
            print(f"[DEBUG] update_metrics: запрос к {METRICS_URL}")
            response = requests.get(METRICS_URL, timeout=REQUEST_TIMEOUT)
            print(f"[DEBUG] update_metrics: получен ответ, длина={len(response.text)}")
            parsed = parse_metrics(response.text)
            print(f"[DEBUG] update_metrics: распарсено {len(parsed)} метрик")
            now = time.time()
            with lock:
                for name, value in parsed.items():
                    # Сохраняем все метрики
                    metrics_data["metrics"][name] = value
                # === NEW: обновляем историю только по ключам из KPI_METRICS_CONFIG и SECTIONS ===
                all_metric_names = set(config["id"] for config in KPI_METRICS_CONFIG)
                for category_name, metrics_list in SECTIONS.items():
                    for pattern in metrics_list:
                        all_metric_names.add(pattern)
                for metric_name in all_metric_names:
                    norm_name = MetricKeyHelper.normalize(metric_name)
                    value = find_metric_value(metrics_data["metrics"], norm_name)
                    if value is None:
                        value = 0.0
                    metrics_data["history"][norm_name].append((now, value))
                # === END NEW ===
                # === TEST LOGS: выводим состояние истории для диагностики ===
                for test_metric in ["jetty_server_requests_seconds_avg", "postgres_connections"]:
                    hist = metrics_data["history"].get(test_metric)
                    if hist:
                        print(f"[TEST] {test_metric}: history_len={len(hist)}, last={hist[-1]}")
                    else:
                        print(f"[TEST] {test_metric}: NO HISTORY")
                # === END TEST LOGS ===
                metrics_data["last_updated"] = now
                metrics_data["last_error"] = None
                print(f"[DEBUG] update_metrics: metrics_data['metrics'] keys: {list(metrics_data['metrics'].keys())}")
                
            # Сохраняем кэш после каждого обновления метрик
            save_cache_to_file()
            
        except Exception as e:
            with lock:
                metrics_data["last_error"] = str(e)
                print(f"[ERROR] Metrics update failed: {e}")
        time.sleep(max(0, UPDATE_INTERVAL - (time.time() - start_time)))

def get_all_metric_names():
    """
    Возвращает все имена метрик из конфигурации
    """
    names = set(config["id"] for config in KPI_METRICS_CONFIG)
    for category_name, metrics_list in SECTIONS.items():
        for pattern in metrics_list:
            # Если pattern не содержит спецсимволов, добавляем как есть
            if not any(c in pattern for c in ".*?[]{}()^$|+\\"):
                names.add(pattern)
    return names

def cleanup_old_cache_files():
    """
    Очищает старые поврежденные файлы кэша
    """
    try:
        cache_dir = os.path.dirname(CACHE_FILE)
        if not cache_dir:
            cache_dir = os.getcwd()
            
        # Ищем файлы с паттерном .corrupted.*
        for filename in os.listdir(cache_dir):
            if filename.startswith('metrics_cache.json.corrupted.'):
                file_path = os.path.join(cache_dir, filename)
                file_age = time.time() - os.path.getmtime(file_path)
                
                # Удаляем файлы старше 24 часов
                if file_age > 86400:  # 24 часа в секундах
                    try:
                        os.remove(file_path)
                        print(f"[DEBUG] Removed old corrupted cache file: {filename}")
                    except Exception as e:
                        print(f"[WARNING] Failed to remove old cache file {filename}: {e}")
                        
    except Exception as e:
        print(f"[WARNING] Failed to cleanup old cache files: {e}")

def validate_cache_data(data):
    """
    Валидирует данные кэша и возвращает True если данные корректны
    """
    try:
        if not isinstance(data, dict):
            return False
            
        # Проверяем обязательные поля
        required_fields = ['metrics', 'history']
        for field in required_fields:
            if field not in data:
                return False
                
        # Проверяем типы данных
        if not isinstance(data['metrics'], dict):
            return False
            
        if not isinstance(data['history'], dict):
            return False
            
        # Проверяем структуру истории
        for metric_name, history_data in data['history'].items():
            if not isinstance(history_data, list):
                return False
                
            # Проверяем каждый элемент истории
            for point in history_data:
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    return False
                    
                timestamp, value = point
                if not isinstance(timestamp, (int, float)):
                    return False
                    
        return True
        
    except Exception:
        return False


def start_metrics_thread():
    """
    Запускает поток обновления метрик
    """
    # Очищаем старые поврежденные файлы кэша
    cleanup_old_cache_files()
    
    # Инициализируем директорию кэша
    ensure_cache_directory()
    
    # Загружаем кэш из файла
    load_cache_from_file()
    
    # Запускаем поток обновления метрик
    thread = threading.Thread(target=update_metrics, daemon=True)
    thread.start()
