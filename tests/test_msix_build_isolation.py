"""Static anti-regression: MSIX builds must not alter developer Python environments."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BuildIsolationContract(unittest.TestCase):
    def test_python_environment_is_inside_separate_ignored_candidate_dir(self):
        builder = (ROOT / "store" / "build-msix.ps1").read_text(encoding="utf-8")
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("store-output/", ignore)
        self.assertIn('$venv = Join-Path $out "venv"', builder)
        self.assertNotIn('Join-Path $root ".venv\\Scripts\\python.exe"', builder)
        self.assertIn("python", builder.lower())
        self.assertIn("unittest discover", builder)
        self.assertIn("pythonBits", builder)
        self.assertIn('-c "import struct; print(struct.calcsize(\'P\') * 8)"', builder)
        self.assertIn("PYTHONDONTWRITEBYTECODE", builder)
        self.assertIn("MSIX_AUDIT.json", builder)
        self.assertNotIn("Remove-AppxPackage", builder)
        self.assertNotIn("Add-AppxPackage", builder)
        self.assertNotIn("Import-PfxCertificate", builder)

    def test_msix_release_cannot_skip_identity_or_artwork_approval(self):
        builder = (ROOT / "store" / "build-msix.ps1").read_text(encoding="utf-8")
        identity = (ROOT / "store" / "build-with-partner-identity.ps1").read_text(
            encoding="utf-8")
        self.assertIn("STORE_IDENTITY_CONFIRMED", builder)
        self.assertIn("STORE_BRAND_APPROVED", builder)
        self.assertIn("partner_center_registration.json", builder)
        self.assertIn("ApprovedArtwork", identity)
        self.assertIn("NOT_AUTHORIZED", (ROOT / "store" / "partner_center_registration.json").read_text(
            encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
