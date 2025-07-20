import os

# Удалён DEBUG_MODE и print

# Моковый режим для тестирования фронта
# MOCK_MODE = True

METRICS_URL = "http://server:5110/metrics"
UPDATE_INTERVAL = 1.0
REQUEST_TIMEOUT = 3.0
HISTORY_LENGTH = 60

# Удалена переменная PROMETHEUS_URL и связанные строки

# Доступные интервалы времени для графиков (в минутах)
TIME_INTERVALS = [
    {"value": 15, "label": "15 минут"},
    {"value": 30, "label": "30 минут"}, 
    {"value": 45, "label": "45 минут"},
    {"value": 60, "label": "1 час"}
]

# Секции метрик (группировка по категориям)
SECTIONS = {
    "KPI": [
        "avg_response_time_api",
        "system_cpu_usage", 
        "jvm_memory_used",
        "postgres_connections",
        "postgres_locks",
        "gc_pause_time",
        "system_load",
        "tx_pool_size"
    ],
    "Transactions": [
        "postgres_transactions_total",
        "postgres_rows_inserted_total",
        "postgres_rows_updated_total",
        "postgres_rows_deleted_total"
    ],
    "PostgreSQL": [
        "postgres_connections",
        "postgres_locks",
        "postgres_blocks_reads_total"
    ],
    "JVM": [
        "jvm_threads_live_threads",
        "jvm_classes_loaded_classes"
    ],
    "Jetty": [
        "jetty_server_requests_seconds_avg",
        "jetty_get_avg_time",
        "jetty_post_avg_time",
        "jetty_connections_current_connections",
        "jetty_connections_bytes_in_bytes_sum",
        "jetty_connections_bytes_out_bytes_sum"
    ],
    "System": [
        "system_cpu_usage",
        "system_load_average_1m",
        "system_cpu_count"
    ]
}

