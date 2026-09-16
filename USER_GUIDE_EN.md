# Data Pipeline Automator — User Guide

## Language

Use **`言語 / Language`** in the upper-right corner to select `日本語` or `English`. The selection is retained on the next launch.

## Normal workflow

1. Choose the Pipeline JSON.
2. Use `Validate` to review input, output, operations, and Formula policy.
3. Run `Preview / Dry Run` to inspect the transformation without writing the output file.
4. If the preview is correct, use `Run Pipeline`.

## Safety behavior

- Default `spreadsheet_formula_policy` is `reject`.
- Values that could be evaluated as spreadsheet formulas are blocked by default.
- Duplicate/blank headers and ambiguous column selections are rejected.
- Output is written to a temporary file and atomically committed.
- Overwriting existing output/input requires explicit configuration.

Complete all applicable items in `SALES_RELEASE_CHECKLIST.md` before commercial distribution.
