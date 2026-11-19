import os
import re
from typing import List
from plearun.models import RecordRow
from plearun.parsers.base import read_file_lines_with_encoding

def parse_timecode(tc: str) -> float:
    """Parses HH:MM:SS.mmm or MM:SS.mmm into total seconds."""
    parts = tc.strip().split(":")
    if len(parts) == 3:
        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
        return h * 3600.0 + m * 60.0 + s
    elif len(parts) == 2:
        m, s = float(parts[0]), float(parts[1])
        return m * 60.0 + s
    return 0.0

def parse_vtt_record_file(file_path: str) -> List[RecordRow]:
    """
    Parses a WebVTT transcript file.
    Handles:
    - Standard WEBVTT header
    - Numeric cue identifiers or cue timing lines
    - Overlapping cue intervals
    - Speaker prefixes: [TAG] Speaker: Text
    - Assigns 1-based cue number as row_num
    - Preserves raw text of the spoken cue line for quote substring matching.
    """
    raw_lines, encoding = read_file_lines_with_encoding(file_path)
    file_name = os.path.basename(file_path)
    records: List[RecordRow] = []

    cue_counter = 0
    i = 0
    n = len(raw_lines)

    while i < n:
        line = raw_lines[i].strip()
        # Look for timing line: e.g. "00:00:00.000 --> 00:00:04.000"
        if "-->" in line:
            cue_counter += 1
            timing_parts = line.split("-->")
            start_tc = timing_parts[0].strip()
            end_tc = timing_parts[1].split()[0].strip() if len(timing_parts) > 1 else ""

            start_sec = parse_timecode(start_tc)
            end_sec = parse_timecode(end_tc)

            # Collect subsequent text lines for this cue
            text_lines = []
            raw_text_line = ""
            i += 1
            while i < n and raw_lines[i].strip() and "-->" not in raw_lines[i]:
                text_lines.append(raw_lines[i].strip())
                if not raw_text_line:
                    raw_text_line = raw_lines[i]
                i += 1

            full_cue_text = " ".join(text_lines)
            if not raw_text_line and text_lines:
                raw_text_line = text_lines[0]

            # Extract speaker if present (e.g. "[SYNTHETIC] Officer Lee: 58 in a 45.")
            speaker = ""
            msg = full_cue_text
            speaker_match = re.search(r'(?:\[.*?\]\s*)?([A-Za-z0-9\s]+):\s*(.*)', full_cue_text)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                msg = speaker_match.group(2).strip()

            rec = RecordRow(
                file_name=file_name,
                row_num=cue_counter,
                raw_text=raw_text_line if raw_text_line else full_cue_text,
                device=speaker if speaker else "bodycam",
                data={
                    "cue_num": cue_counter,
                    "start_sec": start_sec,
                    "end_sec": end_sec,
                    "speaker": speaker,
                    "text": msg,
                    "full_text": full_cue_text
                }
            )
            records.append(rec)
            continue
        i += 1

    return records