# Полная конфигурация всех метрик
ALL_METRICS = {
    "avg_response_time_api": {
        "label": "Среднее время ответа API",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{outcome="SUCCESS",status="200"}[1m]))',
        "type": "trend+bar",
        "unit": "сек",
        "color": "#e74c3c",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.0}
    },
    "get_response_time": {
        "label": "Время ответа GET запросов",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{method="GET",outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{method="GET",outcome="SUCCESS",status="200"}[1m]))',
        "type": "trend+bar",
        "unit": "сек",
        "color": "#3498db",
        "format": "fixed3",
        "thresholds": {"warning": 0.3, "critical": 0.8}
    },
    "post_response_time": {
        "label": "Время ответа POST запросов",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{method="POST",outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{method="POST",outcome="SUCCESS",status="200"}[1m]))',
        "type": "trend+bar",
        "unit": "сек",
        "color": "#9b59b6",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.2}
    },
    "system_cpu_usage": {
        "label": "Загрузка CPU",
        "promql": "system_cpu_usage",
        "type": "trend+bar",
        "unit": "%",
        "color": "#f39c12",
        "format": "percent",
        "thresholds": {"warning": 85, "critical": 95}
    },
    "jvm_memory_used": {
        "label": "Используемая память JVM",
        "promql": 'jvm_memory_used_bytes{area="heap",id="Tenured Gen"} / 1024 / 1024',
        "type": "trend+bar",
        "unit": "МБ",
        "color": "#27ae60",
        "format": "fixed1",
        "thresholds": {"warning": 750, "critical": 900}
    },
    "postgres_connections": {
        "label": "Активные подключения к БД",
        "promql": 'postgres_connections{database="db01"}',
        "type": "trend+bar",
        "unit": "",
        "color": "#1abc9c",
        "format": "fixed0",
        "thresholds": {"warning": 100, "critical": 150}
    },
    "postgres_locks": {
        "label": "Активные блокировки в БД",
        "promql": 'postgres_locks{database="db01"}',
        "type": "trend+bar",
        "unit": "",
        "color": "#e67e22",
        "format": "fixed0",
        "thresholds": {"warning": 10, "critical": 50}
    },
    "gc_pause_time": {
        "label": "Время паузы GC",
        "promql": "jvm_gc_pause_seconds_sum",
        "type": "trend+bar",
        "unit": "сек",
        "color": "#34495e",
        "format": "fixed2",
        "thresholds": {"warning": 1.0, "critical": 3.0}
    },
    "system_load": {
        "label": "Нагрузка системы (1 мин)",
        "promql": "system_load_average_1m",
        "type": "trend+bar",
        "unit": "",
        "color": "#95a5a6",
        "format": "fixed2",
        "thresholds": {"warning": 2.0, "critical": 4.0}
    },
    "tx_pool_size": {
        "label": "Размер пула транзакций",
        "promql": "tx_pool_size",
        "type": "trend+bar",
        "unit": "",
        "color": "#8e44ad",
        "format": "fixed0",
        "thresholds": {"warning": 1000, "critical": 5000}
    },
    "postgres_transactions_total": {
        "label": "Транзакции PostgreSQL",
        "promql": 'rate(postgres_transactions_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#8e44ad",
        "format": "fixed0"
    },
    "postgres_rows_inserted_total": {
        "label": "Вставки в БД",
        "promql": 'rate(postgres_rows_inserted_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#27ae60",
        "format": "fixed0"
    },
    "postgres_rows_updated_total": {
        "label": "Обновления в БД",
        "promql": 'rate(postgres_rows_updated_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#f39c12",
        "format": "fixed0"
    },
    "postgres_rows_deleted_total": {
        "label": "Удаления из БД",
        "promql": 'rate(postgres_rows_deleted_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#e74c3c",
        "format": "fixed0"
    },
    "postgres_blocks_reads_total": {
        "label": "Прочтения блоков с диска",
        "promql": 'rate(postgres_blocks_reads_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#3498db",
        "format": "fixed0"
    },
    "jvm_threads_live_threads": {
        "label": "Активные потоки JVM",
        "promql": "jvm_threads_live_threads",
        "type": "trend+bar",
        "unit": "",
        "color": "#9b59b6",
        "format": "fixed0"
    },
    "jvm_classes_loaded_classes": {
        "label": "Загруженные классы JVM",
        "promql": "jvm_classes_loaded_classes",
        "type": "trend",
        "unit": "",
        "color": "#1abc9c",
        "format": "fixed0"
    },
    "jetty_server_requests_seconds_avg": {
        "label": "Среднее время запросов Jetty",
        "promql": "jetty_server_requests_seconds_avg",
        "type": "trend+bar",
        "unit": "сек",
        "color": "#e74c3c",
        "format": "fixed3"
    },
    "jetty_get_avg_time": {
        "label": "Среднее время GET запросов",
        "promql": "jetty_get_avg_time",
        "type": "trend+bar",
        "unit": "сек",
        "color": "#3498db",
        "format": "fixed3"
    },
    "jetty_post_avg_time": {
        "label": "Среднее время POST запросов",
        "promql": "jetty_post_avg_time",
        "type": "trend+bar",
        "unit": "сек",
        "color": "#9b59b6",
        "format": "fixed3"
    },
    "jetty_connections_current_connections": {
        "label": "Текущие подключения Jetty",
        "promql": "jetty_connections_current_connections",
        "type": "trend+bar",
        "unit": "",
        "color": "#f39c12",
        "format": "fixed0"
    },
    "jetty_connections_bytes_in_bytes_sum": {
        "label": "Входящий трафик Jetty",
        "promql": "jetty_connections_bytes_in_bytes_sum",
        "type": "trend",
        "unit": "байт",
        "color": "#27ae60",
        "format": "mb"
    },
    "jetty_connections_bytes_out_bytes_sum": {
        "label": "Исходящий трафик Jetty",
        "promql": "jetty_connections_bytes_out_bytes_sum",
        "type": "trend",
        "unit": "байт",
        "color": "#e67e22",
        "format": "mb"
    },
    "system_cpu_count": {
        "label": "Количество CPU ядер",
        "promql": "system_cpu_count",
        "type": "bar",
        "unit": "",
        "color": "#95a5a6",
        "format": "fixed0"
    },
    "jvm_gc_pause_seconds_sum": {
        "label": "Суммарное время пауз GC (JVM)",
        "promql": "jvm_gc_pause_seconds_sum",
        "type": "trend+bar",
        "unit": "сек",
        "color": "#34495e",
        "format": "fixed2"
    },
    "jvm_memory_used_bytes": {
        "label": "Используемая память JVM (байт)",
        "promql": 'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}',
        "type": "trend+bar",
        "unit": "МБ",
        "color": "#27ae60",
        "format": "fixed1"
    },
    "system_load_average_1m": {
        "label": "Нагрузка системы (1 мин)",
        "promql": "system_load_average_1m",
        "type": "trend+bar",
        "unit": "",
        "color": "#95a5a6",
        "format": "fixed2"
    }
}

