# Five Windows utilities — real GUI preferences persist through MSIX update
Date: 2026-10-14 (Asia/Tokyo)

## Completed in existing repositories
No new repository created. All five existing Windows utilities now have a user-facing settings save function, automatic settings restore, versioned local JSON, and installed-MSIX update regression tests.

| Product | Existing repository | Actual saved GUI preferences | Windows CI |
|---|---|---|---|
| Local Data Porter | data-pipeline-automator | Selected workspace root | https://github.com/shihuiarenjinba-png/data-pipeline-automator/actions/runs/38477443030 |
| PDF Batch Forms | -PDF-Privacy-Toolkit | Default PDF batch output folder | https://github.com/shihuiarenjinba-png/-PDF-Privacy-Toolkit/actions/runs/38477467465 |
| Backup Restore Verifier | folder-automation-engine | Output reports folder and restore sample-size cap | https://github.com/shihuiarenjinba-png/folder-automation-engine/actions/runs/38477451887 |
| AI Output Auditor | safe-folder-workflow | Key columns, critical/numeric columns, tolerance, report output folder | https://github.com/shihuiarenjinba-png/safe-folder-workflow/actions/runs/38477457218 |
| Storage Cause Analyzer | -Folder-Privacy-Auditor | Output reports folder | https://github.com/shihuiarenjinba-png/-Folder-Privacy-Auditor/actions/runs/38477462623 |

**Verification:** Five CI jobs SUCCESS, **44 total unit regression tests** across five jobs (9+8+8+11+8). All prove the actual GUI preferences save action and subsequent automatic restoration through *installed* synthetic-identity QA MSIX 1.0.0.0 -> 1.0.1.0 update, including persisted JSON SHA-256 equality. They also run earlier EXE, GUI E2E, package integrity, and uninstall test stages.

## Implementation and privacy
- `ui_preferences.py` saves versioned `schema_version=1` JSON with allowlisted fields only.
- Use Windows `GetCurrentPackageFamilyName` (not guessed identity) to select `%LOCALAPPDATA%\Packages\<PFN>\LocalState\<Product>\preferences.json`.
- Unpackaged version uses `%LOCALAPPDATA%\<Product>\preferences.json`.
- Atomic write: exclusive temp file, fsync, os.replace.
- Reject excessive values, invalid fields, malformed JSON and future schema versions without silently overwriting the existing data.
- User data never leaves the device as part of preference saving. Existing input documents are not copied to the settings location.
- No automatic collection of customer files into GitHub evidence.

## Important boundaries
- The settings persisted here are **actual newly added GUI preferences**, not a claim that historical versions had persistent settings.
- Upgrade between two package versions built from the **same source** proves retention/reload, not migration from a genuinely different application schema. Explicit schema migrations must be implemented and tested in any future change to `VERSION`.
- No migration of real invoice documents, spreadsheets, source folders, databases, reports or backup manifests has been performed.
- Uninstall can delete per-package LocalState even though update retains it; do not advertise uninstall/reinstall recovery.
- Human Windows 10/11 checks, Japanese PDF display, production Store package identity and icon, Defender/security review, actual customer content, Store certification and purchases **remain unverified**.
- All CI packages and test certificates were created inside disposable GitHub-hosted Windows runners and removed. No customer PC was installed.
- Main-branch GitHub workflows remain manual-only.
- GitHub Action artifact-storage quota means the binary QA builds are not downloadable from these runs.

**Status: FIVE_ACTUAL_GUI_PREFERENCE_UPDATE_TESTS_PASS / SALES_RELEASE_BLOCKED.**

## Next engineering work
1. Test real Windows 10 and Windows 11 human interaction from fresh packaged install, with screen scaling and Japanese inputs.
2. Verify application configuration migration using *different* app schema versions and imported legacy data only if product format evolves.
3. Assess user data outside app LocalState (user-chosen documents/reports) and backup/export guarantees.
4. Resolve packaging icons, Store identity and real Microsoft Partner Center certification after security review.

Reference: https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes
