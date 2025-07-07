import requests
import threading
import time
from collections import defaultdict, deque
from .parser import parse_metrics, should_display_metric
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

def get_kpi_metrics(parsed):
    kpi = {}
    # 1. tx_pool_size
    if 'tx_pool_size' in parsed:
        kpi['tx_pool_size'] = parsed['tx_pool_size']
    # 2. jetty_post_avg_time (sum/count)
    post_sum = None
    post_count = None
    for k, v in parsed.items():
        if k.startswith('jetty_server_requests_seconds_sum') and 'method="POST"' in k:
            post_sum = v
        if k.startswith('jetty_server_requests_seconds_count') and 'method="POST"' in k:
            post_count = v
    if post_sum is not None and post_count:
        kpi['jetty_post_avg_time'] = post_sum / post_count if post_count else 0.0
    # 3. process_cpu_usage
    if 'process_cpu_usage' in parsed:
        kpi['process_cpu_usage'] = parsed['process_cpu_usage']
    # 4. postgres_locks{database="db01"}
    for k, v in parsed.items():
        if k.startswith('postgres_locks{') and 'database="db01"' in k:
            kpi['postgres_locks{database="db01"}'] = v
    # 5. jvm_gc_pause_seconds_sum (minor+major)
    gc_sum = 0.0
    found_gc = False
    for k, v in parsed.items():
        if k.startswith('jvm_gc_pause_seconds_sum{') and (
            'action="end of minor GC"' in k or 'action="end of major GC"' in k):
            gc_sum += v
            found_gc = True
    if found_gc:
        kpi['jvm_gc_pause_seconds_sum'] = gc_sum
    # 6. postgres_connections{database="db01"}
    for k, v in parsed.items():
        if k.startswith('postgres_connections{') and 'database="db01"' in k:
            kpi['postgres_connections{database="db01"}'] = v
    # 7. jvm_memory_used_bytes{area="heap",id="Tenured Gen"} и max
    heap_used = None
    heap_max = None
    for k, v in parsed.items():
        if k.startswith('jvm_memory_used_bytes{') and 'area="heap"' in k and 'id="Tenured Gen"' in k:
            heap_used = v
        if k.startswith('jvm_memory_max_bytes{') and 'area="heap"' in k and 'id="Tenured Gen"' in k:
            heap_max = v
    if heap_used is not None:
        kpi['jvm_memory_used_bytes{area="heap",id="Tenured Gen"}'] = heap_used
        if heap_max:
            kpi['jvm_memory_used_bytes{area="heap",id="Tenured Gen"}_max'] = heap_max
    # 8. system_load_average_1m
    if 'system_load_average_1m' in parsed:
        kpi['system_load_average_1m'] = parsed['system_load_average_1m']
    # 9. jetty_server_requests_seconds_count{method="POST",outcome="SUCCESS",status="200",}
    for k, v in parsed.items():
        if k.startswith('jetty_server_requests_seconds_count{') and 'method="POST"' in k and 'outcome="SUCCESS"' in k and 'status="200"' in k:
            kpi['jetty_server_requests_seconds_count{method="POST",outcome="SUCCESS",status="200",}'] = v
    # 10. postgres_rows_inserted_total{database="db01"}
    for k, v in parsed.items():
        if k.startswith('postgres_rows_inserted_total{') and 'database="db01"' in k:
            kpi['postgres_rows_inserted_total{database="db01"}'] = v
    # 11. postgres_blocks_reads_total{database="db01"}
    for k, v in parsed.items():
        if k.startswith('postgres_blocks_reads_total{') and 'database="db01"' in k:
            kpi['postgres_blocks_reads_total{database="db01"}'] = v
    # 12. jvm_threads_live_threads
    if 'jvm_threads_live_threads' in parsed:
        kpi['jvm_threads_live_threads'] = parsed['jvm_threads_live_threads']
    # 13. jvm_classes_loaded_classes
    if 'jvm_classes_loaded_classes' in parsed:
        kpi['jvm_classes_loaded_classes'] = parsed['jvm_classes_loaded_classes']
    return kpi

def get_metrics_data():
    with lock:
        parsed = metrics_data["metrics"]
        kpi = get_kpi_metrics(parsed)
        # Обновляем history для KPI-метрик
        for k, v in kpi.items():
            metrics_data["history"][k].append((metrics_data["last_updated"], v))
        # Фильтруем history по should_display_metric
        from .parser import should_display_metric
        filtered_history = {name: list(history) for name, history in metrics_data["history"].items() if should_display_metric(name, METRICS_CONFIG)}
        return {
            "metrics": parsed,
            "kpi": kpi,
            "history": filtered_history,
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

# Очищаем историю при старте, чтобы убрать старые игнорируемые метрики
metrics_data["history"].clear()
