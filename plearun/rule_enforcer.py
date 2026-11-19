from typing import List, Dict, Any
from plearun.models import Finding
from plearun.parsers import RecordsManager

class RuleEnforcer:
    """
    Guarantees strict compliance with all assignment rules before output serialization:
    Rule 1: Every match or conflict must cite a real row, and your code must verify
            the quote is an exact substring of the raw text of that row before the
            finding is written. Otherwise downgrade to not_settled.
    Rule 1 (cont): cite and quote are required for match and conflict, and must be
            omitted for the other two.
    """
    def __init__(self, records_manager: RecordsManager):
        self.rm = records_manager

    def enforce_and_serialize(self, findings: List[Finding]) -> Dict[str, Any]:
        output_list = []

        for f in findings:
            final_finding = f.finding
            cite_file = f.cite_file
            cite_row = f.cite_row
            quote = f.quote

            # Apply Rule 1 verification
            if final_finding in ("match", "conflict"):
                is_valid = False
                if cite_file and cite_row is not None and quote:
                    is_valid = self.rm.verify_quote(cite_file, cite_row, quote)

                if not is_valid:
                    # Downgrade immediately to not_settled
                    final_finding = "not_settled"
                    cite_file = None
                    cite_row = None
                    quote = None

            # Construct dictionary according to exact schema
            item: Dict[str, Any] = {
                "claim": f.claim,
                "finding": final_finding
            }

            if final_finding in ("match", "conflict"):
                item["cite"] = {
                    "file": cite_file,
                    "row": cite_row
                }
                item["quote"] = quote

            output_list.append(item)

        return {"findings": output_list}
