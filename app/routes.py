from flask import Blueprint, render_template, jsonify, request
from .metrics import get_metrics_data, get_metrics_history, start_metrics_thread
from .config import METRICS_CONFIG, PROMINENT_METRICS

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

js_error_log = []

@dashboard_bp.route('/log-js-error', methods=['POST'])
def log_js_error():
    data = request.get_json(force=True)
    context = data.get('context', 'unknown')
    error = data.get('error', 'unknown')
    entry = {'context': context, 'error': error}
    js_error_log.append(entry)
    print(f"[JS ERROR] Context: {context}\nError: {error}")
    # Оставляем только последние 100 ошибок
    if len(js_error_log) > 100:
        js_error_log.pop(0)
    return '', 204

@dashboard_bp.route('/log-js-error', methods=['GET'])
def get_js_error_log():
    return jsonify(js_error_log)

start_metrics_thread()
