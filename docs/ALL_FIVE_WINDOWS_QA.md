# 5-product local Windows QA orchestrator

This is a **local testing convenience script** only. It does not clone repos, upload evidence, perform a Store submission, sign code, install packages or approve a release.

## Expected directory layout

Five existing repositories must already be checked out as sibling directories, for example:

```text
C:\Dev\
  data-pipeline-automator\
  -PDF-Privacy-Toolkit\
  folder-automation-engine\
  safe-folder-workflow\
  -Folder-Privacy-Auditor\
```

Run PowerShell from the **data-pipeline-automator** repository:

```powershell
# Print the intended paths and products without modifying anything.
powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\verify-five-products-local.ps1 -WorkspaceRoot "C:\Dev" -PlanOnly

# Check 5 existing local EXE builds, record SHA-256 and signature/Defender STATUS.
powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\verify-five-products-local.ps1 -WorkspaceRoot "C:\Dev"

# If local validation EXEs do not exist, build them first.
# Requires the Python launcher and access to build dependencies.
powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\verify-five-products-local.ps1 -WorkspaceRoot "C:\Dev" -BuildMissing

# OPTIONAL: also create test-only unsigned MSIX packages (Windows SDK MakeAppx required).
powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\verify-five-products-local.ps1 -WorkspaceRoot "C:\Dev" -TestMSIX

# OPTIONAL: human-led GUI checks. Requires answering prompts, using synthetic data.
powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\verify-five-products-local.ps1 -WorkspaceRoot "C:\Dev" -HumanChecks
```

No default Defender scan is launched. An optional `-DefenderScan` flag requests a Windows Defender custom scan; use it only on your own Windows machine, respect organizational security policy and review Windows Security history. The default QA command is read-only against the EXE files; it writes evidence reports under `dist-validation`.

A new `local-five-product-qa-<GUID>\summary.json` is written under the workspace root, listing each product status. Individual product QA reports remain in `dist-validation\...\qa-evidence-<GUID>`.

## What these checks do NOT prove

- User-operated GUI usability, graphics, Windows 10 vs Windows 11 compatibility, installed MSIX behavior or accessibility
- Windows App Certification Kit pass, code signing, Store identity match, safe uninstallation or store payment/licensing
- Network-isolation test or malware-free status

A successful QA summary **never automatically authorizes a release**. Each product uses the same `docs/WINDOWS_MANUAL_ACCEPTANCE.md` checklist. Use local synthetic samples and keep customer data and private screenshots out of Git.

**Release status: BLOCKED pending human/Defender/Store packaging checks.**