# Конфигурация KPI-метрик для модернизированного дашборда (для обратной совместимости)
KPI_METRICS_CONFIG = [
    {
        "id": "avg_response_time_api",
        "title": "Среднее время ответа API",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{outcome="SUCCESS",status="200"}[1m]))',
        "unit": "сек",
        "color": "#e74c3c",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.0}
    },
    {
        "id": "get_response_time", 
        "title": "Время ответа GET запросов",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{method="GET",outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{method="GET",outcome="SUCCESS",status="200"}[1m]))',
        "unit": "сек",
        "color": "#3498db",
        "format": "fixed3",
        "thresholds": {"warning": 0.3, "critical": 0.8}
    },
    {
        "id": "post_response_time",
        "title": "Время ответа POST запросов", 
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{method="POST",outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{method="POST",outcome="SUCCESS",status="200"}[1m]))',
        "unit": "сек",
        "color": "#9b59b6",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.2}
    },
    {
        "id": "system_cpu_usage",
        "title": "Загрузка CPU",
        "promql": 'system_cpu_usage',
        "unit": "%",
        "color": "#f39c12",
        "format": "percent",
        "thresholds": {"warning": 85, "critical": 95}
    },
    {
        "id": "jvm_memory_used",
        "title": "Используемая память JVM",
        "promql": 'jvm_memory_used_bytes{area="heap",id="Tenured Gen"} / 1024 / 1024',
        "unit": "МБ",
        "color": "#27ae60",
        "format": "fixed1",
        "thresholds": {"warning": 750, "critical": 900}
    },
    {
        "id": "postgres_connections",
        "title": "Активные подключения к БД",
        "promql": 'postgres_connections{database="db01"}',
        "unit": "",
        "color": "#1abc9c",
        "format": "fixed0",
        "thresholds": {"warning": 100, "critical": 150}
    },
    {
        "id": "postgres_locks",
        "title": "Активные блокировки в БД",
        "promql": 'postgres_locks{database="db01"}',
        "unit": "",
        "color": "#e67e22",
        "format": "fixed0",
        "thresholds": {"warning": 10, "critical": 50}
    },
    {
        "id": "gc_pause_time",
        "title": "Время паузы GC",
        "promql": 'jvm_gc_pause_seconds_sum',
        "unit": "сек",
        "color": "#34495e",
        "format": "fixed2",
        "thresholds": {"warning": 1.0, "critical": 3.0}
    },
    {
        "id": "system_load",
        "title": "Нагрузка системы (1 мин)",
        "promql": 'system_load_average_1m',
        "unit": "",
        "color": "#95a5a6",
        "format": "fixed2",
        "thresholds": {"warning": 2.0, "critical": 4.0}
    },
    {
        "id": "tx_pool_size",
        "title": "Размер пула транзакций",
        "promql": 'tx_pool_size',
        "unit": "",
        "color": "#8e44ad",
        "format": "fixed0",
        "thresholds": {"warning": 1000, "critical": 5000}
    }
]

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

METRIC_HISTORY_SECONDS = int(os.getenv("METRIC_HISTORY_SECONDS", 3600))  # 1 час
