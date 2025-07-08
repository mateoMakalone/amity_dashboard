import requests
import threading
import time
from collections import defaultdict, deque
from .parser import parse_metrics, should_display_metric, filter_metric, sum_metric
from .config import METRICS_URL, REQUEST_TIMEOUT, UPDATE_INTERVAL, HISTORY_LENGTH, METRICS_CONFIG, PROMINENT_METRICS

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

def update_metrics():
    while True:
        try:
            start_time = time.time()
            response = requests.get(METRICS_URL, timeout=REQUEST_TIMEOUT)
            parsed = parse_metrics(response.text)

            now = time.time()
            with lock:
                for name, value in parsed.items():
                    if should_display_metric(name, METRICS_CONFIG):
                        metrics_data["metrics"][name] = value
                        metrics_data["history"][name].append((now, value))
                metrics_data["last_updated"] = now
                metrics_data["last_error"] = None
        except Exception as e:
            with lock:
                metrics_data["last_error"] = str(e)
        time.sleep(max(0, UPDATE_INTERVAL - (time.time() - start_time)))

def get_all_metric_names():
    names = set(PROMINENT_METRICS.keys())
    for category in METRICS_CONFIG:
        for pattern in category["metrics"]:
            # Если pattern не содержит спецсимволов, добавляем как есть
            if not any(c in pattern for c in ".*?[]{}()^$|+\\"):
                names.add(pattern)
    return names

def get_metrics_data():
    with lock:
        metrics = metrics_data["metrics"].copy()
        all_names = get_all_metric_names()
        # Если была ошибка — заполняем все метрики 0.0
        if metrics_data["last_error"]:
            for name in all_names:
                metrics[name] = 0.0
        else:
            for name in all_names:
                if name not in metrics:
                    metrics[name] = 0.0

        # KPI: Transaction Pool
        tx_pool = metrics.get('tx_pool_size')
        if tx_pool is not None:
            metrics['tx_pool_size'] = tx_pool

        # KPI: API Response Time (avg)
        post_sum = filter_metric(metrics, 'jetty_server_requests_seconds_sum', {"method": "POST", "outcome": "SUCCESS", "status": "200"})
        post_count = filter_metric(metrics, 'jetty_server_requests_seconds_count', {"method": "POST", "outcome": "SUCCESS", "status": "200"})
        if post_sum is not None and post_count and post_count > 0:
            metrics['jetty_server_requests_seconds_avg'] = post_sum / post_count

        # KPI: CPU Usage
        cpu_usage = metrics.get('process_cpu_usage')
        if cpu_usage is not None:
            metrics['process_cpu_usage'] = cpu_usage

        # KPI: GC Pause (major)
        gc_pause = filter_metric(metrics, 'jvm_gc_pause_seconds_sum', {"action": "end of major GC"})
        if gc_pause is not None:
            metrics['jvm_gc_pause_seconds_sum'] = gc_pause

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

        # KPI: System Load (1m)
        sys_load = metrics.get('system_load_average_1m')
        if sys_load is not None:
            metrics['system_load_average_1m'] = sys_load

        # KPI: Jetty Request Count
        jetty_count = sum_metric(metrics, 'jetty_server_requests_seconds_count')
        if jetty_count is not None:
            metrics['jetty_server_requests_seconds_count'] = jetty_count

        # KPI: Rows Inserted
        rows_inserted = filter_metric(metrics, 'postgres_rows_inserted_total', {"database": "db01"})
        if rows_inserted is not None:
            metrics['postgres_rows_inserted_total{database="db01"}'] = rows_inserted

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

        # JVM: Live Threads
        live_threads = metrics.get('jvm_threads_live_threads')
        if live_threads is not None:
            metrics['jvm_threads_live_threads'] = live_threads

        # JVM: Loaded Classes
        loaded_classes = metrics.get('jvm_classes_loaded_classes')
        if loaded_classes is not None:
            metrics['jvm_classes_loaded_classes'] = loaded_classes

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

        # System: CPU Count
        cpu_count = metrics.get('system_cpu_count')
        if cpu_count is not None:
            metrics['system_cpu_count'] = cpu_count

        from .config import DASHBOARD_DEBUG
        if DASHBOARD_DEBUG:
            for name in all_names:
                metrics[name] = 0.0

        return {
            "metrics": metrics,
            "config": METRICS_CONFIG,
            "prominent": PROMINENT_METRICS,
            "last_updated": metrics_data["last_updated"],
            "error": metrics_data["last_error"]
        }

def get_metrics_history():
    with lock:
        # Возвращаем историю для всех метрик: {name: [(timestamp, value), ...], ...}
        return {name: list(history) for name, history in metrics_data["history"].items()}

def start_metrics_thread():
    thread = threading.Thread(target=update_metrics, daemon=True)
    thread.start()
