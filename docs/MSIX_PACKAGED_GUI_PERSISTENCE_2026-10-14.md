# MSIX installed GUI activation and update data persistence — 2026-10-14

**Product:** LocalDataPorter
**Existing repository:** data-pipeline-automator
**Evidence:** https://github.com/shihuiarenjinba-png/data-pipeline-automator/actions/runs/38419199979
**Automated result:** PASS on disposable GitHub-hosted Windows runner.

The test starts with synthetic MSIX identity `QA.LocalDataPorter.Prototype` and v1.0.0.0. The COM `IApplicationActivationManager.ActivateApplication` API launches the **registered packaged GUI** using its AUMID rather than starting the unpackaged binary. The compiled Tk app writes `qa_msix_before_upgrade.json` to its MSIX `LocalState`. The test confirms the output contents and SHA-256, updates to v1.0.1.0, checks the original marker is unchanged, launches packaged GUI again, and verifies its second marker. It then uninstalls test package and removes test certificates.

**The artifact is synthetic**: it proves package LocalState persistence and app test-mode GUI initialization across version change, **not** that a real customer configuration, business database, documents, or application-specific save migration is correctly implemented. Visual display, human interaction, physical Windows 10/11 compatibility, production signing and Partner Center certification remain **NOT TESTED**.

The lifecycle script refuses non-ephemeral Windows runners and does not install on a user's computer. Github Actions remains manual-only on main. Artifacts are not uploaded because of existing GitHub storage quota.

Release state: `PACKAGED_GUI_LOCALSTATE_CI_PASS / RELEASE_BLOCKED`.
