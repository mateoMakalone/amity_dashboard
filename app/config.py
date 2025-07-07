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
        "title": "Транзакции в пуле ожидания",
        "priority": 10,
        "description": "Рост = перегрузка сети / задержка обработки",
        "why": "Рост значения — признак перегрузки сети или задержки обработки транзакций.",
        "unit": "",
        "format": "fixed0",
        "warning": 1000.0,
        "critical": 5000.0
    },
    "jetty_server_requests_seconds_avg": {
        "title": "Среднее время ответа API (Jetty)",
        "priority": 10,
        "description": "Рост = признак перегрузки, возможны таймауты",
        "why": "Рост среднего времени ответа — признак перегрузки, возможны таймауты.",
        "unit": "с",
        "format": "fixed2",
        "warning": 3.0,
        "critical": 5.0
    },
    "process_cpu_usage": {
        "title": "Загрузка CPU процесса узла",
        "priority": 9,
        "description": "Высокая загрузка CPU = узкое место",
        "why": "Высокая загрузка CPU может быть узким местом производительности.",
        "unit": "",
        "format": "fixed2",
        "warning": 0.85,
        "critical": 0.95
    },
    "postgres_locks": {
        "title": "Количество активных блокировок в БД",
        "priority": 9,
        "description": "Блокировки тормозят транзакции и запросы",
        "why": "Блокировки могут тормозить транзакции и запросы к БД.",
        "unit": "",
        "format": "fixed0",
        "warning": 10.0,
        "critical": 50.0
    },
    "jvm_gc_pause_seconds_sum": {
        "title": "Общее время пауз GC",
        "priority": 9,
        "description": "Долгие паузы GC = замирание узла",
        "why": "Долгие паузы GC приводят к замиранию узла и задержкам.",
        "unit": "с",
        "format": "fixed2",
        "warning": 1.0,
        "critical": 3.0
    },
    "postgres_connections": {
        "title": "Количество открытых подключений к БД",
        "priority": 8,
        "description": "Превышение лимита соединений = сбои",
        "why": "Превышение лимита соединений может привести к сбоям в работе БД.",
        "unit": "",
        "format": "fixed0",
        "warning": 100.0,
        "critical": 150.0
    },
    "jvm_memory_used_bytes": {
        "title": "Использование памяти (heap)",
        "priority": 8,
        "description": "Рост heap = давление на GC / OOM риск",
        "why": "Рост heap увеличивает давление на GC и риск OutOfMemory.",
        "unit": "B",
        "format": "fixed0",
        "warning": 0.75,
        "critical": 0.9
    },
    "system_load1": {
        "title": "Системная нагрузка за 1 минуту",
        "priority": 7,
        "description": "Высокая нагрузка = CPU/память на пределе",
        "why": "Высокая нагрузка — признак того, что CPU или память на пределе.",
        "unit": "",
        "format": "fixed2",
        "warning": 2.0,
        "critical": 4.0
    },
    "jetty_server_requests_seconds_count": {
        "title": "Количество запросов за всё время",
        "priority": 6,
        "description": "Нужно для оценки нагрузки",
        "why": "Позволяет оценить общую нагрузку на сервис.",
        "unit": "",
        "format": "fixed0"
    },
    "postgres_rows_inserted_total": {
        "title": "Количество вставок в БД",
        "priority": 6,
        "description": "Высокая вставка = возможное узкое место",
        "why": "Высокая скорость вставки может быть узким местом.",
        "unit": "",
        "format": "fixed0"
    },
    "postgres_blocks_read_total": {
        "title": "Чтения с диска",
        "priority": 5,
        "description": "Спайки = неэффективные запросы / IO",
        "why": "Спайки чтений с диска — признак неэффективных запросов или IO.",
        "unit": "",
        "format": "fixed0"
    },
    "jvm_threads_live": {
        "title": "Количество живых JVM-потоков",
        "priority": 4,
        "description": "Рост = утечка потоков / стресс",
        "why": "Рост числа потоков может быть признаком утечки или стресса JVM.",
        "unit": "",
        "format": "fixed0"
    },
    "jvm_classes_loaded": {
        "title": "Количество загруженных классов JVM",
        "priority": 3,
        "description": "Рост = возможная утечка классов",
        "why": "Рост числа классов может быть признаком утечки классов.",
        "unit": "",
        "format": "fixed0"
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
    "jetty_server_async_expires_total"
]
