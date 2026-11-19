"""
Plearun Incident Report Verification CLI
Usage: python3 plearun_cli.py REPORT RECORDS_DIR
"""
import sys
import json
import os
from plearun.parsers import RecordsManager
from plearun.claims import extract_claims_from_report
from plearun.verifier import IncidentVerifier
from plearun.rule_enforcer import RuleEnforcer

def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python3 plearun_cli.py REPORT RECORDS_DIR", file=sys.stderr)
        return 2

    report_path = sys.argv[1]
    records_dir = sys.argv[2]

    if not os.path.exists(report_path):
        print(f"Error: Report file not found at {report_path}", file=sys.stderr)
        return 1

    if not os.path.exists(records_dir):
        print(f"Error: Records directory not found at {records_dir}", file=sys.stderr)
        return 1

    # Ingest and parse machine records
    rm = RecordsManager(records_dir)

    # Ingest and extract narrative claims from report
    claims = extract_claims_from_report(report_path)

    # Verify each claim against records
    verifier = IncidentVerifier(rm)
    findings = verifier.verify_all_claims(claims)

    # Strictly enforce Rule 1 (substring quote verification) and serialize
    enforcer = RuleEnforcer(rm)
    output_dict = enforcer.enforce_and_serialize(findings)

    # Output exact JSON to stdout
    print(json.dumps(output_dict, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
