# Data dictionary

| Table | Primary key | Description |
|---|---|---|
| products | product_id | Manufactured SKUs |
| bom | bom_id | Product-to-material requirements |
| suppliers | supplier_id | Approved material suppliers |
| material_lot | material_lot_id | Incoming supplier material batches and derived balances |
| production_order | production_order_id | Manufacturing work orders |
| machines | machine_id | Production equipment |
| process_step | process_step_id | Ordered manufacturing operations |
| inspection_plan | inspection_plan_id | Quality characteristics and specification limits |
| inspection_result | inspection_result_id | Inspection measurements, quantities and calculated defect rates |
| material_consumption | consumption_id | Explicit lot consumption by production order |
| defect | defect_id | Defects linked to inspection, order, lot, step and machine |
| corrective_action | corrective_action_id | Corrective action lifecycle records |

`anomalies` is a separate labelled dataset and is deliberately not inserted into valid baseline tables.
