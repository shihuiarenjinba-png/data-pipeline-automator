# Real user preferences and Windows MSIX update — 2026-10-14

**Product**: Local Data Porter
**Proven**: https://github.com/shihuiarenjinba-png/data-pipeline-automator/actions/runs/38477443030 (GitHub-hosted Windows CI SUCCESS).

The product's GUI now has a `作業フォルダ設定を保存` button to retain a user-selected workspace folder across restarts and package version updates. It does not save the source/destination document paths automatically.

Preferences use a UTF-8 JSON object with `schema_version: 1` and a strictly allowlisted `rootdir` string. The implementation writes through an exclusive temporary file, fsync and atomic `os.replace`. Unknown fields are rejected on save; corrupt or future-version preference files are NOT silently replaced. On failure, the GUI shows a status/error and leaves the original file alone.

- Windows MSIX: `%LOCALAPPDATA%\Packages\<ActualPackageFamilyName>\LocalState\LocalDataPorter\preferences.json` (identity via Windows GetCurrentPackageFamilyName, NOT guessed)
- Unpackaged Windows EXE: `%LOCALAPPDATA%\LocalDataPorter\preferences.json`
- No external API, network upload or business content is saved by this feature.

**Windows CI proof**: real GUI save button invoked from the installed app; version 1.0.0.0 saves synthetic Japanese-text settings; v1.0.1.0 checks matching SHA-256 and restored GUI setting; test app and temporary cert removed after success. The 9 Python tests also pass, including corrupted/newer preferences scenarios.

**Not tested / not claimed**: existing user preferences from earlier product releases (none previously supported), migrations from later schema versions, Windows 10/11 physical use, real human GUI interaction, business data retention, Store identity/certification, purchase/licensing, malware-free status. Uninstall may remove package LocalState, unlike version update. Do not promise retention after uninstall.

**Release status: REAL_GUI_PREFERENCES_CI_PASS / RELEASE_BLOCKED.**
