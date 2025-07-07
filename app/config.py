DASHBOARD_DEBUG = True  # Меняйте на True для включения debug-режима
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
        "title": "Tx Pool Size",
        "unit": "",
        "color": "#2980b9",
        "format": "fixed0",
        "priority": 10,
        "warning": 1000,
        "critical": 5000,
        "description": "Кол-во необработанных транзакций в пуле ожидания. Рост → перегрузка ноды или консенсуса."
    },
    "jetty_post_avg_time": {
        "title": "POST Avg Time",
        "unit": "сек",
        "color": "#8e44ad",
        "format": "fixed2",
        "priority": 9,
        "warning": 3.0,
        "critical": 5.0,
        "description": "Среднее время ответа на POST-запросы. Рост = угроза отказа."
    },
    "process_cpu_usage": {
        "title": "CPU Usage",
        "unit": "%",
        "color": "#e67e22",
        "format": "fixed2",
        "priority": 8,
        "warning": 0.85,
        "critical": 0.95,
        "description": "Использование CPU конкретным процессом. Рост указывает на узкое место или утечку."
    },
    "postgres_locks{database=\"db01\"}": {
        "title": "Postgres Locks",
        "unit": "",
        "color": "#c0392b",
        "format": "fixed0",
        "priority": 7,
        "warning": 10,
        "critical": 50,
        "description": "Кол-во активных блокировок в PostgreSQL. Рост может тормозить транзакции."
    },
    "jvm_gc_pause_seconds_sum": {
        "title": "GC Pause Time (sum)",
        "unit": "сек",
        "color": "#16a085",
        "format": "fixed2",
        "priority": 6,
        "warning": 1.0,
        "critical": 3.0,
        "description": "Общее время пауз GC. Рост → лаги, сбои, паузы JVM."
    },
    "postgres_connections{database=\"db01\"}": {
        "title": "Postgres Connections",
        "unit": "",
        "color": "#34495e",
        "format": "fixed0",
        "priority": 5,
        "warning": 100,
        "critical": 150,
        "description": "Текущее количество соединений к БД. При превышении лимита — падение соединений."
    },
    "jvm_memory_used_bytes{area=\"heap\",id=\"Tenured Gen\"}": {
        "title": "JVM Heap (Tenured Gen)",
        "unit": "байт",
        "color": "#9b59b6",
        "format": "fixed0",
        "priority": 4,
        "description": "Использование памяти JVM heap (долгоживущие объекты). При росте → давление на GC / OOM."
        # warning/critical вычисляются на фронте по max
    },
    "system_load_average_1m": {
        "title": "System Load 1m",
        "unit": "",
        "color": "#f39c12",
        "format": "fixed2",
        "priority": 3,
        "warning": 2.0,
        "critical": 4.0,
        "description": "Средняя загрузка CPU за 1 мин. Рост = CPU/IO перегрузка."
    },
    "jetty_server_requests_seconds_count{method=\"POST\",outcome=\"SUCCESS\",status=\"200\",}": {
        "title": "POST Success Count",
        "unit": "",
        "color": "#27ae60",
        "format": "roundFormat",
        "priority": 2,
        "description": "Общее число успешных POST-запросов. Показывает нагрузку на API."
    },
    "postgres_rows_inserted_total{database=\"db01\"}": {
        "title": "Rows Inserted",
        "unit": "",
        "color": "#2980b9",
        "format": "roundFormat",
        "priority": 2,
        "description": "Количество вставленных строк. Высокие значения → потенциальная нагрузка."
    },
    "postgres_blocks_reads_total{database=\"db01\"}": {
        "title": "Blocks Read",
        "unit": "",
        "color": "#7f8c8d",
        "format": "roundFormat",
        "priority": 2,
        "description": "Чтения с диска. Рост → проблемы с планировкой/индексами."
    },
    "jvm_threads_live_threads": {
        "title": "JVM Live Threads",
        "unit": "",
        "color": "#2ecc71",
        "format": "fixed0",
        "priority": 1,
        "description": "Активные потоки в JVM. Рост = утечка потоков или стресс."
    },
    "jvm_classes_loaded_classes": {
        "title": "JVM Loaded Classes",
        "unit": "",
        "color": "#e67e22",
        "format": "fixed0",
        "priority": 1,
        "description": "Кол-во загруженных классов. Рост → потенциальная утечка classloader’ов."
    }
}

IGNORE_METRICS = [
    # PostgreSQL
    "postgres_buffers_clean_total",
    "postgres_rows_dead",
    "postgres_blocks_hits_total",
    "postgres_checkpoints_requested_total",
    "postgres_size",
    # JVM
    "jvm_buffer_count_buffers",
    "jvm_buffer_memory_used_bytes",
    "jvm_buffer_total_capacity_bytes",
    "jvm_classes_unloaded_classes_total",
    "jvm_gc_live_data_size_bytes",
    "jvm_memory_committed_bytes",
    "jvm_memory_max_bytes",
    # Для jvm_memory_used_bytes с area=nonheap — фильтровать по лейблу на фронте
    # Jetty
    "jetty_connections_bytes_in_bytes_max",
    "jetty_connections_bytes_out_bytes_max",
    "jetty_connections_messages_in_messages_total",
    "jetty_connections_messages_out_messages_total",
    "jetty_server_dispatches_open_seconds_max",
    "jetty_server_async_waits_operations",
    "jetty_server_async_dispatches_total",
    "jetty_server_async_expires_total",
    # Новое игнорируемое
    "jetty_connections_bytes_in_bytes_count"
]
