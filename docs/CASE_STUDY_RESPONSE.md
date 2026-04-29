# StockFlow Case Study Response

## Overall Approach

I approached this problem from three angles:

1. **Data correctness**: avoid invalid or partial product/inventory records.
2. **Multi-tenant isolation**: ensure company data does not leak across customers.
3. **Operational usefulness**: design inventory, supplier, and alert data in a way that supports real workflows like reordering and auditing.

Where requirements were incomplete, I made reasonable assumptions and documented what I would confirm with the product team.

---

# Part 1: Code Review and Debugging

## Issues Found

| Issue | Impact | Fix |
|---|---|---|
| No input validation | Missing or invalid data can crash the endpoint or create bad records. | Validate required and optional fields. |
| Direct use of `data['field']` | Missing keys raise runtime errors. | Use `.get()` and return clear 400 errors. |
| Two separate commits | Product may be created even if inventory insert fails. | Use one transaction. |
| Product stores `warehouse_id` | Incorrect because products can exist in multiple warehouses. | Store warehouse quantity in `inventory`. |
| No SKU uniqueness handling | Duplicate SKUs break product identification. | Add unique constraint and return 409. |
| No decimal handling for price | Money values may have floating-point errors. | Use Decimal/Numeric. |
| No company scoping | Data may leak across tenants. | Scope product creation by company. |
| No warehouse validation | Inventory may be created in another company's warehouse. | Validate warehouse belongs to company. |
| No initial quantity validation | Negative inventory can be inserted. | Check quantity is non-negative integer. |
| No inventory history | Cannot audit stock changes. | Add inventory transaction record. |
| No supplier validation | Product can reference invalid supplier. | Validate supplier belongs to company. |

## Main Reasoning

I considered storing `warehouse_id` directly on products, but rejected it because the requirement says products can exist in multiple warehouses. Therefore, inventory should be modeled as the join between product and warehouse.

I also considered committing the product first and inventory second, but that can leave partial data. In inventory systems, partial writes are risky because users may see a product with no stock record. Therefore, both writes should happen in one database transaction.

---

# Part 2: Database Design

## Tables

- companies
- warehouses
- products
- inventory
- inventory_transactions
- suppliers
- product_suppliers
- product_bundles
- sales

## Key Design Choices

### Product and warehouse relationship

Products and warehouses have a many-to-many relationship through inventory.

### Inventory history

I considered computing current stock only from transaction history, but chose to keep both:

- `inventory` for fast current-stock reads
- `inventory_transactions` for audit/history

This is a trade-off between normalization and performance.

### SKU uniqueness

I interpreted “unique across the platform” as globally unique. If the business later decides each company can reuse SKUs independently, I would change the constraint from:

```sql
UNIQUE(sku)
```

to:

```sql
UNIQUE(company_id, sku)
```

### Supplier relationship

Suppliers and products are many-to-many. A product can have multiple suppliers, and a supplier can provide many products.

### Bundles

A bundle is modeled as a product that contains other products through `product_bundles`.

## Questions for Product Team

1. Should SKU be globally unique or company-specific?
2. Should low-stock thresholds be per product, per product type, or per warehouse?
3. What exactly counts as recent sales activity?
4. Should alerts include incoming purchase orders?
5. Should inventory support reserved, damaged, returned, or in-transit stock?
6. Should bundles reduce stock from the bundle itself or from components?
7. Can bundles contain other bundles?
8. Should alerts be sent by email or only shown in dashboard?
9. Should low-stock alerts be real-time or calculated periodically?
10. Can inventory go negative for backorders?

---

# Part 3: Low-Stock Alert API

## Endpoint

```http
GET /api/companies/{company_id}/alerts/low-stock
```

## Assumptions

1. Recent sales means last 30 days.
2. Alerts are generated per product per warehouse.
3. Product-level threshold overrides product-type default threshold.
4. Only active products and warehouses are included.
5. Supplier shown is the primary supplier.
6. Days until stockout uses average daily sales over the last 30 days.

## Logic

1. Check if company exists.
2. Find product and warehouse combinations with sales in the last 30 days.
3. Join current inventory.
4. Join primary supplier information.
5. Compare current stock to threshold.
6. Calculate days until stockout.
7. Return sorted alerts.

## Edge Cases

| Edge Case | Handling |
|---|---|
| Company not found | Return 404. |
| Product has no recent sales | No alert. |
| Product has no supplier | Supplier is null. |
| Threshold missing | Use product-type default. |
| Stock is zero | Days until stockout is 0. |
| Product inactive | Exclude. |
| Warehouse inactive | Exclude. |
| DB failure | Return generic 500. |

## Trade-Offs

For readability, threshold comparison is done in Python after fetching candidate rows. In production, I would push more filtering into SQL or precompute alerts in a background job for larger companies.

For a small take-home implementation, live calculation is simpler and easier to reason about.

---

# Future Improvements

- Authentication and authorization
- PostgreSQL instead of SQLite
- Alembic migrations
- Unit tests
- API pagination
- Alert caching
- Background jobs
- Purchase order support
- Reserved stock support
- Better logging and monitoring
