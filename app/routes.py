from flask import Blueprint, render_template, jsonify, request
import time
from .config import SECTIONS, ALL_METRICS, TIME_INTERVALS, KPI_METRICS_CONFIG
from .metrics import MetricsService

dashboard_bp = Blueprint("dashboard", __name__)

# Default metrics configuration for frontend (для обратной совместимости)
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
    # Проверяем debug-режим
    debug_mode = request.args.get('debug', 'false').lower() == 'true'
    return render_template("dashboard.html", debug_mode=debug_mode)

@dashboard_bp.route("/data")
def data():
    return jsonify(MetricsService.get_metrics_data())

@dashboard_bp.route("/dashboard_data")
def dashboard_data():
    try:
        kpi_data = MetricsService.get_metrics_data()

        history_data = MetricsService.get_metrics_history()
        
        # Ensure every prominent key exists in history
        prominent = kpi_data["prominent"]
        for key in prominent:
            if key not in history_data:
                # Create empty history entry for missing keys
                history_data[key] = []
        
        response_data = {
            "prominent": prominent,
            "metrics": kpi_data["metrics"],
            "history": history_data,
            "config": DEFAULT_METRICS_CONFIG,
            "error": kpi_data.get("error"),
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to load dashboard data: {str(e)}"
        }), 500

# Удалены все строки, связанные с prometheus_url, requests.get(prometheus_url, ...), и любые упоминания query_range

@dashboard_bp.route("/api/sections")
def sections_config():
    """
    Возвращает конфигурацию секций метрик
    """
    return jsonify({
        "status": "ok",
        "sections": SECTIONS,
        "all_metrics": ALL_METRICS,
        "time_intervals": TIME_INTERVALS
    })

@dashboard_bp.route("/api/test")
def test_endpoint():
    """
    Простой тестовый endpoint для проверки
    """
    return jsonify({
        "status": "ok",
        "message": "Test endpoint works"
    })

# Удалён эндпоинт /sections (sections_simple)

@dashboard_bp.route("/api/kpi/config")
def kpi_config():
    """
    Возвращает конфигурацию KPI-метрик для фронтенда (для обратной совместимости)
    """
    return jsonify({
        "kpi_metrics": KPI_METRICS_CONFIG,
        "time_intervals": TIME_INTERVALS
    })

@dashboard_bp.route("/api/metrics/<metric_id>/history")
def metric_history(metric_id):
    """Возвращает историю конкретной метрики из памяти"""
    try:
        if metric_id not in ALL_METRICS:
            return jsonify({
                "status": "error",
                "error": f"Metric '{metric_id}' not found"
            }), 404

        # Параметр interval определяет окно выборки в минутах
        interval = request.args.get("interval", "30")
        try:
            interval_minutes = int(interval)
        except ValueError:
            interval_minutes = 30

        now = int(time.time())
        start_time = now - interval_minutes * 60

        history = MetricsService.get_metrics_history()
        values = history.get(metric_id, [])
        filtered = [v for v in values if v[0] >= start_time]

        result = {
            "status": "success",
            "data": {
                "result": [{
                    "metric": {"__name__": metric_id},
                    "values": [[ts, str(val)] for ts, val in filtered]
                }]
            }
        }
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to get metric history: {str(e)}"
        }), 500

@dashboard_bp.route("/api/history")
def metric_history_api():
    metric = request.args.get("metric")
    if not metric:
        return jsonify({"status": "error", "error": "no metric"}), 400
    history = MetricsService.get_metrics_history()
    values = history.get(metric, [])
    result = {
        "status": "success",
        "data": {
            "result": [{
                "metric": {"__name__": metric},
                "values": [[d["ts"], str(d["value"])] for d in values]
            }]
        }
    }
    return jsonify(result)

@dashboard_bp.route("/export")
def export_report():
    history = MetricsService.get_metrics_history()
    stats = {name: calc_metric_stats(history[name]) for name in history}
    return render_template("report.html", stats=stats, history=history)


def calc_metric_stats(values):
    if not values:
        return {"start": 0, "max": 0, "avg": 0}
    vals = [d["value"] for d in values]
    return {
        "start": vals[0],
        "max": max(vals),
        "avg": sum(vals) / len(vals)
    }
