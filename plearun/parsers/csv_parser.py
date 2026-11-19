import csv
import io
import os
from typing import List
from plearun.models import RecordRow
from plearun.parsers.base import read_file_lines_with_encoding, parse_flexible_timestamp

def parse_csv_record_file(file_path: str) -> List[RecordRow]:
    """
    Parses a CSV record file (such as camera_log.csv or notes_cp1252.csv).
    Resilient to:
    - BOM (UTF-8 sig)
    - CP1252 / Windows-1252 encoding
    - Comment lines starting with #
    - Preserves exact 1-based line numbers for citation and raw quote verification.
    """
    raw_lines, encoding = read_file_lines_with_encoding(file_path)
    file_name = os.path.basename(file_path)
    records: List[RecordRow] = []

    header_cols = None
    header_line_idx = -1

    for line_idx, raw_line in enumerate(raw_lines, 1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if header_cols is None:
            # Parse header row using standard csv reader
            reader = csv.reader(io.StringIO(raw_line))
            cols = next(reader, [])
            header_cols = [c.strip() for c in cols]
            header_line_idx = line_idx
            continue

        # Data row
        reader = csv.reader(io.StringIO(raw_line))
        cols = next(reader, [])
        if not cols:
            continue

        data_dict = {}
        for col_name, col_val in zip(header_cols, cols):
            data_dict[col_name] = col_val.strip()

        # Identify timestamp/time column
        ts_val = None
        for key in ["timestamp", "time", "Time", "logged", "date", "Date"]:
            if key in data_dict:
                ts_val = data_dict[key]
                break

        dt_obj, t_obj = parse_flexible_timestamp(ts_val)

        # Identify device / author / camera column
        device_val = None
        for key in ["device", "Device", "camera", "Camera", "author", "Author", "unit", "Unit"]:
            if key in data_dict:
                device_val = data_dict[key]
                break

        rec = RecordRow(
            file_name=file_name,
            row_num=line_idx,
            raw_text=raw_line,
            timestamp=dt_obj,
            time_of_day=t_obj,
            device=device_val,
            data=data_dict
        )
        records.append(rec)

    return records
