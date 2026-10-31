
import sqlite3

from yottaflex.schema import SCHEMA_SQL
from yottaflex.anomaly_detection import detect_anomalies


def create_anomaly_fixture(db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)

    # Disable FK enforcement only for deliberate invalid test fixtures.
    conn.execute("PRAGMA foreign_keys=OFF")

    conn.execute("""
        INSERT INTO products VALUES
        ('P001', 'Test Product', 'Industrial', 'unit', 'ACTIVE')
    """)
    conn.execute("""
        INSERT INTO suppliers VALUES
        ('S001', 'Test Supplier', 'India', 'ACTIVE')
    """)
    conn.execute("""
        INSERT INTO machines VALUES
        ('M001', 'Test Machine', 'Welding', 'ACTIVE')
    """)
    conn.execute("""
        INSERT INTO process_step VALUES
        ('PS001', 'Welding', 1)
    """)
    conn.execute("""
        INSERT INTO bom VALUES
        ('B001', 'P001', 'MAT001', 2.0, '2026-01-01', NULL)
    """)
    conn.execute("""
        INSERT INTO production_order VALUES
        ('WO001', 'P001', 10, 10,
         '2026-10-01', '2026-10-02', 'COMPLETED')
    """)
    conn.execute("""
        INSERT INTO inspection_plan VALUES
        ('IP001', 'PS001', 'Dimension', 0, 100, 'mm')
    """)
    conn.execute("""
        INSERT INTO inspection_result VALUES
        ('IR001', 'IP001', 'WO001', 'PS001', 'M001',
         '2026-10-02', 10, 10, 105, 'FAIL', 1.0)
    """)

    # ANOM-001: Defect references a nonexistent material lot.
    # ANOM-004: Defect quantity exceeds inspected quantity (12 > 10).
    conn.execute("""
        INSERT INTO defect VALUES
        ('D001', 'IR001', 'WO001', 'LOT-MISSING',
         'PS001', 'M001', 12, 'HIGH', 'OPEN', '2026-10-02')
    """)

    # ANOM-002: Required BOM material has no consumption record.
    # ANOM-005: Consumption references a nonexistent material lot.
    conn.execute("""
        INSERT INTO material_consumption VALUES
        ('MC001', 'WO001', 'LOT-MISSING', 'MAT002',
         2.0, 2.0, 'kg')
    """)

    # ANOM-003: Corrective action closed without verification.
    conn.execute("""
        INSERT INTO corrective_action VALUES
        ('CA001', 'D001', 'Investigate issue', 'QUALITY',
         'CLOSED', '2026-10-02', NULL, '2026-10-03')
    """)

    conn.commit()
    conn.close()


def test_all_five_anomalies_are_detected(tmp_path):
    db_path = tmp_path / "anomaly_test.sqlite3"
    create_anomaly_fixture(db_path)

    results = detect_anomalies(str(db_path))

    assert len(results) == 5

    for result in results:
        assert result["detected"] is True, result
        assert result["count"] > 0, result

    detected_ids = {r["anomaly_id"] for r in results}

    assert detected_ids == {
        "ANOM-001",
        "ANOM-002",
        "ANOM-003",
        "ANOM-004",
        "ANOM-005",
    }
