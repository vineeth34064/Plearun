import re
from typing import List
from plearun.models import Claim

def is_header_or_metadata(line: str) -> bool:
    """Detects synthetic header lines or case metadata lines that are not factual claims."""
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("#"):
        return True
    lower = stripped.lower()
    if "synthetic - fictional case" in lower:
        return True
    if lower.startswith("case:") or lower.startswith("incident number:") or lower.startswith("page "):
        return True
    return False

def extract_claims_from_report(report_path: str) -> List[Claim]:
    """
    Reads an incident report and splits narrative claims as written in the report.
    Extracts semantic entities, times, speeds, and action types.
    """
    with open(report_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()

    # Filter out header / metadata lines
    narrative_lines = []
    for line in lines:
        if is_header_or_metadata(line):
            continue
        narrative_lines.append(line.strip())

    narrative_text = " ".join(narrative_lines)
    # Segment sentences cleanly on period, exclamation, or question mark followed by space and capital letter
    raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', narrative_text)

    claims: List[Claim] = []
    for idx, s in enumerate(raw_sentences, 1):
        s_clean = s.strip()
        if not s_clean:
            continue

        times = re.findall(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', s_clean)
        # Check relative times like "2 minutes after"
        rel_time = re.findall(r'\b\d+\s+(?:minutes|mins|seconds|secs|hours)\b', s_clean, flags=re.IGNORECASE)
        times.extend(rel_time)

        speeds = [float(x) for x in re.findall(r'\b(\d+)\s*(?:mph|kph|km/h)\b', s_clean, flags=re.IGNORECASE)]
        zones = [float(x) for x in re.findall(r'(?:zone|limit|posted)\s*(?:of)?\s*(\d+)', s_clean, flags=re.IGNORECASE)]
        if not zones:
            # check "posted 45"
            zones = [float(x) for x in re.findall(r'posted\s+(\d+)', s_clean, flags=re.IGNORECASE)]

        entities = []
        for e in ["Officer Lee", "Dispatch", "911 call", "sedan", "vehicle", "driver", "unit"]:
            if e.lower() in s_clean.lower():
                entities.append(e)

        # Detect action type
        action_type = "general"
        lower_s = s_clean.lower()
        is_checkable = True

        if "only car" in lower_s or "only vehicle" in lower_s or "empty lane" in lower_s or "lane" in lower_s:
            action_type = "lane_occupancy"
            # Machine records (camera, CAD, notes, bodycam) do NOT record lane occupancy/density
            is_checkable = False
        elif "unit on scene" in lower_s or "on scene" in lower_s:
            action_type = "unit_on_scene"
        elif "911 call" in lower_s or "logged at" in lower_s:
            action_type = "call_logged"
        elif "stopped" in lower_s or "pulled into" in lower_s or "lot" in lower_s:
            action_type = "stop"
        elif "mph" in lower_s or "speed" in lower_s or "travelling" in lower_s:
            action_type = "speed"

        c = Claim(
            raw_text=s_clean,
            sentence_idx=idx,
            times=times,
            speeds=speeds,
            speed_zones=zones,
            entities=entities,
            action_type=action_type,
            is_checkable=is_checkable
        )
        claims.append(c)

    return claims
