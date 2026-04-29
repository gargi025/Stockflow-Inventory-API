from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import (
    Company,
    Inventory,
    InventoryTransaction,
    Product,
    ProductSupplier,
    Supplier,
    Warehouse,
)

products_bp = Blueprint("products", __name__)


@products_bp.route("/api/companies/<int:company_id>/products", methods=["POST"])
def create_product(company_id):
    """
    Create a product and its first inventory row safely.

    Key decisions:
    - The endpoint is company-scoped because this is a B2B SaaS app.
    - Product does not store warehouse_id directly because one product can exist
      in many warehouses.
    - Product creation and inventory creation happen in one transaction.
    """

    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json() or {}

    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404

    required_fields = ["name", "sku", "price", "warehouse_id"]
    missing_fields = [
        field for field in required_fields
        if data.get(field) in [None, ""]
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields
        }), 400

    name = str(data.get("name")).strip()
    sku = str(data.get("sku")).strip().upper()
    warehouse_id = data.get("warehouse_id")
    supplier_id = data.get("supplier_id")
    product_type = data.get("product_type", "standard")
    initial_quantity = data.get("initial_quantity", 0)
    low_stock_threshold = data.get("low_stock_threshold")

    try:
        price = Decimal(str(data.get("price")))
    except (InvalidOperation, TypeError):
        return jsonify({"error": "Invalid price format"}), 400

    if price < 0:
        return jsonify({"error": "Price cannot be negative"}), 400

    if not isinstance(initial_quantity, int) or initial_quantity < 0:
        return jsonify({
            "error": "Initial quantity must be a non-negative integer"
        }), 400

    if low_stock_threshold is not None:
        if not isinstance(low_stock_threshold, int) or low_stock_threshold < 0:
            return jsonify({
                "error": "Low stock threshold must be a non-negative integer"
            }), 400

    warehouse = Warehouse.query.filter_by(
        id=warehouse_id,
        company_id=company_id,
        is_active=True
    ).first()

    if not warehouse:
        return jsonify({
            "error": "Warehouse not found for this company"
        }), 404

    if Product.query.filter_by(sku=sku).first():
        return jsonify({"error": "SKU already exists"}), 409

    supplier = None
    if supplier_id is not None:
        supplier = Supplier.query.filter_by(
            id=supplier_id,
            company_id=company_id
        ).first()

        if not supplier:
            return jsonify({
                "error": "Supplier not found for this company"
            }), 404

    try:
        product = Product(
            company_id=company_id,
            name=name,
            sku=sku,
            price=price,
            product_type=product_type,
            low_stock_threshold=low_stock_threshold
        )

        db.session.add(product)
        db.session.flush()

        inventory = Inventory(
            product_id=product.id,
            warehouse_id=warehouse.id,
            quantity=initial_quantity
        )
        db.session.add(inventory)

        transaction = InventoryTransaction(
            product_id=product.id,
            warehouse_id=warehouse.id,
            change_quantity=initial_quantity,
            transaction_type="INITIAL_STOCK",
            reason="Product created"
        )
        db.session.add(transaction)

        if supplier:
            product_supplier = ProductSupplier(
                product_id=product.id,
                supplier_id=supplier.id,
                is_primary=True
            )
            db.session.add(product_supplier)

        db.session.commit()

        return jsonify({
            "message": "Product created",
            "product_id": product.id
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Database constraint failed"
        }), 409

    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Unexpected server error"
        }), 500
