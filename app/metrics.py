import threading
import time
import os
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
        for config in KPI_METRICS_CONFIG:
            all_metrics.add(config["id"])
        
        # Добавляем метрики из SECTIONS
        for category_name, metrics_list in SECTIONS.items():
            for metric_name in metrics_list:
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
