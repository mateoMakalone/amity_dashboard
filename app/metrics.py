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
            # Моковые данные, максимально приближённые к реальным prod-ответам
            mock_metrics = {
                "jetty_server_requests_seconds_count": 270090.0,
                "jetty_server_requests_seconds_count{method=\"GET\",outcome=\"SUCCESS\",status=\"200\"}": 270090.0,
                "jetty_server_requests_seconds_count{method=\"POST\",outcome=\"SERVER_ERROR\",status=\"500\"}": 1.0,
                "jetty_server_requests_seconds_count{method=\"POST\",outcome=\"SUCCESS\",status=\"200\"}": 21253.0,
                "jetty_server_requests_seconds_sum": 45577.570267428,
                "jetty_server_requests_seconds_sum{method=\"GET\",outcome=\"SUCCESS\",status=\"200\"}": 45577.570267428,
                "jetty_server_requests_seconds_sum{method=\"POST\",outcome=\"SERVER_ERROR\",status=\"500\"}": 1.722175775,
                "jetty_server_requests_seconds_sum{method=\"POST\",outcome=\"SUCCESS\",status=\"200\"}": 49272.573626984,
                "jvm_gc_pause_seconds_sum": 2.065,
                "jvm_memory_used_bytes": 24038272.0,
                "postgres_connections": 66.0,
                "postgres_locks": 1.0,
                "postgres_rows_inserted_total": 1336082.0,
                "system_cpu_usage": 0.06987864285714286,
                "system_load_average_1m": 0.21,
                "tx_pool_size": 0.0
            }
            # prominent формируется по тем же правилам, что и в проде
            mock_prominent = {}
            for name, config in PROMINENT_METRICS.items():
                value = None
                if name in mock_metrics:
                    value = mock_metrics[name]
                elif "formula" in config:
                    value = eval_formula(config["formula"], mock_metrics)
                else:
                    base_name = name.split('{')[0]
                    for key, v in mock_metrics.items():
                        if key.startswith(base_name + '{'):
                            value = v
                            break
                if value is None:
                    value = 0.0
                mock_prominent[name] = value
            print("[DEBUG] MOCK MODE: returning prod-like test data")
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
                # === PATCH: добавляем историю для KPI-метрик (PROMINENT_METRICS) ===
                for kpi_name, config in PROMINENT_METRICS.items():
                    value = None
                    norm_name = MetricKeyHelper.normalize(kpi_name)
                    if norm_name in metrics_data["metrics"]:
                        value = metrics_data["metrics"][norm_name]
                    elif "formula" in config:
                        value = eval_formula(config["formula"], metrics_data["metrics"])
                    else:
                        value = get_metric(metrics_data["metrics"], norm_name)
                    if value is None:
                        value = 0.0
                    metrics_data["history"][kpi_name].append((now, value))
                # === END PATCH ===
                # === NEW PATCH: инициализация истории для всех метрик из конфигов ===
                all_metric_names = set()
                for category in METRICS_CONFIG:
                    for pattern in category["metrics"]:
                        all_metric_names.add(pattern)
                all_metric_names.update(PROMINENT_METRICS.keys())
                for metric_name in all_metric_names:
                    if metric_name not in metrics_data["history"] or len(metrics_data["history"][metric_name]) == 0:
                        metrics_data["history"][metric_name].append((now, 0.0))
                # === END NEW PATCH ===
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
        import random
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
        
        # Базовые значения для разных типов метрик
        base_values = {
            # API Response Time (avg) - в секундах, обычно 0.01-0.1
            'jetty_server_requests_seconds_avg': {'base': 0.045, 'range': 0.02, 'min': 0.01},
            # GET Response Time (avg) - в секундах, обычно 0.01-0.1
            'jetty_server_requests_seconds_avg_get': {'base': 0.032, 'range': 0.01, 'min': 0.02},
            # POST Response Time (avg) - в секундах, обычно 0.05-0.2
            'jetty_server_requests_seconds_avg_post': {'base': 0.078, 'range': 0.05, 'min': 0.06},
            # Jetty Requests Count - счетчик, растет
            'jetty_server_requests_seconds_count': {'base': 1234, 'range': 200, 'min': 1000},
            # GC Pause - в секундах, обычно 0.1-50
            'jvm_gc_pause_seconds_sum': {'base': 21.743, 'range': 5, 'min': 15},
            # CPU Usage - процент, 0-1
            'system_cpu_usage': {'base': 0.75, 'range': 0.2, 'min': 0.3},
            # System Load - обычно 0.1-5
            'system_load_average_1m': {'base': 0.82, 'range': 0.3, 'min': 0.4},
            # Transaction Pool - целые числа
            'tx_pool_size': {'base': 150, 'range': 30, 'min': 100},
            # PostgreSQL connections
            'postgres_connections': {'base': 68, 'range': 15, 'min': 50},
            # PostgreSQL locks
            'postgres_locks': {'base': 1, 'range': 3, 'min': 0},
            # Memory usage - в байтах, большие числа
            'jvm_memory_used_bytes': {'base': 192521736, 'range': 50000000, 'min': 150000000},
            # Rows inserted - счетчик, растет
            'postgres_rows_inserted_total': {'base': 1282731, 'range': 100000, 'min': 1200000},
        }
        
        # Создаем моковую историю для всех метрик
        for metric_name in all_metrics:
            mock_history[metric_name] = []
            
            # Определяем базовые параметры для метрики
            if metric_name in base_values:
                config = base_values[metric_name]
                base_val = config['base']
                range_val = config['range']
                min_val = config['min']
            else:
                # Для неизвестных метрик используем общие параметры
                base_val = 100
                range_val = 50
                min_val = 50
            
            # Создаем историю с реалистичными изменениями
            current_val = base_val
            for i in range(20):
                timestamp = now - (20 - i) * 5  # 5 секунд между точками
                
                # Добавляем случайные колебания
                change = (random.random() - 0.5) * range_val * 0.1  # ±10% от диапазона
                current_val += change
                
                # Обеспечиваем минимальные значения
                current_val = max(current_val, min_val)
                
                # Для счетчиков (count, total) значения только растут
                if 'count' in metric_name or 'total' in metric_name:
                    current_val = max(current_val, base_val + i * range_val * 0.05)
                
                mock_history[metric_name].append([timestamp, round(current_val, 3)])
        
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
