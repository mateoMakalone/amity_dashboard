import requests
import threading
import time
import os
from collections import defaultdict, deque
from .parser import parse_metrics, should_display_metric, filter_metric, sum_metric
from .config import METRICS_URL, REQUEST_TIMEOUT, UPDATE_INTERVAL, HISTORY_LENGTH, METRICS_CONFIG, PROMINENT_METRICS, DEBUG_MODE, INITIAL_METRICS

HISTORY_SECONDS = 3600  # 1 час
HISTORY_POINTS = int(HISTORY_SECONDS / UPDATE_INTERVAL)

metrics_data = {
    "metrics": {},
    # history: {metric_name: deque([(timestamp, value), ...], maxlen=HISTORY_POINTS)}
    "history": defaultdict(lambda: deque(maxlen=HISTORY_POINTS)),
    "last_updated": 0,
    "last_error": None
}

lock = threading.Lock()

def eval_formula(formula: str, metrics: dict) -> float:
    """
    Вычисляет формулу с поддержкой sum() для метрик с лейблами
    """
    def sum_expr(name):
        # Убираем {...} из имени метрики для поиска
        base_name = name.split('{')[0]
        return sum(val for key, val in metrics.items() if key.startswith(base_name + '{'))
    
    try:
        # Заменяем sum(...) на sum_expr(...)
        modified_formula = formula.replace("sum(", "sum_expr(")
        result = eval(modified_formula, {"sum_expr": sum_expr})
        if isinstance(result, float) and (result == float('inf') or result != result):  # inf или nan
            return 0.0
        return result
    except ZeroDivisionError:
        return 0.0
    except Exception as e:
        print(f"[ERROR] Failed to eval formula '{formula}': {e}")
        return 0.0

def load_mock_metrics():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        mock_path = os.path.join(base_dir, "mock_metrics.txt")
        with open(mock_path, "r", encoding="utf-8") as f:
            raw = f.read()
        parsed = parse_metrics(raw)
        now = time.time()
        metrics = {}
        for name, value in parsed.items():
            if should_display_metric(name, METRICS_CONFIG):
                metrics[name] = value
        return metrics, now
    except Exception as e:
        print(f"[ERROR] Failed to load mock_metrics.txt: {e}")
        return {}, time.time()

