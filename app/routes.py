from flask import Blueprint, render_template, jsonify
from .metrics import MetricsService, get_metrics_history

dashboard_bp = Blueprint("dashboard", __name__)

# Default metrics configuration for frontend
DEFAULT_METRICS_CONFIG = [
    { "category": "Transactions", "metrics": [
        'postgres_transactions_total{database="db01"}',
        'postgres_rows_updated_total{database="db01"}',
        'postgres_rows_deleted_total{database="db01"}'
    ], "display": "counter", "color": "#8e44ad", "priority": 1 },
    { "category": "PostgreSQL", "metrics": [
        'postgres_connections{database="db01"}',
        'postgres_locks{database="db01"}',
        'postgres_blocks_reads_total{database="db01"}',
        'postgres_rows_inserted_total{database="db01"}',
        'postgres_rows_updated_total',
        'postgres_transactions_total'
    ], "display": "compact", "color": "#3498db", "priority": 2 },
    { "category": "JVM", "metrics": [
        'jvm_gc_pause_seconds_sum',
        'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}',
        'jvm_threads_live_threads',
        'jvm_classes_loaded_classes'
    ], "display": "compact", "color": "#27ae60", "priority": 3 },
    { "category": "Jetty", "metrics": [
        'jetty_server_requests_seconds_avg',
        'jetty_connections_current_connections',
        'jetty_connections_bytes_in_bytes_sum',
        'jetty_connections_bytes_out_bytes_sum'
    ], "display": "compact", "color": "#e74c3c", "priority": 4 },
    { "category": "System", "metrics": [
        'process_cpu_usage',
        'system_load_average_1m',
        'system_cpu_count'
    ], "display": "compact", "color": "#f39c12", "priority": 5 }
]

@dashboard_bp.route("/")
def dashboard():
    return render_template("dashboard.html")

@dashboard_bp.route("/data")
def data():
    return jsonify(MetricsService.get_metrics_data())

@dashboard_bp.route("/history")
def history():
    return jsonify(get_metrics_history())

@dashboard_bp.route("/dashboard_data")
def dashboard_data():
    kpi_data = MetricsService.get_metrics_data()
    history_data = get_metrics_history()
    
    # Ensure every prominent key exists in history
    prominent = kpi_data["prominent"]
    for key in prominent:
        if key not in history_data:
            # Create empty history entry for missing keys
            history_data[key] = []
    
    return jsonify({
        "prominent": prominent,
        "metrics": kpi_data["metrics"],
        "history": history_data,
        "config": DEFAULT_METRICS_CONFIG,
        "error": kpi_data.get("error"),
    })
