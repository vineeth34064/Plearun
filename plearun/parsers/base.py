import os
import re
from datetime import datetime, time, timezone, timedelta
from typing import List, Tuple, Optional, Any

# Standard reference timezone: EST/EDT (-05:00) as observed in the incident data
DEFAULT_TZ = timezone(timedelta(hours=-5))

def read_file_lines_with_encoding(file_path: str) -> Tuple[List[str], str]:
    """
    Reads a file attempting utf-8-sig, utf-8, cp1252, and latin-1.
    Returns (list of raw lines without trailing newlines, encoding_used).
    Preserves exact 1-based indexing for line numbers.
    """
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                lines = f.read().splitlines()
                return lines, enc
        except UnicodeDecodeError:
            continue
    # Fallback with replacement to never crash on unexpected byte sequences
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines(), "utf-8-replace"

def parse_flexible_timestamp(val: Any) -> Tuple[Optional[datetime], Optional[time]]:
    """
    Parses timestamps from various formats:
    - Integer / float Unix ms (e.g. 1772504040000)
    - Integer / float Unix seconds (e.g. 1772504040)
    - ISO8601 strings (e.g. '2026-03-02T21:17:19-05:00')
    - Space-separated strings (e.g. '2026-03-02 21:10:19')
    - Time-only strings (e.g. '21:15', '~21:16', '21:10:19')
    Returns (datetime_obj or None, time_of_day or None).
    """
    if val is None:
        return None, None

    # Handle numeric timestamps
    if isinstance(val, (int, float)):
        ts = float(val)
        if ts > 1e11:  # Milliseconds
            ts = ts / 1000.0
        try:
            dt = datetime.fromtimestamp(ts, tz=DEFAULT_TZ)
            return dt, dt.time()
        except Exception:
            return None, None

    val_str = str(val).strip()

    # Check if purely digits (string representation of unix timestamp)
    if val_str.isdigit():
        ts = float(val_str)
        if ts > 1e11:
            ts = ts / 1000.0
        try:
            dt = datetime.fromtimestamp(ts, tz=DEFAULT_TZ)
            return dt, dt.time()
        except Exception:
            return None, None

    # Clean leading tildes or approximate markers (e.g. '~21:16')
    clean_str = re.sub(r'^[~approx\.\s]+', '', val_str, flags=re.IGNORECASE).strip()

    # Try ISO8601 parsing
    try:
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=DEFAULT_TZ)
        return dt, dt.time()
    except Exception:
        pass

    # Try space-separated datetime: YYYY-MM-DD HH:MM:SS
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(clean_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=DEFAULT_TZ)
            return dt, dt.time()
        except Exception:
            pass

    # Try time-only formats: HH:MM:SS or HH:MM
    time_match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', clean_str)
    if time_match:
        hr = int(time_match.group(1))
        mn = int(time_match.group(2))
        sc = int(time_match.group(3)) if time_match.group(3) else 0
        t_obj = time(hr, mn, sc)
        return None, t_obj

    return None, None
