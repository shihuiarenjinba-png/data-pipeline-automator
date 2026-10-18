# MSIX Package Upload Gate — 2026-10-18

Product: **Local Data Porter**  
Repo: `data-pipeline-automator`  
Working branch: `release/package-readiness-20261018`  
Partner Center Store ID: `9N2JSKQJXKV1`  
Pricing: Paid, price not locked

## Verified at source level
- Latest functional improvement branch was used as the base for this isolated release preparation branch.
- Product display metadata and Store Identity record refer to the same product.
- `store/build-msix.ps1` checks the product's recorded Partner Center Identity, source SHA/branch, clean tracked files, Python and basic regression suite. It produces an **unsigned, non-released MSIX candidate** when all prerequisites are provided.
- The build script is not proof of an actual Windows run or Store certification.

## Before producing an MSIX candidate
1. On Windows x64, fetch this branch in an independent working copy. Keep existing `main`, outputs and historical releases untouched.
2. Create a dedicated Python 3.11 x64 `.venv`; install fixed product dependencies and PyInstaller; confirm SHA/source status and Windows SDK MakeAppx availability.
3. Supply and approve four real Store PNG assets under `store/assets` (50x50, 44x44, 150x150, 310x150). **Do not substitute unapproved placeholder art**.
4. Set `STORE_IDENTITY_NAME`, `STORE_PUBLISHER`, `STORE_PUBLISHER_DISPLAY_NAME`, `STORE_VERSION`, `STORE_IDENTITY_CONFIRMED=YES`, `STORE_BRAND_APPROVED=YES` from the matching recorded registration; never reuse a different app's Identity. Version follows x.y.z.0.
5. Execute `powershell.exe -NoProfile -File store/build-msix.ps1 -PreflightOnly`, keep full logs. Then execute without `-PreflightOnly` to produce a candidate, never overwrite old files.
6. Verify `MSIX_AUDIT.json`, package SHA256, extracted manifest Identity/Publisher, and packaged program startup. If a step fails, stop rather than upload.

## Mandatory upload block — still NOT PASSED
- [ ] Windows complete test suite with real logs and SHA
- [ ] Windows GUI end-to-end tests / JA+EN / DPI / input + output integrity
- [ ] Approved commercial rights, icons, third-party LICENSE / NOTICE / privacy / support URL
- [ ] Unsigned build created on target Windows, manifest/archive/architecture validated
- [ ] Proper signed QA installation in an isolated trusted test environment (never disable OS defenses)
- [ ] Installed start, save, relaunch, update and uninstall verified
- [ ] WACK / Store readiness checks verified with report
- [ ] Store pricing/listing/screenshots and corresponding release notes reviewed

**Current verdict: HOLD / DO NOT UPLOAD YET.** A source-level builder and official ID alone are insufficient. Do not submit a package or claim finished MSIX until the above evidence is supplied.
