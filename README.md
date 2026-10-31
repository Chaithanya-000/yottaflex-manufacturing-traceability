# YottaFlex Manufacturing Traceability

A reproducible synthetic-data foundation for the YottaFlex 72-hour coding challenge.

## Current implementation
- Deterministic synthetic manufacturing data using a configurable random seed.
- 11 core entities: Product, BOM, Supplier, MaterialLot, ProductionOrder, Machine,
  ProcessStep, InspectionPlan, InspectionResult, Defect, CorrectiveAction.
- Referentially consistent baseline data and deterministic IDs.
- Five labelled negative scenarios stored separately from valid baseline data.
- CSV, JSON, SQLite, SQL schema, data dictionary, validation summary and SHA-256 manifests.
- Reproducibility check: run twice with the same seed and compare checksums.

## Requirements
- Python 3.11+ (standard library only; no external packages required).

## Quick start (Windows PowerShell)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m yottaflex.generate --seed 20261022 --output data/generated
python -m yottaflex.validate --input data/generated
python -m yottaflex.reproducibility --seed 20261022
```

Run from the repository root. If `py -3.11` is unavailable, use `python` after confirming
`python --version`.

## Output layout
```text
data/generated/
  csv/                 one CSV per entity plus labelled anomalies
  json/                one JSON array per entity plus anomalies
  yottaflex.sqlite3    SQLite database with primary/foreign keys
  schema.sql           portable SQLite DDL\n  seed_data.sql        SQL DDL + INSERT seed statements
  data_dictionary.md
  validation_summary.json
  manifest.sha256
```

## Design decisions
1. The baseline dataset contains valid records only. Deliberate invalid examples are kept in
   `anomalies` with an `issue_type` and `ground_truth` label; they are not inserted into the
   valid relational tables.
2. The seed is explicit and controls every random choice. IDs are deterministic and zero-padded.
3. Inspection defect rates use inspected quantity as the denominator. A defect count greater
   than inspected quantity is an explicit anomaly, not a valid result.
4. Material lots are allocated to production orders through `material_consumptions`, which
   makes lot-to-order traceability explicit.
5. Derived values (remaining lot quantity, defect rate, order material balance) are calculated
   from source records after generation.

## Important limitation
This is the first executable foundation, not the finished challenge solution. The traceability
query service, richer lifecycle event history, web UI, and expanded domain validation are next
implementation stages. Do not represent those as complete until implemented and tested.

## Challenge coverage checklist
- [x] Deterministic baseline generation with fixed seed
- [x] 200 products/SKUs, 50 suppliers, 2,000 material lots, 5,000 production orders,
      20,000 inspection results
- [x] Related master and transaction entities
- [x] Labelled required negative scenarios
- [x] CSV / JSON / SQL schema / SQLite exports
- [x] Validation and reproducibility commands
- [ ] Traceability API and interactive defect investigation
- [ ] Full lifecycle event history and advanced quality analytics
- [ ] User interface and end-to-end tests
