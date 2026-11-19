import unittest
import os
from plearun.parsers import RecordsManager
from plearun.parsers.csv_parser import parse_csv_record_file
from plearun.parsers.json_parser import parse_json_record_file
from plearun.parsers.vtt_parser import parse_vtt_record_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestRecordParsers(unittest.TestCase):
    def setUp(self):
        self.records_dir = os.path.join(ROOT, "records")
        self.rm = RecordsManager(self.records_dir)

    def test_camera_log_parsing(self):
        records = parse_csv_record_file(os.path.join(self.records_dir, "camera_log.csv"))
        self.assertGreater(len(records), 0)
        # Check first data row (Line 3 in camera_log.csv)
        row1 = records[0]
        self.assertEqual(row1.row_num, 3)
        self.assertEqual(row1.device, "CAM-07")
        self.assertEqual(row1.data["speed_mph"], "42")
        self.assertIsNotNone(row1.timestamp)

    def test_notes_cp1252_parsing(self):
        records = parse_csv_record_file(os.path.join(self.records_dir, "notes_cp1252.csv"))
        self.assertEqual(len(records), 3)
        # Check Row N-3 (Line 4 in file)
        row3 = records[2]
        self.assertEqual(row3.row_num, 4)
        self.assertEqual(row3.device, "Officer Lee")
        self.assertIn("Stopped at lot", row3.data["Note"])
        self.assertEqual(row3.data["Time"], "21:16")

    def test_dispatch_json_parsing(self):
        records = parse_json_record_file(os.path.join(self.records_dir, "dispatch.json"))
        self.assertEqual(len(records), 3)
        ev_types = [r.data["type"] for r in records]
        self.assertIn("911_call", ev_types)
        self.assertIn("unit_on_scene", ev_types)
        self.assertIn("unit_dispatched", ev_types)

        # Check line numbering maps to real lines in file
        for r in records:
            self.assertGreater(r.row_num, 0)
            raw = self.rm.get_raw_row_text(r.file_name, r.row_num)
            self.assertIsNotNone(raw)

    def test_vtt_parsing_with_overlaps(self):
        records = parse_vtt_record_file(os.path.join(self.records_dir, "bodycam_transcript.vtt"))
        self.assertEqual(len(records), 3)
        # Cue 1: 00:00:00.000 to 00:00:04.000
        # Cue 2: 00:00:03.500 to 00:00:07.000 (starts before Cue 1 ends!)
        cue1 = records[0]
        cue2 = records[1]
        self.assertEqual(cue1.row_num, 1)
        self.assertEqual(cue2.row_num, 2)
        self.assertLess(cue2.data["start_sec"], cue1.data["end_sec"])
        self.assertEqual(cue1.data["speaker"], "Officer Lee")
        self.assertIn("58 in a 45", cue1.data["text"])

    def test_raw_quote_verification(self):
        # notes_cp1252.csv row 4
        self.assertTrue(self.rm.verify_quote("notes_cp1252.csv", 4, "Stopped at lot ~21:16,21:16"))
        self.assertTrue(self.rm.verify_quote("notes_cp1252.csv", 4, "21:16"))
        # Invalid substring should fail
        self.assertFalse(self.rm.verify_quote("notes_cp1252.csv", 4, "Stopped at station"))

if __name__ == "__main__":
    unittest.main()
