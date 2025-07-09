from flask import Blueprint, render_template, jsonify
from .metrics import get_metrics_data, get_metrics_history

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
