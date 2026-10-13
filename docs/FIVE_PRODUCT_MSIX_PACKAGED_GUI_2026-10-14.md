# Five Windows utilities — installed MSIX GUI and synthetic update-state QA
Date: 2026-10-14 (Japan time)

## Verified result
**All five passed** GitHub-hosted Windows CI, with isolated QA-only package identities and temporary certificates.

| Product | Existing repository | CI evidence |
|---|---|---|
| Local Data Porter | data-pipeline-automator | https://github.com/shihuiarenjinba-png/data-pipeline-automator/actions/runs/38419199979 |
| PDF Batch Forms | -PDF-Privacy-Toolkit | https://github.com/shihuiarenjinba-png/-PDF-Privacy-Toolkit/actions/runs/38419674271 |
| Backup Restore Verifier | folder-automation-engine | https://github.com/shihuiarenjinba-png/folder-automation-engine/actions/runs/38419688946 |
| AI Output Auditor | safe-folder-workflow | https://github.com/shihuiarenjinba-png/safe-folder-workflow/actions/runs/38419698890 |
| Storage Cause Analyzer | -Folder-Privacy-Auditor | https://github.com/shihuiarenjinba-png/-Folder-Privacy-Auditor/actions/runs/38419707858 |

Each workflow now checks:
1. Existing Python unit/regression tests and synthetic GUI-to-file E2E.
2. PyInstaller unsigned EXE build and package SHA-256 validation.
3. Test MSIX pack/unpack verification.
4. Self-signed *disposable* certificate and synthetic QA identity; install MSIX 1.0.0.0.
5. Windows Shell COM `IApplicationActivationManager.ActivateApplication` launch with installed package's AUMID; Tk GUI writes an app-generated QA JSON to `LocalState`.
6. MSIX update to 1.0.1.0 with the same package family.
7. SHA-256 confirms the original app-generated QA JSON is preserved; the updated installed GUI launches again and writes a second QA JSON.
8. Remove test package and certificate copies, with cleanup part of success criteria.

## What this does not demonstrate
- **Not real product data migration**. The preserved file is only a synthetic QA startup marker, not a report, saved user setting, database, business document or source file. Inspect each app's actual persistence code and migration path before selling.
- Not manual Start Menu clicks, human visual checks, accessibility or Japanese PDF glyph verification.
- Not testing on physical Windows 10 and Windows 11 devices.
- Not production Partner Center identity, real icons, official Store certification, purchases, billing, or customer delivery.
- Not malware-free certification or complete security review.

## Precautions
- CI lifecycle code refuses ordinary Windows PCs and self-hosted runners.
- Never automatically add a synthetic test certificate to a user's TrustedPeople store.
- Main branch workflows remain `workflow_dispatch` only.
- The current GitHub Actions Artifact quota prevents downloading QA binaries from these runs.
- No new repositories were created; only the five existing Windows utility repositories were extended.

**Overall state: AUTOMATED_INSTALLED_MSIX_GUI_STATE_QA_PASS_5_OF_5 / RELEASE_BLOCKED.**

Microsoft documentation:
- https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-iapplicationactivationmanager-activateapplication
- https://learn.microsoft.com/en-us/windows/msix/msix-troubleshooting-guide
