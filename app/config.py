import os

# Удалён DEBUG_MODE и print

# URL метрик - можно переопределить через переменную окружения
METRICS_URL = os.getenv("METRICS_URL", "http://server:5110/metrics")
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

# ============================================================================
# ЦЕНТРАЛИЗОВАННАЯ КОНФИГУРАЦИЯ МЕТРИК
# ============================================================================
# Теперь все метрики определяются в одном месте с указанием секции
# Для добавления новой метрики достаточно добавить её в METRICS_CONFIG

METRICS_CONFIG = {
    # KPI секция
    "avg_response_time_api": {
        "section": "KPI",
        "label": "Среднее время ответа API",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{outcome="SUCCESS",status="200"}[1m]))',
        "type": "trend",
        "unit": "сек",
        "color": "#e74c3c",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.0}
    },
    "system_cpu_usage": {
        "section": "KPI",
        "label": "Загрузка CPU",
        "promql": "system_cpu_usage",
        "type": "trend",
        "unit": "%",
        "color": "#f39c12",
        "format": "percent",
        "thresholds": {"warning": 85, "critical": 95}
    },
    "jvm_memory_used": {
        "section": "KPI",
        "label": "Используемая память JVM",
        "promql": 'jvm_memory_used_bytes{area="heap",id="Tenured Gen"} / 1024 / 1024',
        "type": "trend",
        "unit": "МБ",
        "color": "#27ae60",
        "format": "fixed1",
        "thresholds": {"warning": 750, "critical": 900}
    },
    "postgres_connections": {
        "section": "KPI",
        "label": "Активные подключения к БД",
        "promql": 'postgres_connections{database="db01"}',
        "type": "trend",
        "unit": "",
        "color": "#1abc9c",
        "format": "fixed0",
        "thresholds": {"warning": 100, "critical": 150}
    },
    "postgres_locks": {
        "section": "KPI",
        "label": "Активные блокировки в БД",
        "promql": 'postgres_locks{database="db01"}',
        "type": "trend",
        "unit": "",
        "color": "#e67e22",
        "format": "fixed0",
        "thresholds": {"warning": 10, "critical": 50}
    },
    "gc_pause_time": {
        "section": "KPI",
        "label": "Время паузы GC",
        "promql": "jvm_gc_pause_seconds_sum",
        "type": "trend",
        "unit": "сек",
        "color": "#34495e",
        "format": "fixed2",
        "thresholds": {"warning": 1.0, "critical": 3.0}
    },
    "system_load": {
        "section": "KPI",
        "label": "Нагрузка системы (1 мин)",
        "promql": "system_load_average_1m",
        "type": "trend",
        "unit": "",
        "color": "#95a5a6",
        "format": "fixed2",
        "thresholds": {"warning": 2.0, "critical": 4.0}
    },
    "tx_pool_size": {
        "section": "KPI",
        "label": "Размер пула транзакций",
        "promql": "tx_pool_size",
        "type": "trend",
        "unit": "",
        "color": "#8e44ad",
        "format": "fixed0",
        "thresholds": {"warning": 1000, "critical": 5000}
    },
    
    # Transactions секция
    "postgres_transactions_total": {
        "section": "Transactions",
        "label": "Транзакции PostgreSQL",
        "promql": 'rate(postgres_transactions_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#8e44ad",
        "format": "fixed0"
    },
    "postgres_rows_inserted_total": {
        "section": "Transactions",
        "label": "Вставки в БД",
        "promql": 'rate(postgres_rows_inserted_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#27ae60",
        "format": "fixed0"
    },
    "postgres_rows_updated_total": {
        "section": "Transactions",
        "label": "Обновления в БД",
        "promql": 'rate(postgres_rows_updated_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#f39c12",
        "format": "fixed0"
    },
    "postgres_rows_deleted_total": {
        "section": "Transactions",
        "label": "Удаления из БД",
        "promql": 'rate(postgres_rows_deleted_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#e74c3c",
        "format": "fixed0"
    },
    
    # PostgreSQL секция
    "postgres_blocks_reads_total": {
        "section": "PostgreSQL",
        "label": "Прочтения блоков с диска",
        "promql": 'rate(postgres_blocks_reads_total{database="db01"}[1m])',
        "type": "trend",
        "unit": "",
        "color": "#3498db",
        "format": "fixed0"
    },
    "postgres_dead_rows": {
        "section": "PostgreSQL",
        "label": "Мертвые строки в БД",
        "promql": 'postgres_dead_rows{database="db01"}',
        "type": "trend",
        "unit": "",
        "color": "#c0392b",
        "format": "fixed0",
        "thresholds": {"warning": 10000, "critical": 20000}
    },
    
    # JVM секция
    "jvm_threads_live_threads": {
        "section": "JVM",
        "label": "Активные потоки JVM",
        "promql": "jvm_threads_live_threads",
        "type": "trend",
        "unit": "",
        "color": "#9b59b6",
        "format": "fixed0"
    },
    "jvm_classes_loaded_classes": {
        "section": "JVM",
        "label": "Загруженные классы JVM",
        "promql": "jvm_classes_loaded_classes",
        "type": "trend",
        "unit": "",
        "color": "#1abc9c",
        "format": "fixed0"
    },
    
    # Jetty секция
    "jetty_server_requests_seconds_avg": {
        "section": "Jetty",
        "label": "Среднее время запросов Jetty",
        "promql": "jetty_server_requests_seconds_avg",
        "type": "trend",
        "unit": "сек",
        "color": "#e74c3c",
        "format": "fixed3"
    },
    "jetty_get_avg_time": {
        "section": "Jetty",
        "label": "Среднее время GET запросов",
        "promql": "jetty_get_avg_time",
        "type": "trend",
        "unit": "сек",
        "color": "#3498db",
        "format": "fixed3"
    },
    "jetty_post_avg_time": {
        "section": "Jetty",
        "label": "Среднее время POST запросов",
        "promql": "jetty_post_avg_time",
        "type": "trend",
        "unit": "сек",
        "color": "#9b59b6",
        "format": "fixed3"
    },
    "jetty_connections_current_connections": {
        "section": "Jetty",
        "label": "Текущие подключения Jetty",
        "promql": "jetty_connections_current_connections",
        "type": "trend",
        "unit": "",
        "color": "#f39c12",
        "format": "fixed0"
    },
    "jetty_connections_bytes_in_bytes_sum": {
        "section": "Jetty",
        "label": "Входящий трафик Jetty",
        "promql": "jetty_connections_bytes_in_bytes_sum",
        "type": "trend",
        "unit": "байт",
        "color": "#27ae60",
        "format": "mb"
    },
    "jetty_connections_bytes_out_bytes_sum": {
        "section": "Jetty",
        "label": "Исходящий трафик Jetty",
        "promql": "jetty_connections_bytes_out_bytes_sum",
        "type": "trend",
        "unit": "байт",
        "color": "#e67e22",
        "format": "mb"
    },
    
    # System секция
    "system_cpu_count": {
        "section": "System",
        "label": "Количество CPU ядер",
        "promql": "system_cpu_count",
        "type": "trend",
        "unit": "",
        "color": "#95a5a6",
        "format": "fixed0"
    },
    
    # Дополнительные метрики (не в основных секциях)
    "get_response_time": {
        "section": "API",
        "label": "Время ответа GET запросов",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{method="GET",outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{method="GET",outcome="SUCCESS",status="200"}[1m]))',
        "type": "trend",
        "unit": "сек",
        "color": "#3498db",
        "format": "fixed3",
        "thresholds": {"warning": 0.3, "critical": 0.8}
    },
    "post_response_time": {
        "section": "API",
        "label": "Время ответа POST запросов",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{method="POST",outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{method="POST",outcome="SUCCESS",status="200"}[1m]))',
        "type": "trend",
        "unit": "сек",
        "color": "#9b59b6",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.2}
    },
    "jvm_gc_pause_seconds_sum": {
        "section": "JVM",
        "label": "Суммарное время пауз GC (JVM)",
        "promql": "jvm_gc_pause_seconds_sum",
        "type": "trend",
        "unit": "сек",
        "color": "#34495e",
        "format": "fixed2"
    }
}

