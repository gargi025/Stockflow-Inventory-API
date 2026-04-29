# StockFlow Inventory API

A small backend implementation for the **StockFlow B2B SaaS inventory management case study**.

This project focuses on the backend parts of the case study:

- product creation with validation and transactional safety
- database design for inventory across multiple warehouses
- supplier relationships
- bundle product modeling
- inventory history
- low-stock alert API

## Tech Stack

- Python
- Flask
- SQLAlchemy
- SQLite

SQLite is used to keep the take-home easy to run locally. In production, I would use PostgreSQL with migrations, stronger operational tooling, authentication, authorization, logging, and monitoring.

## Project Structure

```text
stockflow-inventory-api/
├── app.py
├── config.py
├── extensions.py
├── models.py
├── seed.py
├── schema.sql
├── requirements.txt
├── routes/
│   ├── __init__.py
│   ├── products.py
│   └── alerts.py
└── docs/
    └── CASE_STUDY_RESPONSE.md
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python seed.py
python app.py
```

The app runs on:

```text
http://127.0.0.1:5000
```

## Health Check

```bash
curl http://127.0.0.1:5000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## API 1: Create Product

```http
POST /api/companies/1/products
```

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/companies/1/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Mouse",
    "sku": "MOUSE-001",
    "price": "599.99",
    "warehouse_id": 1,
    "initial_quantity": 30,
    "supplier_id": 1,
    "product_type": "standard",
    "low_stock_threshold": 10
  }'
```

Expected response:

```json
{
  "message": "Product created",
  "product_id": 5
}
```

## API 2: Low-Stock Alerts

```http
GET /api/companies/1/alerts/low-stock
```

Example:

```bash
curl http://127.0.0.1:5000/api/companies/1/alerts/low-stock
```

Example response:

```json
{
  "alerts": [
    {
      "product_id": 3,
      "product_name": "Starter Kit Bundle",
      "sku": "KIT-001",
      "warehouse_id": 1,
      "warehouse_name": "Main Warehouse",
      "current_stock": 3,
      "threshold": 5,
      "days_until_stockout": 11,
      "supplier": {
        "id": 1,
        "name": "Supplier Corp",
        "contact_email": "orders@supplier.com"
      }
    }
  ],
  "total_alerts": 3
}
```

## Key Assumptions

1. SKU is globally unique across the platform.
2. A product belongs to one company.
3. A product can exist in multiple warehouses through the inventory table.
4. Recent sales activity means sales within the last 30 days.
5. Low-stock alerts are generated per product per warehouse.
6. Product-level threshold overrides product-type default threshold.
7. Supplier shown in the alert is the primary supplier.
8. Inventory history is stored in a transaction table.
9. Bundle products are modeled as normal products with component mappings.

## Design Notes

### Product and inventory are separate

I did not store `warehouse_id` on the product table because one product can exist in multiple warehouses. The inventory table is the relationship between products and warehouses.

### Transactions are used for product creation

Product creation and initial inventory creation should succeed or fail together. This prevents a product from existing without its initial inventory record.

### Current quantity and inventory history are both stored

The inventory table stores the latest quantity for fast reads. The inventory transactions table stores the audit history.

### Supplier relationship is many-to-many

A product can have multiple suppliers, and a supplier can provide many products. The `product_suppliers` table also supports primary supplier, supplier SKU, and lead time.

## Production Improvements

Given more time, I would add:

- Alembic migrations
- unit and integration tests
- JWT authentication
- role-based access control
- pagination for large alert lists
- background jobs for alert generation
- purchase order support
- reserved stock and damaged stock tracking
- structured logging
- request tracing
- Docker setup
- CI using GitHub Actions
