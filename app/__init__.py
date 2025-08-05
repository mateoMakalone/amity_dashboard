from flask import Flask

def create_app():
    app = Flask(__name__)
    # Удалён импорт DEBUG_MODE
    from .metrics import initialize_metrics
    initialize_metrics()
    from .routes import dashboard_bp
    app.register_blueprint(dashboard_bp)
    return app
