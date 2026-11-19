import os
from typing import Dict, List, Optional, Tuple
from plearun.models import RecordRow
from plearun.parsers.csv_parser import parse_csv_record_file
from plearun.parsers.json_parser import parse_json_record_file
from plearun.parsers.vtt_parser import parse_vtt_record_file
from plearun.parsers.base import read_file_lines_with_encoding

class RecordsManager:
    """
    Manages loading, indexing, and validating all machine record files in RECORDS_DIR.
    """
    def __init__(self, records_dir: str):
        self.records_dir = os.path.abspath(records_dir)
        self.records_by_file: Dict[str, List[RecordRow]] = {}
        self.raw_lines_by_file: Dict[str, List[str]] = {}
        self.all_records: List[RecordRow] = []
        self._load_records()

    def _load_records(self) -> None:
        if not os.path.isdir(self.records_dir):
            return

        for fname in sorted(os.listdir(self.records_dir)):
            fpath = os.path.join(self.records_dir, fname)
            if not os.path.isfile(fpath):
                continue

            # Load raw lines for exact line-level verification
            lines, _ = read_file_lines_with_encoding(fpath)
            self.raw_lines_by_file[fname] = lines

            lower_name = fname.lower()
            file_records: List[RecordRow] = []

            if lower_name.endswith(".csv"):
                file_records = parse_csv_record_file(fpath)
            elif lower_name.endswith(".json"):
                file_records = parse_json_record_file(fpath)
            elif lower_name.endswith(".vtt"):
                file_records = parse_vtt_record_file(fpath)

            self.records_by_file[fname] = file_records
            self.all_records.extend(file_records)

    def get_raw_row_text(self, file_name: str, row_num: int) -> Optional[str]:
        """
        Retrieves the exact raw text for a cited file and row number.
        For VTT: row_num is the cue number.
        For CSV / JSON: row_num is the 1-based line number.
        """
        if file_name not in self.records_by_file:
            return None

        # Check records loaded for this file
        for rec in self.records_by_file[file_name]:
            if rec.row_num == row_num:
                return rec.raw_text

        # Fallback to direct raw line access if valid line index
        if file_name in self.raw_lines_by_file:
            lines = self.raw_lines_by_file[file_name]
            if 1 <= row_num <= len(lines):
                return lines[row_num - 1]

        return None

    def verify_quote(self, file_name: str, row_num: int, quote: str) -> bool:
        """
        Rule 1 check: Verifies that quote is an exact substring of the raw text of that row.
        """
        if not file_name or row_num is None or not quote:
            return False

        raw_row = self.get_raw_row_text(file_name, row_num)
        if raw_row is None:
            return False

        return quote in raw_row
