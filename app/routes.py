from flask import Blueprint, render_template, jsonify, request
from .metrics import get_metrics_data, get_metrics_history, start_metrics_thread
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
    # Оставляем только последние 100 ошибок
    if len(js_error_log) > 100:
        js_error_log.pop(0)
    # Записываем ошибку в файл
    try:
        with open(JS_ERROR_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"[JS ERROR] Context: {context}\nError: {error}\n\n")
    except Exception as e:
        print(f"[JS ERROR] Не удалось записать в файл: {e}")
    return '', 204

@dashboard_bp.route('/log-js-error', methods=['GET'])
def get_js_error_log():
    return jsonify(js_error_log)

start_metrics_thread()
