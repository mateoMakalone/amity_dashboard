from flask import Flask

def create_app():
    app = Flask(__name__)
    # Удалён импорт DEBUG_MODE
    from .metrics import start_metrics_thread
    start_metrics_thread()
    from .routes import dashboard_bp
    app.register_blueprint(dashboard_bp)
    return app
