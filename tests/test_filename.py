import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report_generator import storage


class SanitizeTest(unittest.TestCase):
    def test_plain_number(self):
        self.assertEqual(storage.report_base_name(u"123456"), u"Raport_123456")

    def test_invalid_characters_removed(self):
        self.assertEqual(storage.report_base_name(u'SRV/2026\\00:12*?"<>|'),
                         u"Raport_SRV20260012")

    def test_spaces_and_polish_letters(self):
        self.assertEqual(storage.report_base_name(u"  Zgł 12 ąę  "),
                         u"Raport_Zgł_12_ąę")

    def test_empty_ticket(self):
        self.assertEqual(storage.report_base_name(u" / "), u"Raport_bez_numeru")

    def test_reserved_name(self):
        self.assertEqual(storage.sanitize_filename_part(u"CON"), u"_CON")

    def test_trailing_dots_removed(self):
        self.assertEqual(storage.sanitize_filename_part(u"123..."), u"123")


class VersionTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def touch(self, name):
        open(os.path.join(self.dir, name), "w").close()

    def test_versioned_name(self):
        self.assertEqual(storage.versioned_name(u"Raport_1", 1), u"Raport_1")
        self.assertEqual(storage.versioned_name(u"Raport_1", 2), u"Raport_1_v2")

    def test_no_conflict(self):
        self.assertEqual(storage.find_existing(self.dir, u"Raport_1",
                                               [".odt", ".pdf"]), [])

    def test_conflict_detected(self):
        self.touch("Raport_123456.pdf")
        found = storage.find_existing(self.dir, u"Raport_123456", [".odt", ".pdf"])
        self.assertEqual([os.path.basename(p) for p in found], ["Raport_123456.pdf"])

    def test_next_version_v2(self):
        self.touch("Raport_123456.pdf")
        self.assertEqual(storage.next_free_version(
            self.dir, u"Raport_123456", [".odt", ".pdf"]), u"Raport_123456_v2")

    def test_next_version_skips_existing(self):
        for name in ("Raport_123456.pdf", "Raport_123456_v2.pdf",
                     "Raport_123456_v3.odt"):
            self.touch(name)
        self.assertEqual(storage.next_free_version(
            self.dir, u"Raport_123456", [".odt", ".pdf"]), u"Raport_123456_v4")

    def test_target_paths(self):
        paths = storage.target_paths(self.dir, u"Raport_1", True, False)
        self.assertEqual(list(paths), ["odt"])
        self.assertTrue(paths["odt"].endswith("Raport_1.odt"))


class JsonStorageTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_settings_roundtrip_and_defaults(self):
        settings = storage.load_settings(self.dir)
        self.assertTrue(settings["export_pdf"])
        settings["service_name"] = u"Serwis Łódź"
        settings["save_odt"] = False
        storage.save_settings(self.dir, settings)
        loaded = storage.load_settings(self.dir)
        self.assertEqual(loaded["service_name"], u"Serwis Łódź")
        self.assertFalse(loaded["save_odt"])

    def test_invalid_settings_file_falls_back(self):
        with open(os.path.join(self.dir, "settings.json"), "w") as fh:
            fh.write("{to nie jest json")
        self.assertEqual(storage.load_settings(self.dir)["export_pdf"], True)

    def test_custom_phrases(self):
        phrases = storage.add_custom_phrase([], u"TV – test pełny",
                                            u"Test urządzenia / Sprawdzono obraz.")
        phrases = storage.add_custom_phrase(phrases, u"Inna", u"A / b")
        storage.save_custom_phrases(self.dir, phrases)
        loaded = storage.load_custom_phrases(self.dir)
        self.assertEqual([p["title"] for p in loaded], [u"TV – test pełny", u"Inna"])
        loaded = storage.add_custom_phrase(loaded, u"Inna", u"C / d")
        self.assertEqual(len(loaded), 2)
        loaded = storage.remove_custom_phrase(loaded, loaded[0]["id"])
        self.assertEqual([p["title"] for p in loaded], [u"Inna"])

    def test_custom_phrase_requires_text(self):
        with self.assertRaises(ValueError):
            storage.add_custom_phrase([], u"", u"x")


if __name__ == "__main__":
    unittest.main()
