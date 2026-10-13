# Five-product MSIX Windows installation lifecycle — 2026-10-13

## Scope
Existing 5 repositories only; **no new product repository** was created.
Tests used a disposable GitHub-hosted Windows runner, synthetic QA package IDs,
self-signed short-lived test certificates, and no customer data.

## Results

| Product | Existing repository | GitHub Windows run | Registration / upgrade / cleanup |
|---|---|---|---|
| Local Data Porter | data-pipeline-automator | https://github.com/shihuiarenjinba-png/data-pipeline-automator/actions/runs/38408785021 | PASS |
| PDF Batch Forms | -PDF-Privacy-Toolkit | https://github.com/shihuiarenjinba-png/-PDF-Privacy-Toolkit/actions/runs/38409220526 | PASS |
| Backup Restore Verifier | folder-automation-engine | https://github.com/shihuiarenjinba-png/folder-automation-engine/actions/runs/38409248963 | PASS |
| AI Output Auditor | safe-folder-workflow | https://github.com/shihuiarenjinba-png/safe-folder-workflow/actions/runs/38409232544 | PASS |
| Storage Cause Analyzer | -Folder-Privacy-Auditor | https://github.com/shihuiarenjinba-png/-Folder-Privacy-Auditor/actions/runs/38409241168 | PASS |

Each run passed the following checks:
- PyInstaller validation build and GUI smoke/E2E fixtures
- Unsigned MSIX pack/unpack, EXE SHA-256 roundtrip
- Self-signed **ephemeral** QA signing in a hosted runner; temporary LocalMachine/TrustedPeople trust
- Install signed version 1.0.0.0 and confirm registered version and family
- Update signed version 1.0.1.0 and confirm same family and new version
- Uninstall QA package and remove ephemeral test certificates; fail the job on cleanup errors

A Windows deployment error `0x800B0109` in the initial Local Data Porter run
was resolved by trusting the public QA certificate in the machine-level
TrustedPeople store, per Microsoft deployment troubleshooting guidance.
**This machine-level trust operation must never be run on end-user or shared PCs by automation.**

## Remaining release blockers

1. Start Menu / app package identity launch, manual GUI visual checks, Japanese PDF glyphs.
2. Persists and migrates synthetic save/configuration data correctly across MSIX update.
3. Windows 10 and 11 physical device test matrix, Defender behavior and security review.
4. Real Partner Center MSIX identity, custom original icons, metadata and product association.
5. Store submission and certification; seller and licensing checks.
6. Distribution artifacts must be locally rebuilt or storage capacity restored before delivery.

Production Store MSIX signing is handled by Microsoft after successful certification;
developer QA self-signed certificates are not suitable for production.
WACK was deprecated as a mandatory pre-submission requirement; Microsoft Store
certification still occurs on actual submission. Review current Microsoft Learn
rather than treating local WACK as a definitive sales gate.

## Release policy

**5/5 automated MSIX install/update/uninstall PASS. SALES RELEASE BLOCKED.**
No code changes affect normal product runtime; all new lifecycle verification
is opt-in CI-only and the production `main` workflow remains manual-only.

Official information:
- https://learn.microsoft.com/en-us/windows/msix/msix-troubleshooting-guide
- https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements
