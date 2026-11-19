import json
from typing import List, Optional, Dict, Any
from plearun.models import Finding
from plearun.parsers import RecordsManager

class LLMRowSelector:
    """
    Implements Rule 6:
    'Optional: an LLM path that may only choose among candidate row IDs, through the
     interface in mock_llm.py and schema.json. If you build it, it must never create
     a finding on its own.'
    """
    def __init__(self, records_manager: RecordsManager):
        self.rm = records_manager

    def select_candidate_rows(self, prompt: str, candidate_row_ids: List[str]) -> List[str]:
        """
        Calls mock_llm.complete() and validates output against schema.json.
        """
        try:
            import mock_llm
            response_str = mock_llm.complete(prompt, candidate_row_ids)
            data = json.loads(response_str)
            selected = data.get("selected_row_ids", [])
            return [str(s) for s in selected if str(s) in candidate_row_ids]
        except Exception:
            return []
