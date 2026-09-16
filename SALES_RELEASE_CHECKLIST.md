# Sales release checklist / 販売直前チェック

## Automated / code gates

- [x] Duplicate/blank CSV header rejection
- [x] Transformation schema validation
- [x] Spreadsheet formula policy (`reject` default, explicit `escape`/`preserve`)
- [x] Atomic output write
- [x] Dry Run / Preview path
- [x] Explicit **`言語 / Language`** selector with persisted `日本語` / `English`
- [x] Language/Preview UI regression tests
- [x] Japanese and English user guides

## Real Windows/data gates

- [ ] Windows 10 smoke test
- [ ] Windows 11 smoke test
- [ ] Switch 日本語 → English → 日本語; restart and confirm persistence
- [ ] Check 100%, 125%, 150% display scaling
- [ ] Preview and run a controlled CSV transformation
- [ ] Test duplicate header, blank header, missing-column, and invalid-operation failures
- [ ] Test `spreadsheet_formula_policy=reject` against cells beginning with formula-capable prefixes
- [ ] Test `escape` only with controlled expected output
- [ ] Confirm normal signed numeric values are not incorrectly treated as formulas
- [ ] Confirm output is not partially committed after an injected failure
- [ ] Confirm overwrite behavior matches configuration and never silently overwrites input
- [ ] Test UTF-8 and supported non-UTF-8 encodings used in product documentation
- [ ] Build packaged Windows executable from a path with spaces/non-ASCII characters
- [ ] Run Windows Defender/AV scan and record release SHA-256
- [ ] Prepare LICENSE/NOTICE/SBOM and lock dependency versions
- [ ] Sign the final installer/executable if distributed commercially

Do not mark the product sales-ready until every applicable unchecked item has been completed with controlled test data.

未チェック項目が残っている間は販売完成扱いにしません。
