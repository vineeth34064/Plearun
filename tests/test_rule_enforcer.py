import unittest
import os
from plearun.models import Finding
from plearun.parsers import RecordsManager
from plearun.rule_enforcer import RuleEnforcer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestRuleEnforcer(unittest.TestCase):
    def setUp(self):
        self.rm = RecordsManager(os.path.join(ROOT, "records"))
        self.enforcer = RuleEnforcer(self.rm)

    def test_valid_match_retains_cite_and_quote(self):
        f = Finding(
            claim="The driver pulled into the Harbor Gas lot and stopped around 21:16.",
            finding="match",
            cite_file="notes_cp1252.csv",
            cite_row=4,
            quote="Stopped at lot ~21:16,21:16"
        )
        out = self.enforcer.enforce_and_serialize([f])
        item = out["findings"][0]
        self.assertEqual(item["finding"], "match")
        self.assertIn("cite", item)
        self.assertEqual(item["cite"]["file"], "notes_cp1252.csv")
        self.assertEqual(item["cite"]["row"], 4)
        self.assertEqual(item["quote"], "Stopped at lot ~21:16,21:16")

    def test_invalid_quote_downgrades_to_not_settled(self):
        # Intentional typo in quote that is not a substring
        f = Finding(
            claim="The driver pulled into the Harbor Gas lot and stopped around 21:16.",
            finding="match",
            cite_file="notes_cp1252.csv",
            cite_row=4,
            quote="Stopped at gas station at 21:16"
        )
        out = self.enforcer.enforce_and_serialize([f])
        item = out["findings"][0]
        self.assertEqual(item["finding"], "not_settled")
        self.assertNotIn("cite", item)
        self.assertNotIn("quote", item)

    def test_invalid_row_downgrades_to_not_settled(self):
        # Non-existent row number
        f = Finding(
            claim="Test claim",
            finding="conflict",
            cite_file="camera_log.csv",
            cite_row=9999,
            quote="test"
        )
        out = self.enforcer.enforce_and_serialize([f])
        item = out["findings"][0]
        self.assertEqual(item["finding"], "not_settled")
        self.assertNotIn("cite", item)
        self.assertNotIn("quote", item)

    def test_not_checkable_omits_cite_and_quote(self):
        f = Finding(
            claim="Officer Lee states the vehicle was the only car in the lane.",
            finding="not_checkable",
            cite_file="camera_log.csv", # Should be stripped
            cite_row=18,
            quote="CAM-07"
        )
        out = self.enforcer.enforce_and_serialize([f])
        item = out["findings"][0]
        self.assertEqual(item["finding"], "not_checkable")
        self.assertNotIn("cite", item)
        self.assertNotIn("quote", item)

if __name__ == "__main__":
    unittest.main()
