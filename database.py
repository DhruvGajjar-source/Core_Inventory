from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship("Product", backref="category_rel", lazy=True)


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    uom = db.Column(db.String(50), default="Units")
    stock_qty = db.Column(db.Float, default=0)
    reorder_threshold = db.Column(db.Float, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def stock_status(self):
        if self.stock_qty <= 0:
            return "out"
        elif self.stock_qty <= self.reorder_threshold:
            return "low"
        return "ok"


class Warehouse(db.Model):
    __tablename__ = "warehouses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(300))
    locations = db.relationship("Location", backref="warehouse", lazy=True)


class Location(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location_type = db.Column(db.String(50), default="internal")  # internal, supplier, customer, virtual
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=True)
    full_name = db.Column(db.String(200))


class Receipt(db.Model):
    __tablename__ = "receipts"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    supplier_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default="draft")  # draft, ready, done
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    lines = db.relationship("ReceiptLine", backref="receipt", lazy=True, cascade="all, delete-orphan")


class ReceiptLine(db.Model):
    __tablename__ = "receipt_lines"
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey("receipts.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    qty_ordered = db.Column(db.Float, default=0)
    qty_received = db.Column(db.Float, default=0)
    product = db.relationship("Product")


class DeliveryOrder(db.Model):
    __tablename__ = "delivery_orders"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default="draft")  # draft, ready, picked, packed, done
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    lines = db.relationship("DeliveryLine", backref="delivery", lazy=True, cascade="all, delete-orphan")


class DeliveryLine(db.Model):
    __tablename__ = "delivery_lines"
    id = db.Column(db.Integer, primary_key=True)
    delivery_id = db.Column(db.Integer, db.ForeignKey("delivery_orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    qty_ordered = db.Column(db.Float, default=0)
    qty_done = db.Column(db.Float, default=0)
    product = db.relationship("Product")


class InternalTransfer(db.Model):
    __tablename__ = "internal_transfers"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    from_location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=True)
    to_location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=True)
    status = db.Column(db.String(20), default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    from_location = db.relationship("Location", foreign_keys=[from_location_id])
    to_location = db.relationship("Location", foreign_keys=[to_location_id])
    lines = db.relationship("TransferLine", backref="transfer", lazy=True, cascade="all, delete-orphan")


class TransferLine(db.Model):
    __tablename__ = "transfer_lines"
    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey("internal_transfers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    qty = db.Column(db.Float, default=0)
    product = db.relationship("Product")


class StockMove(db.Model):
    __tablename__ = "stock_moves"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    operation_type = db.Column(db.String(50))  # receipt, delivery, transfer, adjustment
    qty_change = db.Column(db.Float)
    reference = db.Column(db.String(100))
    location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    product = db.relationship("Product")


def init_db():
    db.create_all()
    # Seed default data if empty
    if not Warehouse.query.first():
        wh = Warehouse(name="Main Warehouse", code="WH001", address="123 Industrial Park")
        db.session.add(wh)
        db.session.flush()

        locs = [
            Location(name="Stock", location_type="internal", warehouse_id=wh.id, full_name="WH001/Stock"),
            Location(name="Input", location_type="internal", warehouse_id=wh.id, full_name="WH001/Input"),
            Location(name="Output", location_type="internal", warehouse_id=wh.id, full_name="WH001/Output"),
            Location(name="Suppliers", location_type="supplier", full_name="Suppliers"),
            Location(name="Customers", location_type="customer", full_name="Customers"),
        ]
        for l in locs:
            db.session.add(l)

        cats = ["Electronics", "Furniture", "Apparel", "Raw Materials", "Packaging"]
        for c in cats:
            db.session.add(Category(name=c))

        db.session.commit()
