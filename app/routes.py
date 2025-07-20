from flask import Blueprint, render_template, jsonify, request
import requests
import time
from .metrics import MetricsService, get_metrics_history
from .config import SECTIONS, ALL_METRICS, TIME_INTERVALS, PROMETHEUS_URL, MOCK_MODE, KPI_METRICS_CONFIG

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
        print("[DEBUG] /dashboard_data called")
        kpi_data = MetricsService.get_metrics_data()
        print(f"[DEBUG] /dashboard_data kpi_data keys: {list(kpi_data.keys())}")
        print(f"[DEBUG] /dashboard_data prominent keys: {list(kpi_data.get('prominent', {}).keys())}")
        
        history_data = get_metrics_history()
        print(f"[DEBUG] /dashboard_data history_data keys: {list(history_data.keys())}")
        
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
        
        print(f"[DEBUG] /dashboard_data response data keys: {list(response_data.keys())}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[ERROR] /dashboard_data error: {e}")
        return jsonify({
            "error": f"Failed to load dashboard data: {str(e)}"
        }), 500

@dashboard_bp.route("/api/prometheus/query_range")
def prometheus_query_range():
    """
    Прокси-эндпоинт для запросов к Prometheus query_range API
    """
    try:
        # Получаем параметры из запроса
        query = request.args.get('query')
        start = request.args.get('start')
        end = request.args.get('end')
        step = request.args.get('step')
        
        if not all([query, start, end, step]):
            return jsonify({
                "status": "error",
                "error": "Missing required parameters: query, start, end, step"
            }), 400
        
        # В MOCK_MODE возвращаем тестовые данные
        if MOCK_MODE:
            return generate_mock_prometheus_data(query, start, end, step)
        
        # Формируем URL для запроса к Prometheus
        prometheus_url = f"{PROMETHEUS_URL}/api/v1/query_range"
        params = {
            'query': query,
            'start': start,
            'end': end,
            'step': step
        }
        
        # Делаем запрос к Prometheus
        response = requests.get(prometheus_url, params=params, timeout=10)
        response.raise_for_status()
        
        # Возвращаем ответ как есть
        return jsonify(response.json())
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "error": f"Prometheus request failed: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error", 
            "error": f"Internal error: {str(e)}"
        }), 500

@dashboard_bp.route("/api/sections")
def sections_config():
    """
    Возвращает конфигурацию секций метрик
    """
    print("[DEBUG] /api/sections called - real config")
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

@dashboard_bp.route("/sections")
def sections_simple():
    """
    Простой endpoint для секций без /api/ префикса
    """
    return jsonify({
        "status": "ok",
        "message": "Simple sections endpoint works"
    })

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
    """
    Возвращает историю конкретной метрики
    """
    try:
        if metric_id not in ALL_METRICS:
            return jsonify({
                "status": "error",
                "error": f"Metric '{metric_id}' not found"
            }), 404
        
        metric_config = ALL_METRICS[metric_id]
        
        # Получаем параметры времени
        interval = request.args.get('interval', '30')
        try:
            interval_minutes = int(interval)
        except ValueError:
            interval_minutes = 30
        
        # Вычисляем временные параметры
        now = int(time.time())
        start_time = now - (interval_minutes * 60)
        step = max(1, interval_minutes)  # step = interval_seconds / 60
        
        # Формируем запрос к Prometheus
        params = {
            'query': metric_config['promql'],
            'start': str(start_time),
            'end': str(now),
            'step': str(step)
        }
        
        # В MOCK_MODE возвращаем тестовые данные
        if MOCK_MODE:
            return generate_mock_prometheus_data(metric_config['promql'], str(start_time), str(now), str(step))
        
        # Делаем запрос к Prometheus
        prometheus_url = f"{PROMETHEUS_URL}/api/v1/query_range"
        response = requests.get(prometheus_url, params=params, timeout=10)
        response.raise_for_status()
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to get metric history: {str(e)}"
        }), 500

