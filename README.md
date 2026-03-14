# CoreInventory 📦

A locally-runnable Inventory Management System prototype built with Python Flask,
SQLite, and Bootstrap. Simulates real ERP inventory lifecycle workflows.

---

## 📁 Project Structure

```
CoreInventory/
├── app.py                    # Flask app factory & entry point
├── database.py               # SQLAlchemy models + DB init
├── requirements.txt
├── seed_demo.py              # Optional: populate with demo data
│
├── routes/
│   ├── auth.py               # Signup, Login, OTP, Password reset
│   ├── dashboard.py          # KPI dashboard
│   ├── products.py           # Product CRUD
│   ├── receipts.py           # Incoming stock receipts
│   ├── deliveries.py         # Outgoing delivery orders
│   ├── transfers.py          # Internal transfers
│   ├── adjustments.py        # Inventory adjustment
│   ├── history.py            # Stock move ledger
│   └── settings.py           # Warehouse + profile settings
│
├── templates/
│   ├── base.html             # Sidebar layout shell
│   ├── auth/                 # login, signup, forgot_password, verify_otp, reset_password
│   ├── dashboard/            # KPI cards + timeline + category bars
│   ├── products/             # list, form, detail
│   ├── receipts/             # list, form, detail
│   ├── deliveries/           # list, form, detail
│   ├── transfers/            # list, form, detail
│   ├── adjustments/          # adjustment form + recent log
│   ├── history/              # paginated ledger with filters
│   └── settings/             # warehouse, categories, profile
│
└── static/
    └── css/
        └── main.css          # Full design system stylesheet
```

---

## ⚙️ Setup & Run

### 1. Prerequisites
- Python 3.9 or higher
- pip

### 2. Install dependencies

```bash
cd CoreInventory
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

The SQLite database (`instance/coreinventory.db`) is created automatically on
first run, along with default warehouse locations and product categories.

### 4. (Optional) Load demo data

```bash
python seed_demo.py
```

This creates:
- Demo user: `admin@demo.com` / `demo1234`
- 14 products across 5 categories (including low-stock and out-of-stock items)
- 4 receipts (done, ready, and draft)
- 4 delivery orders (done, packed, picked, draft)
- 1 validated internal transfer
- Full stock move history

---

## 🔐 Authentication

| Feature | Detail |
|---|---|
| Signup | Name, email (unique), password |
| Login | Email + password → session |
| Password Reset | Email → simulated OTP screen (always **1234**) → new password |
| Logout | Clears session |

---

## 🗄️ Database Tables

| Table | Purpose |
|---|---|
| `users` | Auth accounts |
| `products` | Product catalog with stock quantities |
| `categories` | Product categories |
| `warehouses` | Warehouse configuration |
| `locations` | Stock locations (internal/supplier/customer) |
| `receipts` + `receipt_lines` | Incoming stock documents |
| `delivery_orders` + `delivery_lines` | Outgoing stock documents |
| `internal_transfers` + `transfer_lines` | Location-to-location moves |
| `stock_moves` | Full audit ledger for every stock change |

---

## 🔄 Workflow Lifecycles

### Receipts (Incoming Stock)
```
Draft → Ready → Done (stock increases)
```

### Delivery Orders (Outgoing Stock)
```
Draft → Picked → Packed → Done (stock decreases)
```
- System blocks delivery if stock is insufficient

### Internal Transfers
```
Draft → Done (total stock unchanged, ledger entry created)
```

### Inventory Adjustment
- Select product → enter physical count → system calculates diff → updates stock + logs move

---

## 🎯 Suggested Hackathon Demo Flow

1. **Sign up** for a new account → log in
2. **Dashboard** — show KPI cards (zeros on fresh DB, or use seed data)
3. **Add a product** — e.g. "Wireless Keyboard", SKU: WK-001, Stock: 100
4. **Create a Receipt** from supplier → Mark Ready → Validate (stock increases)
5. **Check Products** — see updated stock
6. **Create a Delivery Order** → Pick → Pack → Validate (stock decreases)
7. **Try to over-deliver** — system blocks with error
8. **Create an Internal Transfer** → Validate → check Move History
9. **Run an Adjustment** — change counted qty → see diff calculated live
10. **Move History** — filter by operation type to show full audit trail
11. **Settings** — update warehouse info, add a category

---

## 🗓️ Suggested Git Commit Milestones

```
feat: initial project structure and Flask app factory
feat: database models (User, Product, Warehouse, Location, StockMove)
feat: authentication module (signup, login, OTP reset, logout)
feat: dashboard with KPI cards and stock move timeline
feat: product management (CRUD, search, stock status badges)
feat: receipts module (draft→ready→done lifecycle, stock update)
feat: delivery orders (pick/pack/validate, stock guard)
feat: internal transfers with ledger entry
feat: inventory adjustment with live diff calculation
feat: move history ledger with pagination and filters
feat: settings (warehouse config, categories, profile)
feat: seed_demo.py with realistic demo data
style: responsive sidebar, dark nav, status badges, CSS design system
docs: README with setup instructions and demo flow
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.9+, Flask 3.x |
| ORM | Flask-SQLAlchemy |
| Database | SQLite (file-based, zero config) |
| Frontend | HTML5, Bootstrap 5.3 |
| Icons | Font Awesome 6 |
| Fonts | Space Grotesk + JetBrains Mono |
| Auth | Flask sessions + Werkzeug password hashing |
| JS | Minimal vanilla JS (dynamic form lines, live diff) |

---

## 📝 Notes

- No cloud services required — runs 100% locally
- SQLite database resets cleanly if you delete `instance/coreinventory.db`
- Simulated OTP is always `1234` for demo purposes
- All timestamps stored in UTC
