import unittest
import subprocess
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestCLIIntegration(unittest.TestCase):
    def test_cli_execution_on_sample(self):
        report_path = os.path.join(ROOT, "reports", "report_fictional_02.txt")
        records_dir = os.path.join(ROOT, "records")

        cmd = [sys.executable, os.path.join(ROOT, "plearun_cli.py"), report_path, records_dir]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("findings", data)
        findings = data["findings"]
        self.assertEqual(len(findings), 5)

        valid_findings = {"match", "conflict", "not_settled", "not_checkable"}
        for f in findings:
            self.assertIn("claim", f)
            self.assertIn("finding", f)
            self.assertIn(f["finding"], valid_findings)

            if f["finding"] in ("match", "conflict"):
                self.assertIn("cite", f)
                self.assertIn("quote", f)
                self.assertIsInstance(f["cite"], dict)
                self.assertIn("file", f["cite"])
                self.assertIn("row", f["cite"])
                self.assertIsInstance(f["cite"]["row"], int)
                self.assertIsInstance(f["quote"], str)
            else:
                self.assertNotIn("cite", f)
                self.assertNotIn("quote", f)

    def test_cli_missing_args(self):
        cmd = [sys.executable, os.path.join(ROOT, "plearun_cli.py")]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

if __name__ == "__main__":
    unittest.main()
