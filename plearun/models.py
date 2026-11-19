from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional, Dict, Any, List

@dataclass
class RecordRow:
    """Represents a single row or cue from a machine record file."""
    file_name: str
    row_num: int            # 1-based line number or cue number
    raw_text: str           # exact raw line/text in the file
    timestamp: Optional[datetime] = None
    time_of_day: Optional[time] = None
    device: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Claim:
    """Represents a factual statement extracted from a report."""
    raw_text: str
    sentence_idx: int
    times: List[str] = field(default_factory=list)
    speeds: List[float] = field(default_factory=list)
    speed_zones: List[float] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    action_type: str = "general" # speed, stop, call_logged, unit_on_scene, lane_occupancy, etc.
    is_checkable: bool = True

@dataclass
class Finding:
    """Represents a verification finding for a claim."""
    claim: str
    finding: str            # 'match', 'conflict', 'not_settled', 'not_checkable'
    cite_file: Optional[str] = None
    cite_row: Optional[int] = None
    quote: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to the required JSON schema output format."""
        out: Dict[str, Any] = {
            "claim": self.claim,
            "finding": self.finding
        }
        if self.finding in ("match", "conflict"):
            out["cite"] = {
                "file": self.cite_file,
                "row": self.cite_row
            }
            out["quote"] = self.quote
        return out
