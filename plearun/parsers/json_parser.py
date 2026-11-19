import json
import os
from typing import List, Dict, Any
from plearun.models import RecordRow
from plearun.parsers.base import read_file_lines_with_encoding, parse_flexible_timestamp

def parse_json_record_file(file_path: str) -> List[RecordRow]:
    """
    Parses a JSON record file (such as CAD/dispatch exports).
    Handles:
    - Nested JSON objects (e.g. export.events list)
    - Flat JSON event arrays
    - Maps events to their exact 1-based line numbers in the original file
    - Normalizes mixed timestamp formats (ISO8601, space-separated, Unix ms).
    """
    raw_lines, encoding = read_file_lines_with_encoding(file_path)
    file_name = os.path.basename(file_path)
    full_text = "\n".join(raw_lines)

    try:
        data = json.loads(full_text)
    except Exception:
        return []

    # Extract event list from common CAD structures
    events: List[Dict[str, Any]] = []
    if isinstance(data, dict):
        if "export" in data and isinstance(data["export"], dict) and "events" in data["export"]:
            events = data["export"]["events"]
        elif "events" in data and isinstance(data["events"], list):
            events = data["events"]
        else:
            events = [data]
    elif isinstance(data, list):
        events = data

    records: List[RecordRow] = []

    for ev in events:
        if not isinstance(ev, dict):
            continue

        ev_id = str(ev.get("id", ""))
        ev_type = str(ev.get("type", ""))
        logged = ev.get("logged")
        unit = str(ev.get("unit", ""))

        dt_obj, t_obj = parse_flexible_timestamp(logged)

        # Locate the best matching line number in the raw JSON file
        # We search for lines containing the event ID or the logged value or event type
        matched_line_num = -1
        matched_raw_text = ""

        # Priority 1: line containing the exact logged timestamp string or id
        for l_idx, line in enumerate(raw_lines, 1):
            if ev_id and f'"{ev_id}"' in line:
                matched_line_num = l_idx
                matched_raw_text = line
                break

        # Priority 2: line containing logged value specifically
        if logged is not None:
            logged_str = str(logged)
            for l_idx, line in enumerate(raw_lines, 1):
                if logged_str in line and "logged" in line:
                    matched_line_num = l_idx
                    matched_raw_text = line
                    break

        if matched_line_num == -1 and raw_lines:
            matched_line_num = 1
            matched_raw_text = raw_lines[0]

        rec = RecordRow(
            file_name=file_name,
            row_num=matched_line_num,
            raw_text=matched_raw_text,
            timestamp=dt_obj,
            time_of_day=t_obj,
            device=unit if unit else "CAD",
            data={
                "id": ev_id,
                "type": ev_type,
                "logged": logged,
                "unit": unit
            }
        )
        records.append(rec)

    return records
