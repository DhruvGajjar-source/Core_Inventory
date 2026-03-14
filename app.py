# Load .env FIRST — before any other imports read os.environ
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
from flask import Flask
from database import db, init_db
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.products import products_bp
from routes.receipts import receipts_bp
from routes.deliveries import deliveries_bp
from routes.transfers import transfers_bp
from routes.adjustments import adjustments_bp
from routes.history import history_bp
from routes.settings import settings_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "coreinventory-secret-2024")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///coreinventory.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(receipts_bp)
    app.register_blueprint(deliveries_bp)
    app.register_blueprint(transfers_bp)
    app.register_blueprint(adjustments_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(settings_bp)

    import config as cfg

    @app.context_processor
    def inject_globals():
        from flask import session as flask_session
        ctx = {"config": cfg}
        if flask_session.get("user_id"):
            try:
                from database import Product, Receipt, DeliveryOrder
                ctx["pending_receipts_count"] = Receipt.query.filter(
                    Receipt.status.in_(["draft", "ready"])).count()
                ctx["pending_deliveries_count"] = DeliveryOrder.query.filter(
                    DeliveryOrder.status.in_(["draft", "ready", "picked", "packed"])).count()
                ctx["low_stock_count"] = Product.query.filter(
                    Product.stock_qty <= Product.reorder_threshold,
                    Product.stock_qty > 0).count()
            except Exception:
                pass
        return ctx

    with app.app_context():
        init_db()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
