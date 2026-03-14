"""
seed_demo.py — Populate CoreInventory with realistic demo data
Run AFTER first launch: python seed_demo.py
"""

from app import create_app
from database import db, User, Product, Category, Receipt, ReceiptLine, \
    DeliveryOrder, DeliveryLine, InternalTransfer, TransferLine, StockMove, Location
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # ── Users ──
    if not User.query.filter_by(email="admin@demo.com").first():
        u = User(name="Alex Johnson", email="admin@demo.com")
        u.set_password("demo1234")
        db.session.add(u)
        print("✓ Demo user created: admin@demo.com / demo1234")

    # ── Products ──
    cat_map = {c.name: c.id for c in Category.query.all()}

    demo_products = [
        ("Wireless Keyboard",     "WK-001", "Electronics",    "Units",  120, 20),
        ("USB-C Hub 7-Port",      "UC-002", "Electronics",    "Units",   85, 15),
        ("27\" Monitor",          "MN-003", "Electronics",    "Units",   18,  5),
        ("Ergonomic Office Chair","EC-004", "Furniture",      "Units",   22,  5),
        ("Standing Desk",         "SD-005", "Furniture",      "Units",    8,  3),
        ("Laptop Stand",          "LS-006", "Furniture",      "Units",   45, 10),
        ("Cotton T-Shirt M",      "CT-007", "Apparel",        "Units",  200, 30),
        ("Winter Jacket L",       "WJ-008", "Apparel",        "Units",   14,  5),
        ("Copper Wire 100m",      "CW-009", "Raw Materials",  "Rolls",   60, 10),
        ("Aluminium Sheet 1mm",   "AL-010", "Raw Materials",  "Kg",     340, 50),
        ("Bubble Wrap 50m",       "BW-011", "Packaging",      "Rolls",   33, 10),
        ("Cardboard Box A4",      "CB-012", "Packaging",      "Units",  510, 80),
        ("Bluetooth Mouse",       "BM-013", "Electronics",    "Units",    7, 10),  # low stock
        ("HDMI Cable 2m",         "HC-014", "Electronics",    "Units",    0,  5),  # out of stock
    ]

    created_products = []
    for name, sku, cat, uom, qty, threshold in demo_products:
        if not Product.query.filter_by(sku=sku).first():
            p = Product(
                name=name, sku=sku,
                category_id=cat_map.get(cat),
                uom=uom, stock_qty=qty,
                reorder_threshold=threshold
            )
            db.session.add(p)
            db.session.flush()
            if qty > 0:
                db.session.add(StockMove(
                    product_id=p.id, operation_type="adjustment",
                    qty_change=qty, reference="Initial Stock",
                    location="WH001/Stock", notes="Demo seed — opening balance",
                    date=datetime.utcnow() - timedelta(days=30)
                ))
            created_products.append(p)
            print(f"  + Product: {name} [{sku}]")

    db.session.commit()

    # ── Receipts ──
    all_products = Product.query.all()
    prod_map = {p.sku: p for p in all_products}

    receipts_data = [
        ("TechSupply Co.", "done",  [("WK-001", 50), ("UC-002", 30), ("BM-013", 20)], -10),
        ("FurniturePro",   "done",  [("EC-004", 10), ("LS-006", 25)], -7),
        ("RawMat Depot",   "ready", [("CW-009", 20), ("AL-010", 100)], -3),
        ("PackageWorld",   "draft", [("BW-011", 15), ("CB-012", 200)], -1),
    ]

    for i, (supplier, status, lines, days_offset) in enumerate(receipts_data):
        ref = f"REC/{datetime.now().strftime('%Y%m')}/{i+1:04d}"
        if not Receipt.query.filter_by(reference=ref).first():
            r = Receipt(
                reference=ref, supplier_name=supplier,
                status=status,
                created_at=datetime.utcnow() + timedelta(days=days_offset)
            )
            if status == "done":
                r.validated_at = datetime.utcnow() + timedelta(days=days_offset + 1)
            db.session.add(r)
            db.session.flush()

            for sku, qty in lines:
                p = prod_map.get(sku)
                if p:
                    rl = ReceiptLine(receipt_id=r.id, product_id=p.id,
                                     qty_ordered=qty, qty_received=qty if status == "done" else 0)
                    db.session.add(rl)
                    if status == "done":
                        db.session.add(StockMove(
                            product_id=p.id, operation_type="receipt",
                            qty_change=qty, reference=ref,
                            location="Suppliers → WH001/Stock",
                            notes=f"Receipt from {supplier}",
                            date=r.validated_at
                        ))
            print(f"  + Receipt: {ref} [{status}]")

    db.session.commit()

    # ── Deliveries ──
    deliveries_data = [
        ("Metro Retail",    "done",  [("WK-001", 20), ("UC-002", 10)], -8),
        ("OfficeMax Corp",  "packed",[("EC-004", 3),  ("LS-006", 8)],  -2),
        ("StartupHub",      "picked",[("MN-003", 2),  ("BM-013", 5)],  -1),
        ("City Library",    "draft", [("CB-012", 50)],                  0),
    ]

    for i, (customer, status, lines, days_offset) in enumerate(deliveries_data):
        ref = f"OUT/{datetime.now().strftime('%Y%m')}/{i+1:04d}"
        if not DeliveryOrder.query.filter_by(reference=ref).first():
            d = DeliveryOrder(
                reference=ref, customer_name=customer,
                status=status,
                created_at=datetime.utcnow() + timedelta(days=days_offset)
            )
            if status == "done":
                d.validated_at = datetime.utcnow() + timedelta(days=days_offset + 1)
            db.session.add(d)
            db.session.flush()

            for sku, qty in lines:
                p = prod_map.get(sku)
                if p:
                    dl = DeliveryLine(delivery_id=d.id, product_id=p.id,
                                      qty_ordered=qty, qty_done=qty if status == "done" else 0)
                    db.session.add(dl)
                    if status == "done":
                        db.session.add(StockMove(
                            product_id=p.id, operation_type="delivery",
                            qty_change=-qty, reference=ref,
                            location="WH001/Stock → Customers",
                            notes=f"Delivery to {customer}",
                            date=d.validated_at
                        ))
            print(f"  + Delivery: {ref} [{status}]")

    db.session.commit()

    # ── Internal Transfer ──
    locs = {l.name: l for l in Location.query.all()}
    input_loc  = locs.get("Input")
    stock_loc  = locs.get("Stock")
    output_loc = locs.get("Output")

    if input_loc and stock_loc:
        ref = f"INT/{datetime.now().strftime('%Y%m')}/0001"
        if not InternalTransfer.query.filter_by(reference=ref).first():
            t = InternalTransfer(
                reference=ref,
                from_location_id=input_loc.id,
                to_location_id=stock_loc.id,
                status="done",
                created_at=datetime.utcnow() - timedelta(days=5),
                validated_at=datetime.utcnow() - timedelta(days=5),
                notes="Moved from receiving bay to main stock"
            )
            db.session.add(t)
            db.session.flush()
            p = prod_map.get("WK-001")
            if p:
                tl = TransferLine(transfer_id=t.id, product_id=p.id, qty=30)
                db.session.add(tl)
                db.session.add(StockMove(
                    product_id=p.id, operation_type="transfer",
                    qty_change=0, reference=ref,
                    location="WH001/Input → WH001/Stock",
                    notes="Internal: 30 units moved from Input to Stock",
                    date=t.validated_at
                ))
            print(f"  + Transfer: {ref} [done]")

    db.session.commit()
    print("\n✅ Demo data seeded successfully!")
    print("   Login: admin@demo.com / demo1234")
