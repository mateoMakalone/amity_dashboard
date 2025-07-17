# Удалён DEBUG_MODE и print

# Моковый режим для тестирования фронта
MOCK_MODE = True
print(f"[INFO] MOCK MODE = {MOCK_MODE}")

METRICS_URL = "http://server:5110/metrics"
UPDATE_INTERVAL = 1.0
REQUEST_TIMEOUT = 3.0
HISTORY_LENGTH = 60

METRICS_CONFIG = [
    {
        "category": "Transactions",
        "metrics": [
            'postgres_transactions_total{database="db01"}',
            'postgres_rows_updated_total{database="db01"}',
            'postgres_rows_deleted_total{database="db01"}'
        ],
        "display": "counter",
        "color": "#8e44ad",
        "priority": 1
    },
    {
        "category": "PostgreSQL",
        "metrics": [
            'postgres_connections{database="db01"}',
            'postgres_locks{database="db01"}',
            'postgres_blocks_reads_total{database="db01"}',
            'postgres_rows_inserted_total{database="db01"}',
            'postgres_rows_updated_total',
            'postgres_transactions_total'
        ],
        "display": "compact",
        "color": "#3498db",
        "priority": 2
    },
    {
        "category": "JVM",
        "metrics": [
            'jvm_gc_pause_seconds_sum',
            'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}',
            'jvm_threads_live_threads',
            'jvm_classes_loaded_classes'
        ],
        "display": "compact",
        "color": "#27ae60",
        "priority": 3
    },
    {
        "category": "Jetty",
        "metrics": [
            'jetty_server_requests_seconds_avg',
            'jetty_get_avg_time',
            'jetty_post_avg_time',
            'jetty_connections_current_connections',
            'jetty_connections_bytes_in_bytes_sum',
            'jetty_connections_bytes_out_bytes_sum'
        ],
        "display": "compact",
        "color": "#e74c3c",
        "priority": 4
    },
    {
        "category": "System",
        "metrics": [
            'process_cpu_usage',
            'system_load_average_1m',
            'system_cpu_count'
        ],
        "display": "compact",
        "color": "#f39c12",
        "priority": 5
    }
]

PROMINENT_METRICS = {
    "tx_pool_size": {
        "title": "Transaction Pool",
        "unit": "",
        "format": "fixed0",
        "thresholds": {"warning": 1000, "critical": 5000}
    },
    "jetty_server_requests_seconds_avg": {
        "title": "API Response Time (avg)",
        "unit": "s",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.0}
    },
    "jetty_get_avg_time": {
        "title": "GET Avg Response Time",
        "unit": "s",
        "format": "fixed3",
        "thresholds": {"warning": 0.3, "critical": 0.8}
    },
    "jetty_post_avg_time": {
        "title": "POST Avg Response Time",
        "unit": "s",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.2}
    },
    "system_cpu_usage": {
        "title": "CPU Usage",
        "unit": "%",
        "format": "fixed2",
        "thresholds": {"warning": 0.85, "critical": 0.95}
    },
    "postgres_locks": {
        "title": "Postgres Locks",
        "unit": "",
        "format": "fixed0",
        "thresholds": {"warning": 10, "critical": 50}
    },
    "jvm_gc_pause_seconds_sum": {
        "title": "GC Pause (s)",
        "unit": "s",
        "format": "fixed2",
        "thresholds": {"warning": 1.0, "critical": 3.0}
    },
    "postgres_connections": {
        "title": "DB Connections",
        "unit": "",
        "format": "fixed0",
        "thresholds": {"warning": 100, "critical": 150}
    },
    "jvm_memory_used_bytes": {
        "title": "JVM Memory Used",
        "unit": "B",
        "format": "fixed0",
        "thresholds": {"warning": 0.75, "critical": 0.9, "isRatio": True}
    },
    "system_load_average_1m": {
        "title": "System Load (1m)",
        "unit": "",
        "format": "fixed2",
        "thresholds": {"warning": 2.0, "critical": 4.0}
    },
    "jetty_server_requests_seconds_count": {
        "title": "Jetty Requests Count",
        "unit": "",
        "format": "fixed0"
    },
    "postgres_rows_inserted_total": {
        "title": "Rows Inserted",
        "unit": "",
        "format": "fixed0"
    }
}

# Список всех метрик для инициализации
INITIAL_METRICS = [
    "tx_pool_size",
    "jetty_server_requests_seconds_avg",
    "jetty_server_requests_seconds_avg_get",
    "jetty_server_requests_seconds_avg_post",
    "system_cpu_usage",
    "postgres_locks",
    "jvm_gc_pause_seconds_sum",
    "postgres_connections",
    "jvm_memory_used_bytes",
    "system_load_average_1m",
    "jetty_server_requests_seconds_count",
    "postgres_rows_inserted_total",
    'postgres_transactions_total{database="db01"}',
    'postgres_rows_updated_total{database="db01"}',
    'postgres_rows_deleted_total{database="db01"}',
    'postgres_blocks_reads_total{database="db01"}',
    'jvm_threads_live_threads',
    'jvm_classes_loaded_classes',
    'jetty_connections_current_connections',
    'jetty_connections_bytes_in_bytes_sum',
    'jetty_connections_bytes_out_bytes_sum',
    'system_cpu_count'
]