def prepare_metrics_data():
    """
    Подготавливает данные метрик с вычислением формул и инициализацией
    """
    with lock:
        metrics = metrics_data["metrics"].copy()
        
        # Инициализируем все метрики значением 0.0
        for name in INITIAL_METRICS:
            if name not in metrics:
                metrics[name] = 0.0
            if name not in metrics_data["history"]:
                metrics_data["history"][name].append((time.time(), 0.0))
        
        # Вычисляем формулы для prominent метрик
        for name, config in PROMINENT_METRICS.items():
            if "formula" in config:
                try:
                    value = eval_formula(config["formula"], metrics)
                    metrics[name] = value
                    # Обновляем историю
                    if name in metrics_data["history"]:
                        metrics_data["history"][name].append((time.time(), value))
                    else:
                        metrics_data["history"][name] = deque([(time.time(), value)], maxlen=HISTORY_POINTS)
                except Exception as e:
                    print(f"[ERROR] Failed to compute formula for {name}: {e}")
                    metrics[name] = 0.0
        
        # Обрабатываем специальные случаи для метрик с лейблами
        # KPI: DB Connections
        db_conn = filter_metric(metrics, 'postgres_connections', {"database": "db01"})
        if db_conn is not None:
            metrics['postgres_connections{database="db01"}'] = db_conn
        
        # KPI: Postgres Locks
        db_locks = filter_metric(metrics, 'postgres_locks', {"database": "db01"})
        if db_locks is not None:
            metrics['postgres_locks{database="db01"}'] = db_locks
        
        # KPI: JVM Memory Used (heap)
        heap_mem = filter_metric(metrics, 'jvm_memory_used_bytes', {"area": "heap", "id": "Tenured Gen"})
        if heap_mem is not None:
            metrics['jvm_memory_used_bytes{area="heap",id="Tenured Gen"}'] = heap_mem
        
        # Transactions: Transactions Total
        tx_total = filter_metric(metrics, 'postgres_transactions_total', {"database": "db01"})
        if tx_total is not None:
            metrics['postgres_transactions_total{database="db01"}'] = tx_total
        
        # Transactions: Rows Updated
        rows_updated = filter_metric(metrics, 'postgres_rows_updated_total', {"database": "db01"})
        if rows_updated is not None:
            metrics['postgres_rows_updated_total{database="db01"}'] = rows_updated
        
        # Transactions: Rows Deleted
        rows_deleted = filter_metric(metrics, 'postgres_rows_deleted_total', {"database": "db01"})
        if rows_deleted is not None:
            metrics['postgres_rows_deleted_total{database="db01"}'] = rows_deleted
        
        # PostgreSQL: Blocks Read
        blocks_read = filter_metric(metrics, 'postgres_blocks_reads_total', {"database": "db01"})
        if blocks_read is not None:
            metrics['postgres_blocks_reads_total{database="db01"}'] = blocks_read
        
        # KPI: Rows Inserted
        rows_inserted = filter_metric(metrics, 'postgres_rows_inserted_total', {"database": "db01"})
        if rows_inserted is not None:
            metrics['postgres_rows_inserted_total{database="db01"}'] = rows_inserted
        
        # Jetty: Current Connections
        jetty_conn = filter_metric(metrics, 'jetty_connections_current_connections', {"connector_name": "unnamed"})
        if jetty_conn is not None:
            metrics['jetty_connections_current_connections{connector_name="unnamed"}'] = jetty_conn
        
        # Jetty: Bytes In
        bytes_in = filter_metric(metrics, 'jetty_connections_bytes_in_bytes_sum', {"connector_name": "unnamed"})
        if bytes_in is not None:
            metrics['jetty_connections_bytes_in_bytes_sum{connector_name="unnamed"}'] = bytes_in
        
        # Jetty: Bytes Out
        bytes_out = filter_metric(metrics, 'jetty_connections_bytes_out_bytes_sum', {"connector_name": "unnamed"})
        if bytes_out is not None:
            metrics['jetty_connections_bytes_out_bytes_sum{connector_name="unnamed"}'] = bytes_out
        
        return metrics

def update_metrics():
    """
    Обновляет метрики в зависимости от режима (debug/prod)
    """
    while True:
        try:
            start_time = time.time()
            
            if DEBUG_MODE:
                # Debug режим: читаем из mock_metrics.txt
                try:
                    with open("mock_metrics.txt", "r", encoding="utf-8") as f:
                        raw = f.read()
                    parsed = parse_metrics(raw)
                except Exception as e:
                    print(f"[ERROR] Failed to read mock_metrics.txt: {e}")
                    parsed = {}
            else:
                # Prod режим: запрашиваем с сервера
                response = requests.get(METRICS_URL, timeout=REQUEST_TIMEOUT)
                parsed = parse_metrics(response.text)

            now = time.time()
            with lock:
                # Обновляем метрики
                for name, value in parsed.items():
                    if should_display_metric(name, METRICS_CONFIG):
                        metrics_data["metrics"][name] = value
                        metrics_data["history"][name].append((now, value))
                
                metrics_data["last_updated"] = now
                metrics_data["last_error"] = None
                
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

