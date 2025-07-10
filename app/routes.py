from flask import Blueprint, render_template, jsonify
from .metrics import MetricsService, get_metrics_history

dashboard_bp = Blueprint("dashboard", __name__)

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
    return jsonify({
        "prominent": kpi_data["prominent"],
        "metrics": kpi_data["metrics"],
        "history": history_data,
        "error": kpi_data.get("error"),
    })
