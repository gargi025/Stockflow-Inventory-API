from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from sqlalchemy import func

from models import (
    Company,
    Inventory,
    Product,
    ProductSupplier,
    Sale,
    Supplier,
    Warehouse,
)
from extensions import db

alerts_bp = Blueprint("alerts", __name__)

RECENT_SALES_DAYS = 30

PRODUCT_TYPE_THRESHOLDS = {
    "standard": 10,
    "fast_moving": 25,
    "perishable": 15,
    "bundle": 5
}


@alerts_bp.route("/api/companies/<int:company_id>/alerts/low-stock", methods=["GET"])
def get_low_stock_alerts(company_id):
    """
    Return low-stock alerts for a company.

    Alert logic:
    - alert per product per warehouse
    - include only active products and warehouses
    - include only products with sales in the last 30 days
    - compare current stock with product threshold
    - include primary supplier when available
    """

    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404

    recent_start_date = datetime.utcnow() - timedelta(days=RECENT_SALES_DAYS)

    try:
        recent_sales = (
            db.session.query(
                Sale.product_id.label("product_id"),
                Sale.warehouse_id.label("warehouse_id"),
                func.sum(Sale.quantity).label("total_sold")
            )
            .filter(
                Sale.company_id == company_id,
                Sale.sold_at >= recent_start_date
            )
            .group_by(Sale.product_id, Sale.warehouse_id)
            .subquery()
        )

        primary_supplier = (
            db.session.query(
                ProductSupplier.product_id.label("product_id"),
                Supplier.id.label("supplier_id"),
                Supplier.name.label("supplier_name"),
                Supplier.contact_email.label("supplier_contact_email")
            )
            .join(Supplier, Supplier.id == ProductSupplier.supplier_id)
            .filter(ProductSupplier.is_primary.is_(True))
            .subquery()
        )

        rows = (
            db.session.query(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Product.sku.label("sku"),
                Product.product_type.label("product_type"),
                Product.low_stock_threshold.label("product_threshold"),
                Warehouse.id.label("warehouse_id"),
                Warehouse.name.label("warehouse_name"),
                Inventory.quantity.label("current_stock"),
                recent_sales.c.total_sold.label("total_sold"),
                primary_supplier.c.supplier_id.label("supplier_id"),
                primary_supplier.c.supplier_name.label("supplier_name"),
                primary_supplier.c.supplier_contact_email.label("supplier_contact_email")
            )
            .join(Inventory, Inventory.product_id == Product.id)
            .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
            .join(
                recent_sales,
                (recent_sales.c.product_id == Product.id) &
                (recent_sales.c.warehouse_id == Warehouse.id)
            )
            .outerjoin(
                primary_supplier,
                primary_supplier.c.product_id == Product.id
            )
            .filter(
                Product.company_id == company_id,
                Warehouse.company_id == company_id,
                Product.is_active.is_(True),
                Warehouse.is_active.is_(True)
            )
            .all()
        )

        alerts = []

        for row in rows:
            threshold = row.product_threshold
            if threshold is None:
                threshold = PRODUCT_TYPE_THRESHOLDS.get(row.product_type, 10)

            if row.current_stock >= threshold:
                continue

            average_daily_sales = float(row.total_sold) / RECENT_SALES_DAYS

            if average_daily_sales > 0:
                days_until_stockout = int(row.current_stock / average_daily_sales)
            else:
                days_until_stockout = None

            supplier = None
            if row.supplier_id:
                supplier = {
                    "id": row.supplier_id,
                    "name": row.supplier_name,
                    "contact_email": row.supplier_contact_email
                }

            alerts.append({
                "product_id": row.product_id,
                "product_name": row.product_name,
                "sku": row.sku,
                "warehouse_id": row.warehouse_id,
                "warehouse_name": row.warehouse_name,
                "current_stock": row.current_stock,
                "threshold": threshold,
                "days_until_stockout": days_until_stockout,
                "supplier": supplier
            })

        alerts.sort(key=lambda alert: (
            alert["days_until_stockout"] is None,
            alert["days_until_stockout"] if alert["days_until_stockout"] is not None else 999999,
            alert["current_stock"]
        ))

        return jsonify({
            "alerts": alerts,
            "total_alerts": len(alerts)
        }), 200

    except Exception:
        return jsonify({
            "error": "Failed to fetch low-stock alerts"
        }), 500
