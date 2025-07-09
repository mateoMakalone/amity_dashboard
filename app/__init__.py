from flask import Flask

def create_app():
    app = Flask(__name__)
    from .config import DEBUG_MODE

    # Инициализируем метрики при старте
    from .metrics import start_metrics_thread
    start_metrics_thread()

    if DEBUG_MODE:
        from flask import jsonify, render_template
        from .metrics import get_metrics_data, get_metrics_history

        @app.route("/")
        def dashboard():
            return render_template("dashboard.html")

        @app.route("/data")
        def mock_data():
            return jsonify(get_metrics_data())

        @app.route("/history")
        def mock_history():
            return jsonify(get_metrics_history())
    else:
        from .routes import dashboard_bp
        app.register_blueprint(dashboard_bp)

    return app
