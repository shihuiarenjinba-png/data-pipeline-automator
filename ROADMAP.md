# Roadmap

## Phase 1 — CSV Core（現在）

- CSV input/output
- drop empty rows
- select / rename columns
- deduplicate
- sort
- `root_dir` path boundary
- Dry Run
- atomic output replacement
- default no-overwrite

## Phase 2 — Structured Data

- schema validation
- type conversion rules
- filtering
- joins / lookup tables
- calculated columns with a restricted expression grammar
- error-row quarantine

## Phase 3 — Adapters

- Excel Adapter (`openpyxl`)
- JSON Adapter
- REST API input/output Adapter
- Google Sheets Adapter
- integration with Scheduled API Runner

## Phase 4 — Windows Product

- file picker GUI
- transform-rule editor
- preview before write
- reusable templates
- signed build

## Release Gate

Golden-file regression tests, encoding tests, large-file tests, overwrite/path-boundary tests, formula-injection review for spreadsheet exports, Windows 10/11 smoke tests.
