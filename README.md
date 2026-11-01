# YottaFlex Manufacturing Traceability

A reproducible synthetic manufacturing-data and traceability foundation for the YottaFlex 72-hour coding challenge.

## Current implementation

* Deterministic synthetic manufacturing data generated using a configurable random seed.
* 11 core manufacturing entities and one material-consumption transaction table (12 relational tables in total).Referentially consistent baseline data with deterministic IDs.
* Five labelled negative scenarios stored separately from valid baseline data.
* CSV, JSON, SQLite, SQL schema, seed SQL, data dictionary, validation summary, and SHA-256 manifest exports.
* Data validation covering primary/foreign-key relationships, quantities, material reconciliation, and other integrity rules.
* Reproducibility verification using generated-file checksums.
* Forward traceability from a defect to its production order, product, process, machine, material lot, supplier, and corrective action.
* Reverse traceability from a material lot to the production orders and related defects.
* Five SQL-based anomaly detection checks for data-integrity and lifecycle violations.

## Requirements

* Python 3.11+
* Runtime generation, validation, traceability, and anomaly-detection functionality use Python's standard library.
* `pytest` is required to run the automated tests.

## Setup and quick start (Windows PowerShell)

Run these commands from the repository root:

```powershell
py -3.11 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip
pip install -e .
pip install pytest
```

If `py -3.11` is unavailable, use `python` after confirming that it points to Python 3.11 or a compatible version.

## Generate the dataset

```powershell
python -m yottaflex.generate --seed 20261022 --output data/generated
```

## Validate the generated dataset

```powershell
python -m yottaflex.validate --input data/generated
```

## Verify reproducibility

```powershell
python -m yottaflex.reproducibility --seed 20261022
```

Run the same seed again and compare the generated checksums to verify deterministic output.

## Run anomaly detection

```powershell
python -m yottaflex.anomaly\_detection
```

The detector checks the SQLite baseline database for five conditions:

1. Defects referencing nonexistent material lots.
2. BOM-required materials missing from material-consumption records.
3. Corrective actions marked closed without a verification date.
4. Defect quantities exceeding inspected quantities.
5. Material-consumption records referencing nonexistent material lots.

A clean baseline database is expected to report no detections. The automated anomaly test uses a separate SQLite fixture containing deliberately malformed records to verify that the checks can detect these conditions.

## Run automated tests

```powershell
python -m pytest tests -v
```

The tests cover deterministic generation, required baseline record counts, anomaly detection, forward traceability, reverse traceability, and unknown-ID handling.

## Traceability functions

The traceability module provides two query operations:

* `forward\_trace(db\_path, defect\_id)`: follows a defect through its inspection result, production order, product, process step, machine, material lot, supplier, and corrective action.
* `reverse\_trace(db\_path, material\_lot\_id)`: finds production orders and related defect information associated with a material lot.

These are Python query functions, not a web API or interactive user interface.

## Output layout

```text
data/generated/
  csv/                 CSV exports for generated entities and labelled anomalies
  json/                JSON exports for generated entities and labelled anomalies
  yottaflex.sqlite3    SQLite database
  schema.sql           SQLite database schema
  seed\_data.sql        SQL schema and seed INSERT statements
  data\_dictionary.md   Entity and field descriptions
  validation\_summary.json
  manifest.sha256      Generated-file checksums
```

## Design decisions

1. The baseline dataset contains valid records. Deliberate negative scenarios are stored separately with an `issue\_type` and `ground\_truth` label.
2. The random seed controls generation so the same seed produces reproducible output.
3. IDs are deterministic and zero-padded.
4. Inspection defect rates use inspected quantity as the denominator.
5. Material lots are allocated to production orders through `material\_consumptions`, providing an explicit lot-to-order relationship.
6. Derived values, including remaining lot quantity, defect rate, and order material balance, are calculated from source records after generation.
7. Anomaly detection is performed using SQL checks against a SQLite database. The baseline database is kept clean; malformed records are introduced in isolated test fixtures.

## Limitations and future work

This implementation provides a synthetic-data foundation, validation, traceability query functions, and SQL-based anomaly detection. It does not currently provide:

* A web-based or interactive defect-investigation interface.
* A complete event-sourced manufacturing lifecycle history.
* Advanced quality analytics or dashboards.
* Full end-to-end application testing.

The anomaly checks currently operate on the implemented SQLite relationships. In particular, the traceability-chain-break check interprets a missing material-lot relationship through `material\_consumptions`.

## Challenge coverage checklist

* \[x] Deterministic baseline data generation with a fixed seed.
* \[x] Required baseline record volumes.
* \[x] Related manufacturing master and transaction entities.
* \[x] Five labelled negative scenarios.
* \[x] CSV, JSON, SQL schema, and SQLite exports.
* \[x] Data validation and reproducibility commands.
* \[x] Forward and reverse traceability query functions.
* \[x] Five SQL-based anomaly detection checks.
* \[x] Automated generator and anomaly-detection tests.
* \[x] Automated traceability tests verified.
* \[ ] Interactive defect-investigation interface.
* \[ ] Full lifecycle event history and advanced quality analytics.
* \[ ] Web UI and end-to-end application tests.

