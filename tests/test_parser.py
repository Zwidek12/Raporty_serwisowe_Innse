import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report_generator.parser import (Item, append_line, parse_block,
                                     parse_line)


class ParseLineTest(unittest.TestCase):
    def test_basic_split(self):
        self.assertEqual(parse_line(u"Zasilanie / Telewizor nie uruchamia się."),
                         Item(u"Zasilanie", u"Telewizor nie uruchamia się."))

    def test_split_only_on_first_slash(self):
        item = parse_line(u"Test USB / Sprawdzono ładowanie/komunikację z komputerem.")
        self.assertEqual(item.label, u"Test USB")
        self.assertEqual(item.text, u"Sprawdzono ładowanie/komunikację z komputerem.")
        self.assertEqual(item.as_line(),
                         u"Test USB: Sprawdzono ładowanie/komunikację z komputerem.")

    def test_many_slashes(self):
        item = parse_line(u"Wejścia / HDMI 1/2/3/4 oraz USB-C/DP sprawdzone")
        self.assertEqual(item.label, u"Wejścia")
        self.assertEqual(item.text, u"HDMI 1/2/3/4 oraz USB-C/DP sprawdzone")

    def test_no_slash_is_plain_item(self):
        item = parse_line(u"Urządzenie przekazano do dalszej obsługi.")
        self.assertFalse(item.has_label)
        self.assertEqual(item.as_line(), u"Urządzenie przekazano do dalszej obsługi.")

    def test_empty_and_whitespace_lines(self):
        self.assertIsNone(parse_line(u""))
        self.assertIsNone(parse_line(u"    \t  "))
        self.assertIsNone(parse_line(None))
        self.assertIsNone(parse_line(u" / "))

    def test_extra_spaces_are_normalized(self):
        item = parse_line(u"   Dioda   LED    /    Brak   sygnalizacji  stanu pracy.  ")
        self.assertEqual(item, Item(u"Dioda LED", u"Brak sygnalizacji stanu pracy."))

    def test_polish_characters(self):
        item = parse_line(u"Źródło zasilania / Zażółć gęślą jaźń ĄĆĘŁŃÓŚŹŻ.")
        self.assertEqual(item.label, u"Źródło zasilania")
        self.assertEqual(item.text, u"Zażółć gęślą jaźń ĄĆĘŁŃÓŚŹŻ.")

    def test_empty_label_or_text(self):
        self.assertEqual(parse_line(u"/ sam opis"), Item(u"", u"sam opis"))
        self.assertEqual(parse_line(u"Sama etykieta /"), Item(u"", u"Sama etykieta"))

    def test_trailing_colon_in_label(self):
        self.assertEqual(parse_line(u"Obudowa: / bez uszkodzeń"),
                         Item(u"Obudowa", u"bez uszkodzeń"))

    def test_manual_bullet_removed(self):
        self.assertEqual(parse_line(u"• Audio / Dźwięk prawidłowy."),
                         Item(u"Audio", u"Dźwięk prawidłowy."))
        self.assertEqual(parse_line(u"- Audio / Dźwięk prawidłowy."),
                         Item(u"Audio", u"Dźwięk prawidłowy."))

    def test_negative_number_not_treated_as_bullet(self):
        self.assertEqual(parse_line(u"-5°C / temperatura testu").label, u"-5°C")

    def test_long_text(self):
        desc = u"bardzo długi opis " * 200
        item = parse_line(u"Ekspertyza / " + desc)
        self.assertEqual(item.text, desc.strip())

    def test_text_is_not_interpreted(self):
        item = parse_line(u"Ładowanie / nie ładuje")
        self.assertEqual(item.text, u"nie ładuje")


class ParseBlockTest(unittest.TestCase):
    def test_block_with_empty_lines_and_crlf(self):
        text = (u"Zasilanie / Telewizor nie uruchamia się.\r\n\r\n"
                u"Dioda LED / Brak sygnalizacji stanu pracy.\r\n   \n"
                u"Obudowa / Nie stwierdzono uszkodzeń mechanicznych.\n")
        items = parse_block(text)
        self.assertEqual([i.label for i in items],
                         [u"Zasilanie", u"Dioda LED", u"Obudowa"])

    def test_empty_block(self):
        self.assertEqual(parse_block(u""), [])
        self.assertEqual(parse_block(None), [])
        self.assertEqual(parse_block(u"\n\n  \n"), [])


class AppendLineTest(unittest.TestCase):
    def test_append_to_empty(self):
        self.assertEqual(append_line(u"", u"A / b"), u"A / b")

    def test_append_adds_newline(self):
        self.assertEqual(append_line(u"A / b", u"C / d"), u"A / b\nC / d")

    def test_append_trims_trailing_newlines(self):
        self.assertEqual(append_line(u"A / b\n\n", u"C / d"), u"A / b\nC / d")


if __name__ == "__main__":
    unittest.main()