def generate_mock_prometheus_data(query, start, end, step):
    """
    Генерирует моковые данные для Prometheus query_range в MOCK_MODE
    """
    try:
        start_time = float(start)
        end_time = float(end)
        step_seconds = float(step)
        
        # Определяем базовые значения в зависимости от запроса
        base_values = {
            'system_cpu_usage': {'base': 0.75, 'range': 0.2, 'min': 0.3},
            'jvm_memory_used_bytes': {'base': 192521736, 'range': 50000000, 'min': 150000000},
            'postgres_connections': {'base': 68, 'range': 15, 'min': 50},
            'postgres_locks': {'base': 1, 'range': 3, 'min': 0},
            'jvm_gc_pause_seconds_sum': {'base': 21.743, 'range': 5, 'min': 15},
            'system_load_average_1m': {'base': 0.82, 'range': 0.3, 'min': 0.4},
            'tx_pool_size': {'base': 150, 'range': 30, 'min': 100},
            'jetty_server_requests_seconds_count': {'base': 1234, 'range': 200, 'min': 1000},
            'postgres_rows_inserted_total': {'base': 1282731, 'range': 100000, 'min': 1200000},
            'postgres_transactions_total': {'base': 5000, 'range': 1000, 'min': 4000},
            'postgres_rows_updated_total': {'base': 2000, 'range': 500, 'min': 1500},
            'postgres_rows_deleted_total': {'base': 100, 'range': 50, 'min': 50},
            'postgres_blocks_reads_total': {'base': 50000, 'range': 10000, 'min': 40000},
            'jvm_threads_live_threads': {'base': 45, 'range': 10, 'min': 35},
            'jvm_classes_loaded_classes': {'base': 8000, 'range': 500, 'min': 7500},
            'jetty_server_requests_seconds_avg': {'base': 0.045, 'range': 0.02, 'min': 0.01},
            'jetty_get_avg_time': {'base': 0.032, 'range': 0.01, 'min': 0.02},
            'jetty_post_avg_time': {'base': 0.078, 'range': 0.05, 'min': 0.06},
            'jetty_connections_current_connections': {'base': 25, 'range': 10, 'min': 15},
            'jetty_connections_bytes_in_bytes_sum': {'base': 1000000, 'range': 200000, 'min': 800000},
            'jetty_connections_bytes_out_bytes_sum': {'base': 2000000, 'range': 400000, 'min': 1600000},
            'system_cpu_count': {'base': 8, 'range': 0, 'min': 8}  # Фиксированное значение
        }
        
        # Определяем базовые параметры для метрики
        metric_config = None
        for metric_name, config in base_values.items():
            if metric_name in query:
                metric_config = config
                break
        
        if not metric_config:
            # Для неизвестных метрик используем общие параметры
            metric_config = {'base': 100, 'range': 50, 'min': 50}
        
        # Генерируем временные ряды
        timestamps = []
        values = []
        current_time = start_time
        current_val = metric_config['base']
        
        import random
        
        while current_time <= end_time:
            timestamps.append(current_time)
            
            # Добавляем случайные колебания
            change = (random.random() - 0.5) * metric_config['range'] * 0.1
            current_val += change
            current_val = max(current_val, metric_config['min'])
            
            # Для счетчиков значения только растут
            if 'count' in query or 'total' in query:
                current_val = max(current_val, metric_config['base'] + (current_time - start_time) * 0.01)
            
            # Для system_cpu_count - фиксированное значение
            if 'system_cpu_count' in query:
                current_val = metric_config['base']
            
            values.append(round(current_val, 3))
            current_time += step_seconds
        
        return jsonify({
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [{
                    "metric": {"__name__": query.split('{')[0] if '{' in query else query},
                    "values": list(zip(timestamps, values))
                }]
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Mock data generation failed: {str(e)}"
        }), 500
