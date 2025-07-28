from flask import Blueprint, render_template, jsonify, request
from .metrics import get_metrics_data, get_metrics_history, start_metrics_thread
import time
from .config import METRICS_CONFIG, PROMINENT_METRICS
import os

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def dashboard():
    return render_template("dashboard.html")

@dashboard_bp.route("/data")
def data():
    return jsonify(get_metrics_data())

@dashboard_bp.route("/history")
def history():
    return jsonify(get_metrics_history())

# Новая точка: возвращает историю сразу по нескольким метрикам
@dashboard_bp.route("/api/metrics/history")
def metrics_history():
    """Return history for multiple metrics at once."""
    try:
        metrics_param = request.args.get("metrics", "")
        interval = request.args.get("interval", "30")
        try:
            interval_minutes = int(interval)
        except ValueError:
            interval_minutes = 30
        metric_ids = [m.strip() for m in metrics_param.split(',') if m.strip()]
        now = int(time.time())
        start_time = now - interval_minutes * 60
        history = get_metrics_history()
        results = []
        for metric_id in metric_ids:
            values = history.get(metric_id, [])
            filtered = [v for v in values if v[0] >= start_time]
            results.append({
                "metric": {"__name__": metric_id},
                "values": [[ts, val] for ts, val in filtered]
            })
        return jsonify({
            "status": "success",
            "data": {"result": results}
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to get metrics history: {str(e)}"
        }), 500

js_error_log = []
JS_ERROR_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'js_error.log')

@dashboard_bp.route('/log-js-error', methods=['POST'])
def log_js_error():
    data = request.get_json(force=True)
    context = data.get('context', 'unknown')
    error = data.get('error', 'unknown')
    entry = {'context': context, 'error': error}
    js_error_log.append(entry)
    print(f"[JS ERROR] Context: {context}\nError: {error}")
    print(f"[JS ERROR] Путь к файлу: {JS_ERROR_LOG_PATH}")
    # Оставляем только последние 100 ошибок
    if len(js_error_log) > 100:
        js_error_log.pop(0)
    # Записываем ошибку в файл
    try:
        print(f"[JS ERROR] Пытаемся записать в файл: {JS_ERROR_LOG_PATH}")
        with open(JS_ERROR_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"[JS ERROR] Context: {context}\nError: {error}\n\n")
        print(f"[JS ERROR] Успешно записано в файл")
    except Exception as e:
        print(f"[JS ERROR] Не удалось записать в файл: {e}")
        print(f"[JS ERROR] Тип ошибки: {type(e)}")
        import traceback
        print(f"[JS ERROR] Traceback: {traceback.format_exc()}")
    return '', 204

@dashboard_bp.route('/log-js-error', methods=['GET'])
def get_js_error_log():
    return jsonify(js_error_log)

@dashboard_bp.route('/debug-log-path')
def debug_log_path():
    import os
    return jsonify({
        'log_path': JS_ERROR_LOG_PATH,
        'log_path_exists': os.path.exists(JS_ERROR_LOG_PATH),
        'current_dir': os.getcwd(),
        'app_dir': os.path.dirname(os.path.dirname(__file__))
    })

@dashboard_bp.route('/debug')
def debug_info():
    import os
    import sys
    from .metrics import get_metrics_data, get_metrics_history
    
    # Проверяем файл лога
    log_file_info = {}
    try:
        if os.path.exists(JS_ERROR_LOG_PATH):
            with open(JS_ERROR_LOG_PATH, 'r', encoding='utf-8') as f:
                log_content = f.read()
            log_file_info = {
                'exists': True,
                'size': os.path.getsize(JS_ERROR_LOG_PATH),
                'last_lines': log_content.split('\n')[-10:] if log_content else []
            }
        else:
            log_file_info = {'exists': False}
    except Exception as e:
        log_file_info = {'error': str(e)}
    
    # Получаем данные метрик
    metrics_data = get_metrics_data()
    history_data = get_metrics_history()
    
    return jsonify({
        'system': {
            'python_version': sys.version,
            'current_dir': os.getcwd(),
            'log_path': JS_ERROR_LOG_PATH,
            'log_file_info': log_file_info
        },
        'app': {
            'js_errors_count': len(js_error_log),
            'metrics_count': len(metrics_data.get('metrics', {})) if metrics_data else 0,
            'history_count': len(history_data) if history_data else 0,
            'prominent_metrics': list(PROMINENT_METRICS.keys())
        },
        'js_errors': js_error_log[-5:] if js_error_log else []  # Последние 5 ошибок
    })

start_metrics_thread()
