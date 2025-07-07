from flask import Flask

def create_app():
    app = Flask(__name__)
    from .config import DASHBOARD_DEBUG

    if DASHBOARD_DEBUG:
        from flask import jsonify, render_template
        import random, time
        from .config import METRICS_CONFIG, PROMINENT_METRICS

        @app.route("/")
        def dashboard():
            return render_template("dashboard.html")

        @app.route("/data")
        def mock_data():
            metrics = {}
            for cat in METRICS_CONFIG:
                for pattern in cat['metrics']:
                    base = pattern.replace('.*', 'test')
                    metrics[base] = random.uniform(0, 100)
            for key in PROMINENT_METRICS:
                if key not in metrics:
                    metrics[key] = random.uniform(0, 100)
            data = {
                'metrics': metrics,
                'prominent': PROMINENT_METRICS,
                'config': METRICS_CONFIG,
                'last_updated': int(random.randint(1600000000, 1700000000)),
                'error': None
            }
            return jsonify(data)

        @app.route("/history")
        def mock_history():
            now = int(time.time())
            history = {}
            # Добавляем историю для всех метрик из секции System
            system_patterns = []
            for cat in METRICS_CONFIG:
                if cat["category"] == "System":
                    system_patterns.extend(cat["metrics"])
            for pattern in system_patterns:
                base = pattern.replace('.*', 'test')
                history[base] = [[now - i * 60, random.uniform(0, 100)] for i in reversed(range(60))]
            # Также добавляем историю для PROMINENT_METRICS (чтобы не сломать KPI)
            for key in PROMINENT_METRICS:
                if key not in history:
                    history[key] = [[now - i * 60, random.uniform(0, 100)] for i in reversed(range(60))]
            return jsonify(history)
    else:
        from .routes import dashboard_bp
        app.register_blueprint(dashboard_bp)

    return app
