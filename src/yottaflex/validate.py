import argparse, csv, json
from pathlib import Path

def validate(input_dir: Path):
    base = input_dir / "csv"
    read = lambda name: list(csv.DictReader((base / f"{name}.csv").open(encoding="utf-8")))
    products, suppliers, lots = read("products"), read("suppliers"), read("material_lots")
    orders, results = read("production_orders"), read("inspection_results")
    consumptions, defects, capas = read("material_consumptions"), read("defects"), read("corrective_actions")
    checks = {}
    checks["unique_product_ids"] = len({r["product_id"] for r in products}) == len(products)
    checks["unique_supplier_ids"] = len({r["supplier_id"] for r in suppliers}) == len(suppliers)
    checks["unique_lot_ids"] = len({r["material_lot_id"] for r in lots}) == len(lots)
    supplier_ids = {r["supplier_id"] for r in suppliers}
    lot_ids = {r["material_lot_id"] for r in lots}
    order_ids = {r["production_order_id"] for r in orders}
    checks["lot_supplier_fk"] = all(r["supplier_id"] in supplier_ids for r in lots)
    checks["consumption_order_fk"] = all(r["production_order_id"] in order_ids for r in consumptions)
    checks["consumption_lot_fk"] = all(r["material_lot_id"] in lot_ids for r in consumptions)
    checks["bom_consumption_reconciles"] = all(abs(float(r["required_qty"])-float(r["consumed_qty"])) < 1e-6 for r in consumptions)
    checks["inspection_order_fk"] = all(r["production_order_id"] in order_ids for r in results)
    checks["inspection_quantity_bounds"] = all(0 <= int(r["defect_qty"]) <= int(r["inspected_qty"]) for r in results)
    checks["defect_rate_reconciles"] = all(abs(float(r["defect_rate"])-int(r["defect_qty"])/int(r["inspected_qty"])) < 1e-6 for r in results)
    checks["nonnegative_inventory"] = all(float(r["remaining_qty"]) >= 0 for r in lots)
    checks["defect_order_fk"] = all(r["production_order_id"] in order_ids for r in defects)
    checks["defect_lot_fk"] = all(r["material_lot_id"] in lot_ids for r in defects)
    checks["capa_defect_fk"] = {r["defect_id"] for r in capas}.issubset({r["defect_id"] for r in defects})
    anomalies = read("anomalies")
    required = {"DEFECT_NONEXISTENT_LOT","BOM_MATERIAL_NOT_CONSUMED","CAPA_CLOSED_BEFORE_VERIFICATION",
                "DEFECT_QTY_EXCEEDS_INSPECTED","TRACEABILITY_CHAIN_BREAK"}
    checks["all_required_anomalies_present"] = required.issubset({r["issue_type"] for r in anomalies})
    result = {"passed":all(checks.values()),"checks":checks,"counts":{
        "products":len(products),"suppliers":len(suppliers),"material_lots":len(lots),
        "production_orders":len(orders),"inspection_results":len(results),
        "defects":len(defects),"corrective_actions":len(capas),"anomalies":len(anomalies)}}
    (input_dir/"validation_report.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    if not result["passed"]: raise SystemExit(1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/generated")
    a=p.parse_args()
    validate(Path(a.input))
if __name__=="__main__": main()
