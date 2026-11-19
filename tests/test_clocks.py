import unittest
import os
from plearun.parsers import RecordsManager
from plearun.clocks import ClockSyncEngine

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestClockSync(unittest.TestCase):
    def setUp(self):
        self.rm = RecordsManager(os.path.join(ROOT, "records"))
        self.engine = ClockSyncEngine(self.rm)

    def test_cam07_is_aligned(self):
        # CAM-07 stop at 21:16:48 correlates with CAD on_scene at 21:17:19
        self.assertTrue(self.engine.is_device_aligned("CAM-07"))
        self.assertEqual(self.engine.get_offset_seconds("CAM-07"), 0.0)

    def test_cam03_is_unaligned(self):
        # CAM-03 has conflicting speeds (0 then 61) with no multi-source confirmation
        self.assertFalse(self.engine.is_device_aligned("CAM-03"))
        self.assertIsNone(self.engine.get_offset_seconds("CAM-03"))
        self.assertIn("CAM-03", self.engine.unaligned_devices)

    def test_notes_and_cad_aligned(self):
        self.assertTrue(self.engine.is_device_aligned("Officer Lee"))
        self.assertTrue(self.engine.is_device_aligned("Dispatch"))
        self.assertTrue(self.engine.is_device_aligned("CAD"))

if __name__ == "__main__":
    unittest.main()
