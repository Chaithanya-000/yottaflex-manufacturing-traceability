SCHEMA_SQL = """
PRAGMA foreign_keys=ON;

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL
);

CREATE TABLE suppliers (
    supplier_id TEXT PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    region TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE machines (
    machine_id TEXT PRIMARY KEY,
    machine_name TEXT NOT NULL,
    machine_type TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE process_step (
    process_step_id TEXT PRIMARY KEY,
    step_name TEXT NOT NULL,
    sequence_no INTEGER NOT NULL UNIQUE
);

CREATE TABLE bom (
    bom_id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    material_code TEXT NOT NULL,
    required_qty_per_unit REAL NOT NULL CHECK(required_qty_per_unit > 0),
    effective_from TEXT NOT NULL,
    effective_to TEXT
);

CREATE TABLE material_lot (
    material_lot_id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
    material_code TEXT NOT NULL,
    received_qty INTEGER NOT NULL CHECK(received_qty > 0),
    received_date TEXT NOT NULL,
    lot_status TEXT NOT NULL,
    unit TEXT NOT NULL,
    consumed_qty REAL NOT NULL CHECK(consumed_qty >= 0),
    remaining_qty REAL NOT NULL CHECK(remaining_qty >= 0)
);

CREATE TABLE production_order (
    production_order_id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    planned_qty INTEGER NOT NULL CHECK(planned_qty > 0),
    produced_qty INTEGER NOT NULL CHECK(produced_qty >= 0),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE inspection_plan (
    inspection_plan_id TEXT PRIMARY KEY,
    process_step_id TEXT NOT NULL REFERENCES process_step(process_step_id),
    characteristic TEXT NOT NULL,
    lower_spec REAL NOT NULL,
    upper_spec REAL NOT NULL CHECK(upper_spec >= lower_spec),
    unit TEXT NOT NULL
);

CREATE TABLE material_consumption (
    consumption_id TEXT PRIMARY KEY,
    production_order_id TEXT NOT NULL REFERENCES production_order(production_order_id),
    material_lot_id TEXT NOT NULL REFERENCES material_lot(material_lot_id),
    material_code TEXT NOT NULL,
    required_qty REAL NOT NULL CHECK(required_qty > 0),
    consumed_qty REAL NOT NULL CHECK(consumed_qty >= 0),
    unit TEXT NOT NULL
);

CREATE TABLE inspection_result (
    inspection_result_id TEXT PRIMARY KEY,
    inspection_plan_id TEXT NOT NULL REFERENCES inspection_plan(inspection_plan_id),
    production_order_id TEXT NOT NULL REFERENCES production_order(production_order_id),
    process_step_id TEXT NOT NULL REFERENCES process_step(process_step_id),
    machine_id TEXT NOT NULL REFERENCES machines(machine_id),
    inspection_date TEXT NOT NULL,
    inspected_qty INTEGER NOT NULL CHECK(inspected_qty > 0),
    defect_qty INTEGER NOT NULL CHECK(defect_qty >= 0 AND defect_qty <= inspected_qty),
    measured_value REAL NOT NULL,
    result_status TEXT NOT NULL,
    defect_rate REAL NOT NULL
);

CREATE TABLE defect (
    defect_id TEXT PRIMARY KEY,
    inspection_result_id TEXT NOT NULL REFERENCES inspection_result(inspection_result_id),
    production_order_id TEXT NOT NULL REFERENCES production_order(production_order_id),
    material_lot_id TEXT NOT NULL REFERENCES material_lot(material_lot_id),
    process_step_id TEXT NOT NULL REFERENCES process_step(process_step_id),
    machine_id TEXT NOT NULL REFERENCES machines(machine_id),
    defect_qty INTEGER NOT NULL CHECK(defect_qty > 0),
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    detected_date TEXT NOT NULL
);

CREATE TABLE corrective_action (
    corrective_action_id TEXT PRIMARY KEY,
    defect_id TEXT NOT NULL REFERENCES defect(defect_id),
    action_description TEXT NOT NULL,
    owner_role TEXT NOT NULL,
    status TEXT NOT NULL,
    opened_date TEXT NOT NULL,
    verified_date TEXT,
    closed_date TEXT
);
"""


DATA_DICTIONARY = """# Data Dictionary

This document describes the 12 relational tables in the YottaFlex manufacturing traceability database.

## 1. Products and Manufacturing Setup

| Table | Primary Key | Columns | Description |
|---|---|---|---|
| products | product_id | product_name, category, unit, lifecycle_state | Manufactured products and their lifecycle details. |
| bom | bom_id | product_id, material_code, required_qty_per_unit, effective_from, effective_to | Bill of Materials defining material requirements for each product. |
| process_step | process_step_id | step_name, sequence_no | Ordered manufacturing operations. |
| machines | machine_id | machine_name, machine_type, status | Production equipment and operational status. |

## 2. Suppliers and Materials

| Table | Primary Key | Columns | Description |
|---|---|---|---|
| suppliers | supplier_id | supplier_name, region, status | Approved material suppliers. |
| material_lot | material_lot_id | supplier_id, material_code, received_qty, received_date, lot_status, unit, consumed_qty, remaining_qty | Incoming supplier material batches and their quantity balances. |
| material_consumption | consumption_id | production_order_id, material_lot_id, material_code, required_qty, consumed_qty, unit | Material quantities consumed from specific lots for production orders. |

## 3. Production and Quality

| Table | Primary Key | Columns | Description |
|---|---|---|---|
| production_order | production_order_id | product_id, planned_qty, produced_qty, start_date, end_date, status | Manufacturing work orders and production quantities. |
| inspection_plan | inspection_plan_id | process_step_id, characteristic, lower_spec, upper_spec, unit | Quality inspection characteristics and specification limits. |
| inspection_result | inspection_result_id | inspection_plan_id, production_order_id, process_step_id, machine_id, inspection_date, inspected_qty, defect_qty, measured_value, result_status, defect_rate | Inspection measurements, quantities and calculated defect rates. |
| defect | defect_id | inspection_result_id, production_order_id, material_lot_id, process_step_id, machine_id, defect_qty, severity, status, detected_date | Manufacturing defects linked to inspection and traceability records. |
| corrective_action | corrective_action_id | defect_id, action_description, owner_role, status, opened_date, verified_date, closed_date | Corrective action ownership, status and lifecycle dates. |

## 4. Relationships

- `bom.product_id` references `products.product_id`.
- `material_lot.supplier_id` references `suppliers.supplier_id`.
- `production_order.product_id` references `products.product_id`.
- `inspection_plan.process_step_id` references `process_step.process_step_id`.
- `material_consumption.production_order_id` references `production_order.production_order_id`.
- `material_consumption.material_lot_id` references `material_lot.material_lot_id`.
- `inspection_result` references inspection plans, production orders, process steps and machines.
- `defect` references inspection results, production orders, material lots, process steps and machines.
- `corrective_action.defect_id` references `defect.defect_id`.

## 5. Anomaly Dataset

`anomalies` is a separate labelled dataset. It describes five deliberately designed traceability and data-integrity scenarios. These anomaly labels are not inserted into the valid baseline relational tables.
"""