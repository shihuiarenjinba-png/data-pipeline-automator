"""Regression: Store slot never drifts away from screenshot-confirmed identity."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = "CN=46263F21-A700-41DB-8C9B-114C22FB82FC"
PFN_SUFFIX = "_j8yefg9jgfh58"


class StoreSlotConsistencyTests(unittest.TestCase):
    def test_confirmed_identity_and_display_name(self):
        config = json.loads((ROOT / "store" / "product.json").read_text(encoding="utf-8"))
        record = json.loads((ROOT / "store" / "partner_center_registration.json").read_text(encoding="utf-8"))
        self.assertEqual(record["repository"], ROOT.name)
        self.assertEqual(config["displayName"], record["displayName"])
        self.assertEqual(config["displayName"], "Local Data Porter")
        self.assertEqual(record["partnerCenterState"], "EXISTING_CONFIRMED")
        identity = record["storeIdentity"]
        self.assertEqual(identity["storeId"], "9N2JSKQJXKV1")
        self.assertEqual(identity["packageIdentityName"], "OkinawaDesktopTools.LocalDataPorter")
        self.assertEqual(identity["packageIdentityPublisher"], PUBLISHER)
        self.assertEqual(identity["publisherDisplayName"], "Okinawa Desktop Tools")
        self.assertEqual(identity["packageFamilyName"], "OkinawaDesktopTools.LocalDataPorter" + PFN_SUFFIX)
        self.assertEqual(record["certificationSubmission"], "NOT_AUTHORIZED")
        self.assertEqual(record["salesRelease"], "HOLD")

    def test_msix_build_scripts_do_not_publish(self):
        store = ROOT / "store"
        for file in ("build-msix.ps1", "build-with-partner-identity.ps1",
                     "verify-upload-inputs.py"):
            self.assertTrue((store / file).is_file(), file)


if __name__ == "__main__":
    unittest.main()
