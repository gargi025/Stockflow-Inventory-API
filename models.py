from datetime import datetime
from extensions import db


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    warehouses = db.relationship("Warehouse", backref="company", lazy=True)
    products = db.relationship("Product", backref="company", lazy=True)
    suppliers = db.relationship("Supplier", backref="company", lazy=True)


class Warehouse(db.Model):
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        index=True
    )
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        index=True
    )
    name = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        index=True
    )
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    product_type = db.Column(db.String(50), nullable=False, default="standard")
    low_stock_threshold = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    inventory_records = db.relationship("Inventory", backref="product", lazy=True)


class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True
    )
    warehouse_id = db.Column(
        db.Integer,
        db.ForeignKey("warehouses.id"),
        nullable=False,
        index=True
    )
    quantity = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    warehouse = db.relationship("Warehouse", backref="inventory_records")

    __table_args__ = (
        db.UniqueConstraint(
            "product_id",
            "warehouse_id",
            name="uq_inventory_product_warehouse"
        ),
        db.CheckConstraint("quantity >= 0", name="chk_inventory_quantity_non_negative"),
    )


class InventoryTransaction(db.Model):
    __tablename__ = "inventory_transactions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    change_quantity = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ProductSupplier(db.Model):
    __tablename__ = "product_suppliers"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True
    )
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=False,
        index=True
    )
    supplier_sku = db.Column(db.String(100))
    lead_time_days = db.Column(db.Integer, default=7)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)

    product = db.relationship("Product", backref="supplier_links")
    supplier = db.relationship("Supplier", backref="product_links")

    __table_args__ = (
        db.UniqueConstraint(
            "product_id",
            "supplier_id",
            name="uq_product_supplier"
        ),
    )


class ProductBundle(db.Model):
    __tablename__ = "product_bundles"

    id = db.Column(db.Integer, primary_key=True)
    bundle_product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True
    )
    component_product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True
    )
    component_quantity = db.Column(db.Integer, nullable=False)

    bundle_product = db.relationship(
        "Product",
        foreign_keys=[bundle_product_id],
        backref="bundle_components"
    )
    component_product = db.relationship(
        "Product",
        foreign_keys=[component_product_id]
    )

    __table_args__ = (
        db.UniqueConstraint(
            "bundle_product_id",
            "component_product_id",
            name="uq_bundle_component"
        ),
        db.CheckConstraint(
            "bundle_product_id <> component_product_id",
            name="chk_bundle_not_self"
        ),
        db.CheckConstraint(
            "component_quantity > 0",
            name="chk_component_quantity_positive"
        ),
    )


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True
    )
    warehouse_id = db.Column(
        db.Integer,
        db.ForeignKey("warehouses.id"),
        nullable=False,
        index=True
    )
    quantity = db.Column(db.Integer, nullable=False)
    sold_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    product = db.relationship("Product", backref="sales")
    warehouse = db.relationship("Warehouse", backref="sales")

    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="chk_sale_quantity_positive"),
    )