# ============================================================================
# АВТОМАТИЧЕСКАЯ ГЕНЕРАЦИЯ СЕКЦИЙ И МЕТРИК
# ============================================================================

def generate_sections_from_config():
    """Автоматически генерирует секции из централизованной конфигурации"""
    sections = {}
    for metric_id, config in METRICS_CONFIG.items():
        section_name = config.get("section", "Other")
        if section_name not in sections:
            sections[section_name] = []
        sections[section_name].append(metric_id)
    return sections

def generate_all_metrics_from_config():
    """Автоматически генерирует ALL_METRICS из централизованной конфигурации"""
    all_metrics = {}
    for metric_id, config in METRICS_CONFIG.items():
        # Копируем конфигурацию без поля section
        metric_config = {k: v for k, v in config.items() if k != "section"}
        all_metrics[metric_id] = metric_config
    return all_metrics

# Автоматически генерируем секции и метрики
SECTIONS = generate_sections_from_config()
ALL_METRICS = generate_all_metrics_from_config()

# Конфигурация KPI-метрик для модернизированного дашборда (для обратной совместимости)
KPI_METRIC_IDS = [
    "avg_response_time_api",
    "get_response_time",
    "post_response_time",
    "system_cpu_usage",
    "jvm_memory_used",
    "postgres_connections",
    "postgres_locks",
    "gc_pause_time",
    "system_load",
    "tx_pool_size",
]

# Структуры конфигурации KPI формируются на основе ALL_METRICS
KPI_METRICS_CONFIG = [
    {
        "id": mid,
        "title": ALL_METRICS[mid]["label"],
        **{k: v for k, v in ALL_METRICS[mid].items() if k != "label"}
    }
    for mid in KPI_METRIC_IDS
]

# Список всех метрик для инициализации
INITIAL_METRICS = list(METRICS_CONFIG.keys())

METRIC_HISTORY_SECONDS = int(os.getenv("METRIC_HISTORY_SECONDS", 3600))  # 1 час
