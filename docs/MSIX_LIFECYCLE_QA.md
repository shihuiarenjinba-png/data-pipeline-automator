# Windows MSIX install/update/uninstall QA — 2026-10-13

Validated **only** on an ephemeral GitHub-hosted Windows runner:
https://github.com/shihuiarenjinba-png/data-pipeline-automator/actions/runs/38408785021

Result: **PASS**. After existing unit tests, compiled GUI file-processing checks, EXE hash checks and unsigned MSIX pack/unpack, the CI-only script used a temporary self-signed testing certificate to:

- Sign a synthetic-identity QA MSIX and register version 1.0.0.0 for the runner's current user
- Build and sign version 1.0.1.0 with the same package family and confirm Windows updated it
- Remove the QA package, confirm it no longer appears in Get-AppxPackage
- Remove this run's test certificate from the test runner certificate stores and verify it is absent

The certificate's public part was temporarily trusted in LocalMachine/TrustedPeople because Windows deployment services rejected CurrentUser-only trust with 0x800B0109. The test runs only with `-EphemeralRunner`, `GITHUB_ACTIONS=true`, `RUNNER_ENVIRONMENT=github-hosted`, on Windows. It is **not** for a personal or persistent machine. No production credentials, Microsoft Store identity, actual customer data or user-installed apps were used.

This validates OS package registration, update and removal. It does **NOT** validate Start Menu launch, real app data persistence, end-user click/visual behavior, Windows 10 and 11 physical hardware, MSIX package capabilities, Windows Security decisions, Store identity matching, official certification, or consumer Store purchase/licensing.

Store-submitted MSIX will be signed by Microsoft after certification. Do not reuse the test certificate, package publisher, placeholder icon or synthetic name for the real submission.

Official Microsoft signing info: https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements

State: `AUTOMATED_MSIX_INSTALL_UPDATE_UNINSTALL_PASS / RELEASE_BLOCKED`.
