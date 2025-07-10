import requests
import threading
import time
import os
from collections import defaultdict, deque
from .parser import parse_metrics, should_display_metric, filter_metric, sum_metric, get_metric, eval_formula
from .config import METRICS_URL, REQUEST_TIMEOUT, UPDATE_INTERVAL, HISTORY_LENGTH, METRICS_CONFIG, PROMINENT_METRICS, INITIAL_METRICS, MOCK_MODE
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

class MetricsService:
    @staticmethod
    def fetch_prometheus_metrics(url=METRICS_URL):
        """
        Загружает метрики с Prometheus endpoint
        """
        def fetch():
            try:
                response = requests.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.text, None
            except Exception as e:
                return None, str(e)
        return get_cached_data(fetch, ttl=0.5, cache_key='prometheus_metrics')

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
        if MOCK_MODE:
            # Моковые данные для тестирования фронта
            mock_metrics = {
                "process_cpu_usage": 0.75,
                "postgres_connections": 68.0,
                "postgres_locks": 1.0,
                "jvm_gc_pause_seconds_sum": 21.743,
                "jvm_memory_used_bytes": 192521736.0,
                "system_load_average_1m": 0.82,
                "jetty_server_requests_seconds_count": 1234.0,
                "postgres_rows_inserted_total": 1282731.0,
                "tx_pool_size": 150.0,
                "jetty_server_requests_seconds_avg": 0.045,
                "postgres_connections{database=\"db01\"}": 68.0,
                "jvm_memory_used_bytes{area=\"heap\",id=\"Tenured Gen\"}": 192521736.0,
                "postgres_locks{database=\"db01\"}": 1.0,
                "postgres_rows_inserted_total{database=\"db01\"}": 1282731.0,
                "postgres_transactions_total{database=\"db01\"}": 45678.0,
                "postgres_rows_updated_total{database=\"db01\"}": 23456.0,
                "postgres_rows_deleted_total{database=\"db01\"}": 1234.0,
                "postgres_blocks_reads_total{database=\"db01\"}": 98765.0,
                "jvm_threads_live_threads": 45.0,
                "jvm_classes_loaded_classes": 1234.0,
                "jetty_connections_current_connections": 12.0,
                "jetty_connections_bytes_in_bytes_sum": 1234567.0,
                "jetty_connections_bytes_out_bytes_sum": 987654.0,
                "system_cpu_count": 8.0
            }
            
            # Создаем prominent на основе PROMINENT_METRICS
            mock_prominent = {}
            for name, config in PROMINENT_METRICS.items():
                # Ищем значение в mock_metrics
                if name in mock_metrics:
                    mock_prominent[name] = mock_metrics[name]
                else:
                    # Если нет точного совпадения, ищем с лейблами
                    base_name = name.split('{')[0]
                    for key, value in mock_metrics.items():
                        if key.startswith(base_name + '{'):
                            mock_prominent[name] = value
                            break
                    else:
                        # Если не нашли, используем 0
                        mock_prominent[name] = 0.0
            
            print("[DEBUG] MOCK MODE: returning test data")
            return {"metrics": mock_metrics, "prominent": mock_prominent, "error": None}
        
        # Реальный режим
        raw_metrics, error = MetricsService.fetch_prometheus_metrics(METRICS_URL)
        if error:
            print(f"[DEBUG] get_metrics_data: error={error}")
            return {"metrics": {}, "prominent": {}, "error": error}
        metrics = MetricsService.normalize_metrics(raw_metrics)
        prominent = {}
        for name, config in PROMINENT_METRICS.items():
            value = None
            norm_name = MetricKeyHelper.normalize(name)
            if norm_name in metrics:
                value = metrics[norm_name]
            elif "formula" in config:
                value = eval_formula(config["formula"], metrics)
            else:
                value = get_metric(metrics, norm_name)
            if value is None:
                value = 0.0
            prominent[name] = value
        # DEBUG LOG
        print("[DEBUG] get_metrics_data: prominent=", prominent)
        print("[DEBUG] get_metrics_data: metrics keys=", list(metrics.keys()))
        print("[DEBUG] get_metrics_data: error=", error)
        return {"metrics": metrics, "prominent": prominent, "error": None}

def update_metrics():
    print("[DEBUG] update_metrics: поток сбора метрик стартовал")
    
    # В MOCK_MODE не делаем запросы к внешнему серверу
    if MOCK_MODE:
        print("[DEBUG] MOCK_MODE: skipping external metrics collection")
        while True:
            time.sleep(UPDATE_INTERVAL)
    
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
                    if should_display_metric(name, METRICS_CONFIG):
                        metrics_data["metrics"][name] = value
                        metrics_data["history"][name].append((now, value))
                metrics_data["last_updated"] = now
                metrics_data["last_error"] = None
                print(f"[DEBUG] update_metrics: metrics_data['metrics'] keys: {list(metrics_data['metrics'].keys())}")
        except Exception as e:
            with lock:
                metrics_data["last_error"] = str(e)
                print(f"[ERROR] Metrics update failed: {e}")
        time.sleep(max(0, UPDATE_INTERVAL - (time.time() - start_time)))

def get_all_metric_names():
    """
    Возвращает все имена метрик из конфигурации
    """
    names = set(PROMINENT_METRICS.keys())
    for category in METRICS_CONFIG:
        for pattern in category["metrics"]:
            # Если pattern не содержит спецсимволов, добавляем как есть
            if not any(c in pattern for c in ".*?[]{}()^$|+\\"):
                names.add(pattern)
    return names

def get_metrics_history():
    """
    Возвращает историю метрик
    """
    if MOCK_MODE:
        # Моковая история для тестирования
        import time
        now = time.time()
        mock_history = {}
        
        # Собираем все метрики, для которых нужна история
        all_metrics = set()
        
        # Добавляем метрики из prominent
        for metric_name in PROMINENT_METRICS.keys():
            all_metrics.add(metric_name)
        
        # Добавляем метрики из METRICS_CONFIG
        for category in METRICS_CONFIG:
            for metric_name in category["metrics"]:
                all_metrics.add(metric_name)
        
        # Создаем моковую историю для всех метрик
        for metric_name in all_metrics:
            mock_history[metric_name] = []
            for i in range(20):
                timestamp = now - (20 - i) * 5  # 5 секунд между точками
                value = 50 + i * 2 + (i % 3) * 10  # Имитация изменений
                mock_history[metric_name].append([timestamp, value])
        
        print(f"[DEBUG] MOCK MODE: returning test history for {len(mock_history)} metrics")
        return mock_history
    
    with lock:
        return {name: list(history) for name, history in metrics_data["history"].items()}

def start_metrics_thread():
    """
    Запускает поток обновления метрик
    """
    thread = threading.Thread(target=update_metrics, daemon=True)
    thread.start()
