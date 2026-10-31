
import sqlite3
from pathlib import Path

from yottaflex.traceability import forward_trace, reverse_trace


DB = Path("data/generated/yottaflex.sqlite3")


def test_forward_trace_returns_complete_chain():
    conn = sqlite3.connect(DB)
    defect_id = conn.execute(
        "SELECT defect_id FROM defect LIMIT 1"
    ).fetchone()[0]
    conn.close()

    results = forward_trace(str(DB), defect_id)

    assert results
    result = results[0]

    for field in (
        "defect_id",
        "production_order_id",
        "product_name",
        "step_name",
        "machine_name",
        "material_lot_id",
        "supplier_name",
    ):
        assert result[field] is not None


def test_reverse_trace_finds_material_lot_orders():
    conn = sqlite3.connect(DB)
    lot_id = conn.execute(
        "SELECT material_lot_id FROM material_consumption LIMIT 1"
    ).fetchone()[0]
    conn.close()

    results = reverse_trace(str(DB), lot_id)

    assert results
    assert all(r["material_lot_id"] == lot_id for r in results)
    assert all(r["production_order_id"] for r in results)


def test_unknown_defect_returns_empty():
    assert forward_trace(str(DB), "UNKNOWN-DEFECT") == []


def test_unknown_lot_returns_empty():
    assert reverse_trace(str(DB), "UNKNOWN-LOT") == []
