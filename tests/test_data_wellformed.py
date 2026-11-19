import csv, json, unittest, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class SampleData(unittest.TestCase):
    def test_camera_log_has_marker_and_header(self):
        with open(os.path.join(ROOT, "records/camera_log.csv"), encoding="utf-8-sig") as f:
            raw = f.read().splitlines()
        self.assertTrue(raw[0].startswith("#PLEARUN"))
        self.assertEqual(raw[1], "timestamp,device,speed_mph,zone_mph")

    def test_dispatch_json_parses(self):
        with open(os.path.join(ROOT, "records/dispatch.json"), encoding="utf-8") as f:
            json.load(f)

    def test_notes_decode_as_cp1252(self):
        with open(os.path.join(ROOT, "records/notes_cp1252.csv"), "rb") as f:
            f.read().decode("cp1252")

    def test_transcript_is_webvtt(self):
        with open(os.path.join(ROOT, "records/bodycam_transcript.vtt"), encoding="utf-8") as f:
            self.assertTrue(f.read().startswith("WEBVTT"))

if __name__ == "__main__":
    unittest.main()
