# Plearun Verified Findings Engine

A high-precision, offline verification engine that audits factual claims in incident reports against multimodal machine records (traffic radar camera logs, CAD dispatch exports, officer field notes, and body-camera transcripts).

---

## 1. How It Works

The engine runs as a deterministic, offline pipeline in `plearun_cli.py`:

```
Incident Report & Machine Records
               │
               ▼
┌─────────────────────────────────┐
│ 1. Encoding-Resilient Parsers   │ ──► Handles BOM, CP1252, marker lines (#PLEARUN),
│    (CSV, JSON, WebVTT)          │     three CAD timestamp formats, overlapping cues.
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 2. Clock Synchronization Engine │ ──► Estimates offsets via multi-source anchor events;
│    (Rule 3 Calibration)         │     quarantines uncorroborated devices (e.g. CAM-03).
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 3. Narrative Claim Extractor    │ ──► Filters synthetic headers; segments claims;
│                                 │     extracts times, speeds, entities, checkability.
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 4. Defensible Verification      │ ──► Classifies claims into: match, conflict,
│    Decision Tree (Rule 2)       │     not_settled, or not_checkable.
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 5. Strict Rule 1 Enforcer       │ ──► Verifies quotes are exact substrings of cited
│    & Serializer                 │     raw rows; safely downgrades failures to not_settled.
└─────────────────────────────────┘
```

1. **Record Parsing**: Auto-detects encoding (`utf-8-sig`, `cp1252`, `utf-8`), strips BOMs and `#` comment lines, tracks 1-based raw line numbers, maps nested CAD JSON events, and normalizes WebVTT cues with overlapping intervals.
2. **Clock Offset Estimation (Rule 3)**: Discovers shared anchor events across sources (e.g., lot stop at 21:16 vs CAD `unit_on_scene` at 21:17:19). Aligns verified devices (CAM-07, CAD, Notes) and refuses to align uncorroborated devices (CAM-03).
3. **Claim Extraction**: Extracts discrete narrative claims as written in the report, ignoring synthetic file headers.
4. **Verification**: Compares factual assertions (speeds, times, arrival latency) against calibrated machine evidence.
5. **Rule 1 Enforcement**: Validates that every `match` or `conflict` cites a real row and that `quote` is an exact substring of that row. If verification fails, it immediately downgrades to `not_settled` and omits `cite` and `quote`.

---

## 2. Three Hardest Decisions Made

1. **Speed Discrepancy (Camera 62 mph vs Bodycam 58 mph)**:
   Officer Lee stated "58 in a 45" on bodycam (Cue 1), yet calibrated traffic camera CAM-07 at 21:14:38 recorded 62 mph (Row 18). Because CAM-07 lacks license plate identification (Notes state "plate unknown"), one could argue for `not_settled`. However, the report explicitly asserts the vehicle was travelling 58 mph at 21:14 near mile marker 4. The objective radar camera at that exact mile marker and minute directly refutes 58 mph with 62 mph. We chose `conflict` citing CAM-07 Row 18, representing the ground-truth physical sensor.

2. **Quarantining CAM-03 Under Rule 3**:
   CAM-03 records `speed=0` at 21:15:18, but immediately records `speed=61` at 21:15:20 (2 seconds later). Unlike CAM-07 (whose 21:16:48 stop correlates with the lot arrival and CAD on-scene event at 21:17:19), CAM-03 provides no corroborated multi-source anchor. Per Rule 3, we refused to speculate on an offset and quarantined CAM-03 as unaligned, preventing false findings.

3. **Demarcating `not_checkable` vs `not_settled`**:
   Claims like *"Officer Lee states the vehicle was the only car in the lane"* cannot be verified because no available machine record captures lane traffic density. Rather than marking this `not_settled` (which implies relevant evidence exists but is inconclusive), we mark it `not_checkable`, maintaining a clean legal boundary between unrecorded facts and unresolved evidence.

---

## 3. What It Gets Wrong

- **Multi-Fact Compound Sentences**: If a single sentence contains two factual claims with opposing truth values (e.g. an accurate stop time combined with an inaccurate speed), sentence-level extraction treats the sentence as a unit and evaluates the dominant factual assertion.
- **Human Rounding vs. True Conflict**: A human note written at 21:11 regarding a 911 call logged by CAD at 21:10:19 is a 41-second difference. The tool classifies this as a `conflict` with the CAD export, though a human auditor might interpret it as natural clock rounding.
- **Complex Semantic Paraphrasing**: The rule-based extractor uses semantic regex and entity models; unconventional wording in novel reports could miss unstructured factual assertions without LLM row-selection assistance.

---

## 4. What Would Break First on Real Records

1. **High-Throughput Streaming Records**: In-memory parsing of CSV/JSON files would exhaust memory on multi-gigabyte continuous sensor feeds (e.g. millions of camera reads). Real records require chunked stream parsing or SQLite/DuckDB indexing.
2. **Dense Traffic Disambiguation**: On high-density multi-lane highways without automated license plate recognition (ALPR), assigning a single radar speed reading to a specific vehicle requires vehicle trajectory re-identification across successive cameras.
3. **Messy Human Inputs & Timezone Boundaries**: Real police files contain scanned handwritten notes, fragmented audio transcripts, OCR artifacts, and Daylight Saving Time (DST) shifts across jurisdictional CAD systems.

---

## 5. Tools Used & AI-Assisted Development

- **Antigravity (AI Coding Assistant)**: Used for architecture design, iterative test-driven development, and rapid adversarial vulnerability probing.
- **Python 3.13 Standard Library**: Zero external runtime dependencies; uses built-in `csv`, `json`, `re`, `datetime`, and `unittest`.
- **Git & GNU Make**: Version control and offline test orchestration (`make test`).
- *Human Ownership*: Every line of code, regex rule, clock offset formula, and verification decision was reviewed, tested, and validated to ensure full defensibility during technical review.

---

## Quickstart

```bash
# Run unit tests offline
make test

# Run verification pipeline on sample
python3 plearun_cli.py reports/report_fictional_02.txt records > findings.json
```