def get_metrics_data():
    """
    Возвращает подготовленные данные метрик
    """
    if DEBUG_MODE:
        metrics, now = load_mock_metrics()
        # Инициализация всех метрик и history
        for name in INITIAL_METRICS:
            if name not in metrics:
                metrics[name] = 0.0
        # Вычисляем формулы для prominent метрик
        for name, config in PROMINENT_METRICS.items():
            if "formula" in config:
                try:
                    value = eval_formula(config["formula"], metrics)
                    metrics[name] = value
                except Exception as e:
                    print(f"[ERROR] Failed to compute formula for {name}: {e}")
                    metrics[name] = 0.0
        # Специальные метрики с лейблами (пример)
        db_conn = filter_metric(metrics, 'postgres_connections', {"database": "db01"})
        if db_conn is not None:
            metrics['postgres_connections{database="db01"}'] = db_conn
        db_locks = filter_metric(metrics, 'postgres_locks', {"database": "db01"})
        if db_locks is not None:
            metrics['postgres_locks{database="db01"}'] = db_locks
        heap_mem = filter_metric(metrics, 'jvm_memory_used_bytes', {"area": "heap", "id": "Tenured Gen"})
        if heap_mem is not None:
            metrics['jvm_memory_used_bytes{area="heap",id="Tenured Gen"}'] = heap_mem
        tx_total = filter_metric(metrics, 'postgres_transactions_total', {"database": "db01"})
        if tx_total is not None:
            metrics['postgres_transactions_total{database="db01"}'] = tx_total
        rows_updated = filter_metric(metrics, 'postgres_rows_updated_total', {"database": "db01"})
        if rows_updated is not None:
            metrics['postgres_rows_updated_total{database="db01"}'] = rows_updated
        rows_deleted = filter_metric(metrics, 'postgres_rows_deleted_total', {"database": "db01"})
        if rows_deleted is not None:
            metrics['postgres_rows_deleted_total{database="db01"}'] = rows_deleted
        blocks_read = filter_metric(metrics, 'postgres_blocks_reads_total', {"database": "db01"})
        if blocks_read is not None:
            metrics['postgres_blocks_reads_total{database="db01"}'] = blocks_read
        rows_inserted = filter_metric(metrics, 'postgres_rows_inserted_total', {"database": "db01"})
        if rows_inserted is not None:
            metrics['postgres_rows_inserted_total{database="db01"}'] = rows_inserted
        jetty_conn = filter_metric(metrics, 'jetty_connections_current_connections', {"connector_name": "unnamed"})
        if jetty_conn is not None:
            metrics['jetty_connections_current_connections{connector_name="unnamed"}'] = jetty_conn
        bytes_in = filter_metric(metrics, 'jetty_connections_bytes_in_bytes_sum', {"connector_name": "unnamed"})
        if bytes_in is not None:
            metrics['jetty_connections_bytes_in_bytes_sum{connector_name="unnamed"}'] = bytes_in
        bytes_out = filter_metric(metrics, 'jetty_connections_bytes_out_bytes_sum', {"connector_name": "unnamed"})
        if bytes_out is not None:
            metrics['jetty_connections_bytes_out_bytes_sum{connector_name="unnamed"}'] = bytes_out
        # Формируем ответ
        return {
            "metrics": metrics,
            "config": METRICS_CONFIG,
            "prominent": PROMINENT_METRICS,
            "last_updated": now,
            "error": None
        }
    # --- PROD режим ---
    with lock:
        metrics = prepare_metrics_data()
        if metrics_data["last_error"]:
            for name in INITIAL_METRICS:
                metrics[name] = 0.0
        return {
            "metrics": metrics,
            "config": METRICS_CONFIG,
            "prominent": PROMINENT_METRICS,
            "last_updated": metrics_data["last_updated"],
            "error": metrics_data["last_error"]
        }

def get_metrics_history():
    """
    Возвращает историю метрик
    """
    if DEBUG_MODE:
        # Для простоты: возвращаем плоскую историю (только последние значения)
        metrics, now = load_mock_metrics()
        history = {}
        for name in INITIAL_METRICS:
            v = metrics.get(name, 0.0)
            # 60 точек по 1 минуте назад
            history[name] = [[now - i * 60, v] for i in reversed(range(60))]
        return history
    # --- PROD режим ---
    with lock:
        # Возвращаем историю для всех метрик: {name: [(timestamp, value), ...], ...}
        return {name: list(history) for name, history in metrics_data["history"].items()}

def start_metrics_thread():
    """
    Запускает поток обновления метрик
    """
    if not DEBUG_MODE:
        # В prod режиме запускаем поток обновления
        thread = threading.Thread(target=update_metrics, daemon=True)
        thread.start()
    else:
        # В debug режиме делаем одно обновление при старте
        try:
            with open("mock_metrics.txt", "r", encoding="utf-8") as f:
                raw = f.read()
            parsed = parse_metrics(raw)
            
            now = time.time()
            with lock:
                for name, value in parsed.items():
                    if should_display_metric(name, METRICS_CONFIG):
                        metrics_data["metrics"][name] = value
                        metrics_data["history"][name].append((now, value))
                metrics_data["last_updated"] = now
                metrics_data["last_error"] = None
        except Exception as e:
            print(f"[ERROR] Failed to load mock data: {e}")
            with lock:
                metrics_data["last_error"] = str(e)
