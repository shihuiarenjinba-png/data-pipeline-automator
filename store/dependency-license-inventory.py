"""Read-only Python dependency license evidence inventory for commercial review.

Execute with the exact Python interpreter used to build the MSIX. Outputs JSON
to stdout; never asserts that a package is legally cleared for redistribution.
"""
from __future__ import annotations

from importlib import metadata
import json
import platform
import sys
from pathlib import Path

STORE = Path(__file__).resolve().parent
REPO = STORE.parent


def inventory() -> dict:
    results = []
    for dist in sorted(metadata.distributions(), key=lambda d: (d.metadata.get("Name") or "").casefold()):
        m = dist.metadata
        name = m.get("Name") or "UNKNOWN"
        declared = m.get("License-Expression") or m.get("License") or ""
        classifiers = [
            value for value in m.get_all("Classifier", [])
            if value.startswith("License ::")
        ]
        license_files = [
            str(file) for file in (dist.files or [])
            if Path(str(file)).name.upper().startswith(("LICENSE", "COPYING", "NOTICE"))
        ]
        known = bool(declared.strip() or classifiers or license_files)
        results.append({
            "package": name,
            "version": dist.version,
            "license_declared": declared.strip()[:180],
            "license_classifiers": classifiers,
            "installed_license_paths": license_files[:20],
            "metadata_found": known,
            "redistribution_approved": False,
        })
    return {
        "repo": json.loads((STORE / "product.json").read_text(encoding="utf-8")).get("repository"),
        "python": platform.python_version(),
        "arch": platform.architecture()[0],
        "runtime": sys.executable,
        "distribution_count": len(results),
        "incomplete_metadata": [x["package"] for x in results if not x["metadata_found"]],
        "redistribution_status": "OWNER_LEGAL_APPROVAL_REQUIRED",
        "products": results,
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), ensure_ascii=False, indent=2))
