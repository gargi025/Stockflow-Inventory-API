from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app
from extensions import db
from models import (
    Company,
    Inventory,
    InventoryTransaction,
    Product,
    ProductBundle,
    ProductSupplier,
    Sale,
    Supplier,
    Warehouse,
)


def seed():
    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

        company = Company(name="Acme Retail Pvt Ltd")
        db.session.add(company)
        db.session.flush()

        main_warehouse = Warehouse(
            company_id=company.id,
            name="Main Warehouse",
            address="Pune"
        )
        backup_warehouse = Warehouse(
            company_id=company.id,
            name="Backup Warehouse",
            address="Mumbai"
        )
        db.session.add_all([main_warehouse, backup_warehouse])
        db.session.flush()

        supplier_1 = Supplier(
            company_id=company.id,
            name="Supplier Corp",
            contact_email="orders@supplier.com",
            phone="+91-9876543210"
        )
        supplier_2 = Supplier(
            company_id=company.id,
            name="Packaging World",
            contact_email="sales@packagingworld.com"
        )
        db.session.add_all([supplier_1, supplier_2])
        db.session.flush()

        widget = Product(
            company_id=company.id,
            name="Widget A",
            sku="WID-001",
            price=Decimal("199.99"),
            product_type="fast_moving",
            low_stock_threshold=20
        )

        cable = Product(
            company_id=company.id,
            name="USB Cable",
            sku="USB-001",
            price=Decimal("99.00"),
            product_type="standard",
            low_stock_threshold=10
        )

        kit = Product(
            company_id=company.id,
            name="Starter Kit Bundle",
            sku="KIT-001",
            price=Decimal("399.00"),
            product_type="bundle",
            low_stock_threshold=5
        )

        no_alert_product = Product(
            company_id=company.id,
            name="Notebook Pack",
            sku="NOTE-001",
            price=Decimal("149.00"),
            product_type="standard",
            low_stock_threshold=10
        )

        db.session.add_all([widget, cable, kit, no_alert_product])
        db.session.flush()

        db.session.add_all([
            ProductSupplier(
                product_id=widget.id,
                supplier_id=supplier_1.id,
                supplier_sku="SUP-WID-001",
                lead_time_days=7,
                is_primary=True
            ),
            ProductSupplier(
                product_id=cable.id,
                supplier_id=supplier_2.id,
                supplier_sku="SUP-USB-001",
                lead_time_days=5,
                is_primary=True
            ),
            ProductSupplier(
                product_id=kit.id,
                supplier_id=supplier_1.id,
                supplier_sku="SUP-KIT-001",
                lead_time_days=10,
                is_primary=True
            )
        ])

        db.session.add_all([
            ProductBundle(
                bundle_product_id=kit.id,
                component_product_id=widget.id,
                component_quantity=1
            ),
            ProductBundle(
                bundle_product_id=kit.id,
                component_product_id=cable.id,
                component_quantity=2
            )
        ])

        db.session.add_all([
            Inventory(
                product_id=widget.id,
                warehouse_id=main_warehouse.id,
                quantity=5
            ),
            Inventory(
                product_id=widget.id,
                warehouse_id=backup_warehouse.id,
                quantity=100
            ),
            Inventory(
                product_id=cable.id,
                warehouse_id=main_warehouse.id,
                quantity=8
            ),
            Inventory(
                product_id=kit.id,
                warehouse_id=main_warehouse.id,
                quantity=3
            ),
            Inventory(
                product_id=no_alert_product.id,
                warehouse_id=main_warehouse.id,
                quantity=30
            )
        ])

        db.session.add_all([
            InventoryTransaction(
                product_id=widget.id,
                warehouse_id=main_warehouse.id,
                change_quantity=5,
                transaction_type="INITIAL_STOCK",
                reason="Seed data"
            ),
            InventoryTransaction(
                product_id=cable.id,
                warehouse_id=main_warehouse.id,
                change_quantity=8,
                transaction_type="INITIAL_STOCK",
                reason="Seed data"
            ),
            InventoryTransaction(
                product_id=kit.id,
                warehouse_id=main_warehouse.id,
                change_quantity=3,
                transaction_type="INITIAL_STOCK",
                reason="Seed data"
            )
        ])

        now = datetime.utcnow()

        db.session.add_all([
            Sale(
                company_id=company.id,
                product_id=widget.id,
                warehouse_id=main_warehouse.id,
                quantity=40,
                sold_at=now - timedelta(days=10)
            ),
            Sale(
                company_id=company.id,
                product_id=cable.id,
                warehouse_id=main_warehouse.id,
                quantity=15,
                sold_at=now - timedelta(days=7)
            ),
            Sale(
                company_id=company.id,
                product_id=kit.id,
                warehouse_id=main_warehouse.id,
                quantity=8,
                sold_at=now - timedelta(days=3)
            ),
            Sale(
                company_id=company.id,
                product_id=no_alert_product.id,
                warehouse_id=main_warehouse.id,
                quantity=10,
                sold_at=now - timedelta(days=5)
            )
        ])

        db.session.commit()

        print("Database seeded successfully.")
        print("Company ID:", company.id)
        print("Try: GET /api/companies/1/alerts/low-stock")


if __name__ == "__main__":
    seed()
