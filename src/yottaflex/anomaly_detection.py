
import sqlite3


def detect_anomalies(db_path):
    """Run five integrity checks against the baseline SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    findings = []

    checks = [
        (
            "ANOM-001",
            "INVALID_FK",
            """
            SELECT d.defect_id AS record_id
            FROM defect d
            LEFT JOIN material_lot ml
              ON d.material_lot_id = ml.material_lot_id
            WHERE ml.material_lot_id IS NULL
            """
        ),
        (
            "ANOM-002",
            "RECONCILIATION_FAILURE",
            """
            SELECT b.bom_id AS record_id,
                   po.production_order_id
            FROM production_order po
            JOIN bom b ON b.product_id = po.product_id
            LEFT JOIN material_consumption mc
              ON mc.production_order_id = po.production_order_id
             AND mc.material_code = b.material_code
            WHERE mc.consumption_id IS NULL
            """
        ),
        (
            "ANOM-003",
            "LIFECYCLE_VIOLATION",
            """
            SELECT corrective_action_id AS record_id
            FROM corrective_action
            WHERE UPPER(status) = 'CLOSED'
              AND verified_date IS NULL
            """
        ),
        (
            "ANOM-004",
            "QUANTITY_VIOLATION",
            """
            SELECT d.defect_id AS record_id
            FROM defect d
            JOIN inspection_result ir
              ON d.inspection_result_id = ir.inspection_result_id
            WHERE d.defect_qty > ir.inspected_qty
            """
        ),
        (
            "ANOM-005",
            "MISSING_RELATIONSHIP",
            """
            SELECT mc.consumption_id AS record_id
            FROM material_consumption mc
            LEFT JOIN material_lot ml
              ON mc.material_lot_id = ml.material_lot_id
            WHERE ml.material_lot_id IS NULL
            """
        )
    ]

    for anomaly_id, expected_type, query in checks:
        rows = conn.execute(query).fetchall()
        findings.append({
            "anomaly_id": anomaly_id,
            "expected_type": expected_type,
            "detected": len(rows) > 0,
            "count": len(rows),
            "records": [dict(row) for row in rows[:10]]
        })

    conn.close()
    return findings


if __name__ == "__main__":
    import json

    results = detect_anomalies("data/generated/yottaflex.sqlite3")
    print(json.dumps(results, indent=2))
