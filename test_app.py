import tempfile
import unittest
from pathlib import Path

import app as brandvagt


class BrandvagtApiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_status_file = brandvagt.STATUS_FILE
        brandvagt.STATUS_FILE = Path(self.tempdir.name) / "status.json"
        brandvagt.app.config.update(TESTING=True)
        self.client = brandvagt.app.test_client()

    def tearDown(self):
        brandvagt.STATUS_FILE = self.original_status_file
        self.tempdir.cleanup()

    def test_toggle_rejects_unknown_role(self):
        response = self.client.post("/toggle", json={"vehicle": "M1", "role": "UKENDT"})
        self.assertEqual(response.status_code, 400)

    def test_toggle_persists_boolean_state(self):
        first = self.client.post("/toggle", json={"vehicle": "M1", "role": "CHF"})
        second = self.client.post("/toggle", json={"vehicle": "M1", "role": "CHF"})
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.get_json()["active"])
        self.assertFalse(second.get_json()["active"])

    def test_reset_clears_status(self):
        self.client.post("/toggle", json={"vehicle": "M1", "role": "CHF"})
        response = self.client.post("/reset")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(brandvagt.load_status(), {})


if __name__ == "__main__":
    unittest.main()
