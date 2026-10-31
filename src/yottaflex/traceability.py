
import sqlite3


def forward_trace(db_path, defect_id):
    """Trace a defect back to its supplier and material lot."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = """
    SELECT
        d.defect_id,
        d.severity,
        d.status AS defect_status,
        ir.inspection_result_id,
        ir.result_status AS inspection_status,
        po.production_order_id,
        p.product_name,
        ps.step_name,
        m.machine_name,
        ml.material_lot_id,
        ml.material_code,
        s.supplier_name,
        ca.action_description,
        ca.status AS corrective_action_status
    FROM defect d
    JOIN inspection_result ir
        ON d.inspection_result_id = ir.inspection_result_id
    JOIN production_order po
        ON d.production_order_id = po.production_order_id
    JOIN products p
        ON po.product_id = p.product_id
    JOIN process_step ps
        ON d.process_step_id = ps.process_step_id
    JOIN machines m
        ON d.machine_id = m.machine_id
    JOIN material_lot ml
        ON d.material_lot_id = ml.material_lot_id
    JOIN suppliers s
        ON ml.supplier_id = s.supplier_id
    LEFT JOIN corrective_action ca
        ON d.defect_id = ca.defect_id
    WHERE d.defect_id = ?
    """

    result = [dict(row) for row in conn.execute(query, (defect_id,))]
    conn.close()
    return result


def reverse_trace(db_path, material_lot_id):
    """Find all production orders and defects using a material lot."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = """
    SELECT
        ml.material_lot_id,
        ml.material_code,
        s.supplier_name,
        po.production_order_id,
        p.product_name,
        po.status AS order_status,
        d.defect_id,
        d.severity,
        d.status AS defect_status
    FROM material_lot ml
    JOIN suppliers s
        ON ml.supplier_id = s.supplier_id
    JOIN material_consumption mc
        ON ml.material_lot_id = mc.material_lot_id
    JOIN production_order po
        ON mc.production_order_id = po.production_order_id
    JOIN products p
        ON po.product_id = p.product_id
    LEFT JOIN defect d
        ON po.production_order_id = d.production_order_id
        AND ml.material_lot_id = d.material_lot_id
    WHERE ml.material_lot_id = ?
    ORDER BY po.production_order_id
    """

    result = [dict(row) for row in conn.execute(query, (material_lot_id,))]
    conn.close()
    return result
