"""Synthetic order-to-cash case data and answer keys."""

from __future__ import annotations

COMPANY_NAME = "Gem City Office Supply"

RAW_COLUMNS = (
    "OrderLineID",
    "OrderID",
    "OrderDate",
    "CustomerID",
    "CustomerName",
    "CustomerCity",
    "ProductID",
    "ProductName",
    "StandardPrice",
    "Quantity",
    "ActualUnitPrice",
)

RAW_ROWS = (
    ("OL01", "O5001", "2026-09-03", "C100", "Blue Ridge Design", "Dayton", "P100", "Ergonomic Chair", 325.00, 2, 310.00),
    ("OL02", "O5001", "2026-09-03", "C100", "Blue Ridge Design", "Dayton", "P200", "Desk Lamp", 85.00, 4, 80.00),
    ("OL03", "O5002", "2026-09-04", "C200", "Patterson Legal", "Kettering", "P300", "Standing Desk", 700.00, 1, 700.00),
    ("OL04", "O5003", "2026-09-06", "C100", "Blue Ridge Design", "Dayton", "P100", "Ergonomic Chair", 325.00, 1, 275.00),
    ("OL05", "O5003", "2026-09-06", "C100", "Blue Ridge Design", "Dayton", "P400", "Filing Cabinet", 240.00, 2, 240.00),
    ("OL06", "O5004", "2026-09-08", "C300", "Riverbend Health", "Oakwood", "P200", "Desk Lamp", 85.00, 10, 70.00),
)

GRAIN_OPTIONS = (
    "One customer",
    "One order",
    "One product",
    "One product line on one order",
)
GRAIN_CORRECT = "One product line on one order"

KEY_OPTIONS = (
    "OrderID",
    "ProductID",
    "OrderID plus ProductID",
    "OrderLineID",
)
KEY_CORRECT = "OrderLineID"

ANOMALIES = (
    {
        "id": "insert_customer",
        "scenario": "Gem City Office Supply wants to add a new customer before that customer places an order, but the flat table requires an OrderID and ProductID.",
        "correct": "Insertion anomaly",
        "explanation": "The structure makes one fact depend on an unrelated transaction. A Customers table would let Gem City Office Supply add the customer independently.",
    },
    {
        "id": "update_city",
        "scenario": "Blue Ridge Design moves to Beavercreek. Its city appears on three order-line rows, and only two rows are changed.",
        "correct": "Update anomaly",
        "explanation": "The same customer fact is repeated. Partial updates leave conflicting versions of the customer's city.",
    },
    {
        "id": "delete_product",
        "scenario": "The last order line containing Standing Desk is deleted. The only stored product name and standard price disappear too.",
        "correct": "Deletion anomaly",
        "explanation": "Deleting a transaction also removes a master-data fact that should remain available in a Products table.",
    },
)
ANOMALY_OPTIONS = ("Insertion anomaly", "Update anomaly", "Deletion anomaly")

FIELD_ASSIGNMENTS = (
    ("CustomerName", "Customers", "The name describes the customer identified by CustomerID."),
    ("CustomerCity", "Customers", "The city is a current customer master-data fact."),
    ("OrderDate", "Orders", "The date describes the order identified by OrderID."),
    ("ProductName", "Products", "The product name describes ProductID, not a particular sale."),
    ("StandardPrice", "Products", "The standard price is current product master data."),
    ("Quantity", "OrderLines", "Quantity describes one product's participation in one order."),
    ("ActualUnitPrice", "OrderLines", "The price actually charged is a historical fact about that order line."),
)
TABLE_OPTIONS = ("Customers", "Orders", "Products", "OrderLines")

ER_PROMPTS = (
    ("customers_orders", "Customers to Orders", "One customer can place many orders; each order belongs to one customer.", "1 to many"),
    ("orders_lines", "Orders to OrderLines", "One order can contain many lines; each line belongs to one order.", "1 to many"),
    ("products_lines", "Products to OrderLines", "One product can appear on many lines; each line identifies one product.", "1 to many"),
    ("foreign_keys", "Where do OrderID and ProductID foreign keys belong?", "The child junction row points to both parent records.", "OrderLines"),
)
ER_RELATIONSHIP_OPTIONS = ("1 to 1", "1 to many", "many to many")
ER_FOREIGN_KEY_OPTIONS = ("Orders", "Products", "OrderLines", "Customers")

REA_ITEMS = (
    ("Inventory", "Resource", "Inventory is an economic resource that decreases when a sale occurs."),
    ("Cash", "Resource", "Cash is the economic resource received from the customer."),
    ("Sale", "Event", "The sale is the give event in which inventory is transferred."),
    ("Cash Receipt", "Event", "The cash receipt is the receive event paired with the sale."),
    ("Customer", "Agent", "The customer is the external agent participating in both events."),
    ("Employee", "Agent", "The employee is the internal agent responsible for the event."),
)
REA_OPTIONS = ("Resource", "Event", "Agent")

NORMALIZED_TABLES = {
    "Customers": ("CustomerID PK", "CustomerName", "CustomerCity"),
    "Orders": ("OrderID PK", "OrderDate", "CustomerID FK"),
    "Products": ("ProductID PK", "ProductName", "StandardPrice"),
    "OrderLines": ("OrderLineID PK", "OrderID FK", "ProductID FK", "Quantity", "ActualUnitPrice"),
}
