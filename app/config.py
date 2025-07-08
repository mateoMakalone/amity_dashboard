DASHBOARD_DEBUG = False  # Меняйте на True для включения debug-режима
METRICS_URL = "http://server:5110/metrics"
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
        "color": "#145a32",
        "format": "fixed0"
    },
    "jetty_server_requests_seconds_avg": {
        "title": "Jetty Avg Response Time",
        "unit": "s",
        "color": "#145a32",
        "format": "fixed2"
    },
    "process_cpu_usage": {
        "title": "CPU Usage",
        "unit": "%",
        "color": "#145a32",
        "format": "fixed2"
    },
    "postgres_locks": {
        "title": "Postgres Locks",
        "unit": "",
        "color": "#145a32",
        "format": "fixed0"
    },
    "jvm_gc_pause_seconds_sum": {
        "title": "JVM GC Pause (s)",
        "unit": "s",
        "color": "#145a32",
        "format": "fixed2"
    },
    "postgres_connections": {
        "title": "DB Connections",
        "unit": "",
        "color": "#145a32",
        "format": "fixed0"
    },
    "jvm_memory_used_bytes": {
        "title": "JVM Memory Used",
        "unit": "B",
        "color": "#145a32",
        "format": "fixed0"
    },
    "system_load1": {
        "title": "System Load 1m",
        "unit": "",
        "color": "#145a32",
        "format": "fixed2"
    },
    "jetty_server_requests_seconds_count": {
        "title": "Jetty Requests Count",
        "unit": "",
        "color": "#145a32",
        "format": "fixed0"
    },
    "postgres_rows_inserted_total": {
        "title": "Rows Inserted",
        "unit": "",
        "color": "#145a32",
        "format": "fixed0"
    }
}
