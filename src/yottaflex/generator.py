from __future__ import annotations
import csv, json, random, sqlite3, hashlib
from pathlib import Path
from collections import defaultdict
from datetime import date, timedelta
from .config import GenerationConfig
from .ids import *

def _write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def _write_json(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

def build_dataset(cfg: GenerationConfig) -> dict[str, list[dict]]:
    rng = random.Random(cfg.seed)
    today = date(2026, 10, 30)
    products, boms, suppliers, lots = [], [], [], []
    machines, steps, orders, plans, results = [], [], [], [], []
    consumptions, defects, capas = [], [], []

    materials = [f"MAT-{i:04d}" for i in range(1, min(80, cfg.material_lots) + 1)]
    for i in range(1, cfg.products + 1):
        products.append({"product_id": sku_id(i), "product_name": f"Industrial Component {i:03d}",
                         "category": ["Assembly", "Electrical", "Mechanical", "Hydraulic"][i % 4],
                         "unit": "unit", "lifecycle_state": "ACTIVE"})
        chosen = rng.sample(materials, 3)
        for j, material in enumerate(chosen, 1):
            boms.append({"bom_id": f"BOM-{i:06d}-{j:02d}", "product_id": sku_id(i),
                         "material_code": material, "required_qty_per_unit": round(rng.uniform(0.5, 3.0), 3),
                         "effective_from": "2026-01-01", "effective_to": ""})

    for i in range(1, cfg.suppliers + 1):
        suppliers.append({"supplier_id": supplier_id(i), "supplier_name": f"Supplier {i:03d}",
                          "region": ["North", "South", "East", "West"][i % 4],
                          "status": "APPROVED"})

    for i in range(1, cfg.machines + 1):
        machines.append({"machine_id": machine_id(i), "machine_name": f"Production Machine {i:03d}",
                         "machine_type": ["CNC", "Press", "Molding", "Assembly"][i % 4],
                         "status": "ACTIVE"})

    for i in range(1, cfg.process_steps + 1):
        steps.append({"process_step_id": step_id(i), "step_name": ["Cutting", "Forming", "Machining",
            "Welding", "Assembly", "Finishing", "Testing", "Packaging"][i-1], "sequence_no": i})

    for i in range(1, cfg.material_lots + 1):
        sup_num = rng.randint(1, cfg.suppliers)
        sup = supplier_id(sup_num)
        # Guarantee at least one lot for every generated material, including scaled smoke runs.
        material = materials[i - 1] if i <= len(materials) else rng.choice(materials)
        qty = rng.randint(100000, 500000)
        received = today - timedelta(days=rng.randint(5, 270))
        lots.append({"material_lot_id": lot_id(sup, i), "supplier_id": sup, "material_code": material,
                     "received_qty": qty, "received_date": received.isoformat(),
                     "lot_status": "RELEASED", "unit": "kg"})

    # Pre-create inspection plans for each process step.
    for i, step in enumerate(steps, 1):
        plans.append({"inspection_plan_id": plan_id(i), "process_step_id": step["process_step_id"],
                      "characteristic": ["Dimension", "Surface finish", "Hardness", "Electrical resistance"][i % 4],
                      "lower_spec": 0.0, "upper_spec": 100.0, "unit": "index"})

    lots_by_material = defaultdict(list)
    for lot in lots:
        lots_by_material[lot["material_code"]].append(lot)

    lot_used = defaultdict(int)
    order_materials = {}
    for i in range(1, cfg.production_orders + 1):
        product = rng.choice(products)
        product_bom = [b for b in boms if b["product_id"] == product["product_id"]]
        qty = rng.randint(20, 250)
        start = today - timedelta(days=rng.randint(0, 180))
        end = start + timedelta(days=rng.randint(1, 5))
        order = {"production_order_id": order_id(i), "product_id": product["product_id"],
                 "planned_qty": qty, "produced_qty": qty - rng.randint(0, min(5, qty-1)),
                 "start_date": start.isoformat(), "end_date": end.isoformat(),
                 "status": "COMPLETED"}
        orders.append(order)
        used_lots = []
        for bom in product_bom:
            candidates = lots_by_material[bom["material_code"]]
            required = round(bom["required_qty_per_unit"] * qty, 3)
            # Pick the lot with the greatest remaining balance so each BOM line is
            # fulfilled by one lot; fail loudly rather than silently under-consuming.
            lot = max(candidates, key=lambda candidate:
                      candidate["received_qty"] - lot_used[candidate["material_lot_id"]])
            remaining = lot["received_qty"] - lot_used[lot["material_lot_id"]]
            if remaining < required:
                raise ValueError(f"Insufficient inventory to fulfil {bom['bom_id']}")
            lot_used[lot["material_lot_id"]] += required
            consumptions.append({"consumption_id": f"CONS-{i:06d}-{len(used_lots)+1:02d}",
                "production_order_id": order["production_order_id"], "material_lot_id": lot["material_lot_id"],
                "material_code": lot["material_code"], "required_qty": required,
                "consumed_qty": required, "unit": "kg"})
            used_lots.append(lot["material_lot_id"])
        order_materials[order["production_order_id"]] = used_lots

    # Four inspection records per order = exactly 20,000 at baseline volume.
    defect_counter = 0
    for i in range(1, cfg.inspection_results + 1):
        order_idx = ((i - 1) // 4) + 1
        order = orders[(order_idx - 1) % len(orders)]
        step = steps[(i - 1) % len(steps)]
        plan = plans[(i - 1) % len(plans)]
        machine = machines[(i - 1) % len(machines)]
        inspected = rng.randint(10, 50)
        failed = 0 if rng.random() > cfg.defects_rate else rng.randint(1, min(3, inspected))
        measured = round(rng.uniform(5, 95) if failed == 0 else rng.choice([rng.uniform(-5, -0.1), rng.uniform(100.1, 110)]), 3)
        result = {"inspection_result_id": result_id(i), "inspection_plan_id": plan["inspection_plan_id"],
                  "production_order_id": order["production_order_id"], "process_step_id": step["process_step_id"],
                  "machine_id": machine["machine_id"], "inspection_date": order["end_date"],
                  "inspected_qty": inspected, "defect_qty": failed, "measured_value": measured,
                  "result_status": "PASS" if failed == 0 else "FAIL",
                  "defect_rate": round(failed / inspected, 6)}
        results.append(result)
        if failed:
            defect_counter += 1
            linked_lots = order_materials[order["production_order_id"]]
            defects.append({"defect_id": defect_id(defect_counter), "inspection_result_id": result["inspection_result_id"],
                "production_order_id": order["production_order_id"], "material_lot_id": linked_lots[0],
                "process_step_id": step["process_step_id"], "machine_id": machine["machine_id"],
                "defect_qty": failed, "severity": rng.choice(["LOW", "MEDIUM", "HIGH"]),
                "status": "OPEN", "detected_date": result["inspection_date"]})
            capas.append({"corrective_action_id": capa_id(defect_counter), "defect_id": defect_id(defect_counter),
                "action_description": "Investigate root cause and implement corrective process control",
                "owner_role": "QUALITY_ENGINEER", "status": "OPEN", "opened_date": result["inspection_date"],
                "verified_date": "", "closed_date": ""})

    # Derived inventory balances are calculated from source consumption records.
    for lot in lots:
        lot["consumed_qty"] = round(lot_used[lot["material_lot_id"]], 3)
        lot["remaining_qty"] = round(lot["received_qty"] - lot["consumed_qty"], 3)
        if lot["remaining_qty"] < 0:
            raise ValueError(f"Negative inventory for {lot['material_lot_id']}")

    # Separate, labelled anomalies. Never contaminate valid baseline tables.
    anomalies = [
        {"anomaly_id":"ANOM-001","issue_type":"DEFECT_NONEXISTENT_LOT","ground_truth":"INVALID_FK",
         "description":"Defect points to LOT-UNKNOWN-999999, which does not exist."},
        {"anomaly_id":"ANOM-002","issue_type":"BOM_MATERIAL_NOT_CONSUMED","ground_truth":"RECONCILIATION_FAILURE",
         "description":"A BOM-required material is deliberately absent from an order's consumption rows."},
        {"anomaly_id":"ANOM-003","issue_type":"CAPA_CLOSED_BEFORE_VERIFICATION","ground_truth":"LIFECYCLE_VIOLATION",
         "description":"Corrective action is marked CLOSED with no verification timestamp."},
        {"anomaly_id":"ANOM-004","issue_type":"DEFECT_QTY_EXCEEDS_INSPECTED","ground_truth":"QUANTITY_VIOLATION",
         "description":"Defect quantity 12 exceeds inspected quantity 10."},
        {"anomaly_id":"ANOM-005","issue_type":"TRACEABILITY_CHAIN_BREAK","ground_truth":"MISSING_RELATIONSHIP",
         "description":"Production order references a deliberately missing material lot."}
    ]
    return {"products":products,"boms":boms,"suppliers":suppliers,"material_lots":lots,
            "production_orders":orders,"machines":machines,"process_steps":steps,
            "inspection_plans":plans,"inspection_results":results,"material_consumptions":consumptions,
            "defects":defects,"corrective_actions":capas,"anomalies":anomalies}

def export_dataset(data: dict[str, list[dict]], output: Path):
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in data.items():
        _write_csv(output / "csv" / f"{name}.csv", rows)
        _write_json(output / "json" / f"{name}.json", rows)
    from .schema import SCHEMA_SQL, DATA_DICTIONARY
    (output / "schema.sql").write_text(SCHEMA_SQL, encoding="utf-8")
    (output / "data_dictionary.md").write_text(DATA_DICTIONARY, encoding="utf-8")
    # Portable SQL seed file: schema followed by deterministic INSERT statements.
    sql_lines = [SCHEMA_SQL, "\n-- Deterministic baseline seed data; labelled anomalies are excluded.\n"]
    table_map_sql = {"products":"products","suppliers":"suppliers","machines":"machines",
                     "boms":"bom","material_lots":"material_lot","production_orders":"production_order",
                     "process_steps":"process_step","inspection_plans":"inspection_plan",
                     "material_consumptions":"material_consumption","inspection_results":"inspection_result",
                     "defects":"defect","corrective_actions":"corrective_action"}
    insert_order = ["products","suppliers","machines","process_steps","boms","material_lots",
                    "production_orders","inspection_plans","material_consumptions",
                    "inspection_results","defects","corrective_actions"]
    def sql_value(value):
        if value is None: return "NULL"
        if isinstance(value, (int, float)): return str(value)
        return "'" + str(value).replace("'", "''") + "'"
    for key in insert_order:
        rows = data[key]
        if not rows: continue
        table = table_map_sql[key]
        cols = list(rows[0].keys())
        col_sql = ",".join(cols)
        for row in rows:
            vals = ",".join(sql_value(row[col]) for col in cols)
            sql_lines.append(f"INSERT INTO {table} ({col_sql}) VALUES ({vals});\n")
    (output / "seed_data.sql").write_text("".join(sql_lines), encoding="utf-8")
    db = output / "yottaflex.sqlite3"
    if db.exists(): db.unlink()
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(SCHEMA_SQL)
        # Insert in dependency order; anomalies intentionally excluded.
        order = ["products","suppliers","machines","process_steps","boms","material_lots",
                 "production_orders","inspection_plans","material_consumptions",
                 "inspection_results","defects","corrective_actions"]
        table_map = {"products":"products","suppliers":"suppliers","machines":"machines",
                     "boms":"bom","material_lots":"material_lot","production_orders":"production_order",
                     "process_steps":"process_step","inspection_plans":"inspection_plan",
                     "inspection_results":"inspection_result","material_consumptions":"material_consumption",
                     "defects":"defect","corrective_actions":"corrective_action"}
        for key in order:
            rows = data[key]
            if not rows: continue
            table = table_map.get(key, key.rstrip("s"))
            cols = list(rows[0].keys())
            # SQLite schema uses same columns for baseline records.
            sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})"
            conn.executemany(sql, [[r[c] for c in cols] for r in rows])
    summary = {
        "seed": None,
        "record_counts": {k:len(v) for k,v in data.items()},
        "baseline_valid_tables": [k for k in data if k != "anomalies"],
        "anomalies_kept_separate": True
    }
    (output / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    manifest = []
    for p in sorted(output.rglob("*")):
        if p.is_file() and p.name != "manifest.sha256":
            manifest.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(output).as_posix()}")
    (output / "manifest.sha256").write_text("\n".join(manifest) + "\n", encoding="utf-8")
