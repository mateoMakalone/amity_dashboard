METRICS_URL = "http://ваш-эндпоинт/metrics"
UPDATE_INTERVAL = 1.0
REQUEST_TIMEOUT = 3.0
HISTORY_LENGTH = 60

METRICS_CONFIG = [
    {
        "category": "Transactions",
        "metrics": ["tx_pool_size"],
        "display": "counter",
        "color": "#8e44ad",
        "priority": 1
    },
    {
        "category": "PostgreSQL",
        "metrics": [
            "postgres_checkpoints_.*",
            "postgres_rows_.*",
            "postgres_buffers_.*",
            "postgres_blocks_.*",
            "postgres_size",
            "postgres_transactions_total",
            "postgres_locks"
        ],
        "display": "compact",
        "color": "#3498db",
        "priority": 2
    },
    {
        "category": "JVM",
        "metrics": [
            "jvm_memory_.*",
            "jvm_buffer_.*",
            "jvm_gc_.*",
            "jvm_threads_.*",
            "jvm_classes_.*"
        ],
        "display": "compact",
        "color": "#27ae60",
        "priority": 3
    },
    {
        "category": "Jetty",
        "metrics": ["jetty_.*"],
        "display": "compact",
        "color": "#e74c3c",
        "priority": 4
    },
    {
        "category": "System",
        "metrics": [
            "system_cpu_.*",
            "system_load_.*",
            "process_cpu_usage"
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
        "color": "#8e44ad",
        "format": "fixed0"
    },
    "postgres_connections": {
        "title": "DB Connections", 
        "unit": "",
        "color": "#3498db",
        "format": "fixed0"
    },
    "jetty_server_requests_seconds_count{method=\"POST\",outcome=\"SUCCESS\",status=\"200\",}": {
        "title": "POST Requests",
        "unit": "",
        "color": "#e74c3c",
        "format": "roundFormat"
    },
    "jetty_server_requests_seconds_sum{method=\"POST\",outcome=\"SUCCESS\",status=\"200\",}": {
        "title": "POST Time Total",
        "unit": "s",
        "color": "#d35400",
        "format": "fixed2"
    },
    "jetty_server_requests_seconds_count{method=\"GET\",outcome=\"SUCCESS\",status=\"200\",}": {
        "title": "GET Requests",
        "unit": "",
        "color": "#16a085",
        "format": "roundFormat"
    }
}
