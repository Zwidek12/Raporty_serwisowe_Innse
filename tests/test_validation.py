import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report_generator import constants as C
from report_generator.phrases import PhraseLibrary
from report_generator.report_model import build_report, report_as_text
from report_generator.validators import (normalize_date, parse_date,
                                         status_change_warning, validate)


def form(**kw):
    data = {
        "ticket": u"123456", "report_date": u"04.10.2026", "receipt_date": u"",
        "technician": u"", "manufacturer": u"SONY", "model": u"KE85XH9096",
        "serial": u"SN1", "device_type_text": u"", "report_type": C.RT_REPAIR,
        "status": C.ST_REPAIRED, "custom_status": u"",
        "customer": u"", "diagnosis": u"Zasilanie / Brak reakcji.",
        "work": u"Blok zasilacza / Wymieniono płytę zasilającą.",
        "tests": u"Test / OK", "diagnosis_intro": 0, "tests_intro": 0,
    }
    data.update(kw)
    return data


class RequiredFieldsTest(unittest.TestCase):
    def test_valid_form(self):
        errors, warnings = validate(form())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_required_fields(self):
        for key in ("ticket", "report_date", "manufacturer", "model", "diagnosis"):
            errors, _ = validate(form(**{key: u"   "}))
            self.assertEqual(len(errors), 1, key)

    def test_diagnosis_with_only_empty_lines(self):
        errors, _ = validate(form(diagnosis=u"\n  \n"))
        self.assertTrue(any(u"Diagnoza" in e for e in errors))

    def test_invalid_dates(self):
        errors, _ = validate(form(report_date=u"31.02.2026"))
        self.assertEqual(len(errors), 1)
        errors, _ = validate(form(receipt_date=u"jutro"))
        self.assertEqual(len(errors), 1)

    def test_missing_serial_is_only_warning(self):
        errors, warnings = validate(form(serial=u""))
        self.assertEqual(errors, [])
        self.assertTrue(any(u"seryjnego" in w for w in warnings))

    def test_custom_status_requires_text(self):
        errors, _ = validate(form(status=C.ST_CUSTOM, custom_status=u" "))
        self.assertEqual(len(errors), 1)


class LogicalWarningsTest(unittest.TestCase):
    def test_repaired_without_work(self):
        _, warnings = validate(form(work=u""))
        self.assertTrue(any(u"Wykonane czynności" in w for w in warnings))
        self.assertIsNotNone(status_change_warning(C.ST_REPAIRED, u""))
        self.assertIsNone(status_change_warning(C.ST_REPAIRED, u"A / b"))
        self.assertIsNone(status_change_warning(C.ST_WEAR, u""))

    def test_repaired_without_tests(self):
        _, warnings = validate(form(tests=u""))
        self.assertTrue(any(u"Testy końcowe" in w for w in warnings))

    def test_not_confirmed_with_repair_words(self):
        _, warnings = validate(form(
            status=C.ST_NOT_CONFIRMED, report_type=C.RT_NOT_CONFIRMED, work=u"",
            diagnosis=u"Matryca / Wymieniono matrycę."))
        self.assertTrue(any(u"niepotwierdzona" in w for w in warnings))

    def test_not_confirmed_with_work(self):
        _, warnings = validate(form(status=C.ST_NOT_CONFIRMED,
                                    report_type=C.RT_NOT_CONFIRMED))
        self.assertTrue(any(u"Wykonane czynności" in w for w in warnings))

    def test_placeholder_warning(self):
        _, warnings = validate(form(
            work=u"Część / Wymieniono element [nazwa], nr części: [numer]."))
        self.assertTrue(any(u"[nazwa]" in w for w in warnings))


class DatesTest(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(normalize_date(u"4.10.2026"), u"04.10.2026")
        self.assertEqual(normalize_date(u"2026-10-04"), u"04.10.2026")
        self.assertEqual(normalize_date(u"04/10/2026"), u"04.10.2026")
        self.assertIsNone(parse_date(u"2026.13.01"))


class StatusMapTest(unittest.TestCase):
    def test_every_status_has_text(self):
        for status in C.STATUSES:
            if status in (C.ST_NONE, C.ST_CUSTOM):
                continue
            self.assertTrue(C.STATUS_TEXTS.get(status), status)

    def test_status_texts_exact(self):
        self.assertEqual(
            C.STATUS_TEXTS[C.ST_REPAIRED],
            u"Urządzenie zostało przywrócone do prawidłowej sprawności technicznej "
            u"i funkcjonalnej. Sprzęt jest gotowy do dalszego użytkowania.")
        self.assertEqual(
            C.STATUS_TEXTS[C.ST_WEAR],
            u"Diagnostyka wykazała zużycie eksploatacyjne wskazanego elementu.")

    def test_no_failure_word_in_automatic_texts(self):
        automatic = (list(C.STATUS_TEXTS.values()) + C.DIAGNOSIS_INTROS
                     + C.TESTS_INTROS + list(C.WORK_INTROS.values())
                     + [C.WORK_INTRO_DEFAULT] + list(C.REPORT_TITLES.values()))
        for text in automatic:
            self.assertNotIn(u"awari", text.lower(), text)

    def test_warranty_status_makes_no_future_claims(self):
        text = C.STATUS_TEXTS[C.ST_TO_WARRANTOR].lower()
        for word in (u"wymieni", u"naprawi", u"producent"):
            self.assertNotIn(word, text)


class ReportModelTest(unittest.TestCase):
    def test_repair_example(self):
        model = build_report(form(customer=u"Objawy usterki / Nie uruchamia się."))
        self.assertEqual(model["title"], C.TITLE_REPAIR)
        headings = [model["sections"][k]["heading"] for k in C.TEXT_FIELDS]
        self.assertEqual(headings, [
            u"1. OPIS ZGŁOSZENIA KLIENTA", u"2. DIAGNOZA SERWISOWA (EKSPERTYZA)",
            u"3. ZAKRES WYKONANEJ NAPRAWY I ZASTOSOWANE CZĘŚCI",
            u"4. WYNIK TESTÓW I WERYFIKACJA KOŃCOWA"])
        self.assertEqual(model["final"]["heading"], u"5. STATUS KOŃCOWY")
        self.assertIsNone(model["sections"]["customer"]["intro"] or None)

    def test_empty_sections_skipped_and_renumbered(self):
        model = build_report(form(status=C.ST_NOT_CONFIRMED,
                                  report_type=C.RT_NOT_CONFIRMED, work=u""))
        self.assertIsNone(model["sections"]["customer"])
        self.assertIsNone(model["sections"]["work"])
        self.assertEqual(model["sections"]["diagnosis"]["heading"],
                         u"1. DIAGNOZA SERWISOWA (EKSPERTYZA)")
        self.assertEqual(model["sections"]["tests"]["number"], 2)
        self.assertEqual(model["final"]["number"], 3)
        text = report_as_text(model)
        self.assertNotIn(u"NAPRAWY", text)

    def test_not_confirmed_never_mentions_repair_automatically(self):
        model = build_report(form(status=C.ST_NOT_CONFIRMED,
                                  report_type=C.RT_REPAIR))
        self.assertEqual(model["title"], C.TITLE_DIAGNOSTICS)
        self.assertEqual(model["sections"]["work"]["heading"],
                         u"2. " + C.HEAD_WORK_DEFAULT)
        self.assertEqual(model["sections"]["work"]["intro"], C.WORK_INTRO_DEFAULT)

    def test_work_heading_by_type(self):
        self.assertIn(C.HEAD_WORK_DIAGNOSTICS, build_report(
            form(report_type=C.RT_DIAGNOSTICS))["sections"]["work"]["heading"])
        self.assertIn(C.HEAD_WORK_CLEANING, build_report(
            form(report_type=C.RT_CLEANING))["sections"]["work"]["heading"])
        self.assertIn(C.HEAD_WORK_DEFAULT, build_report(
            form(report_type=C.RT_EXPERTISE))["sections"]["work"]["heading"])

    def test_intro_variants(self):
        model = build_report(form(diagnosis_intro=1, tests_intro=1))
        self.assertEqual(model["sections"]["diagnosis"]["intro"], C.DIAGNOSIS_INTROS[1])
        self.assertEqual(model["sections"]["tests"]["intro"], C.TESTS_INTROS[1])

    def test_no_status_skips_final(self):
        model = build_report(form(status=C.ST_NONE))
        self.assertIsNone(model["final"])
        self.assertEqual(model["fields"][C.BM_DEVICE_STATUS], u"")

    def test_custom_status(self):
        model = build_report(form(status=C.ST_CUSTOM, custom_status=u"Tekst własny."))
        self.assertEqual(model["final"]["text"], u"Tekst własny.")

    def test_model_contains_only_user_text(self):
        model = build_report(form(diagnosis=u"Ładowanie / nie ładuje",
                                  status=C.ST_DIAG_DONE,
                                  report_type=C.RT_DIAGNOSTICS, work=u"", tests=u""))
        text = report_as_text(model).lower()
        self.assertIn(u"ładowanie: nie ładuje", text)
        for forbidden in (u"bateri", u"akumulator", u"płyty głównej", u"awari",
                          u"przepię", u"spowodował"):
            self.assertNotIn(forbidden, text)


class PhraseLibraryTest(unittest.TestCase):
    def setUp(self):
        self.lib = PhraseLibrary.load()

    def test_required_categories(self):
        titles = [c["title"] for c in self.lib.categories]
        for t in (u"Ogólne", u"Mechaniczne", u"Zalanie", u"Zasilanie", u"Bateria",
                  u"Wyświetlacz", u"Audio", u"AGD", u"Odkurzacze", u"Oprogramowanie",
                  u"Naprawa", u"Czyszczenie", u"Testy", u"Gwarancja", u"Ingerencja"):
            self.assertIn(t, titles)

    def test_unique_ids_and_format(self):
        ids = set()
        for _, phrase in self.lib.all_phrases():
            self.assertNotIn(phrase["id"], ids)
            ids.add(phrase["id"])
            self.assertIn(u" / ", phrase["text"], phrase["id"])

    def test_no_causal_or_future_claims(self):
        forbidden = re.compile(
            u"spowodował|w wyniku przepięcia|awari|producent wymieni|"
            u"wymieni urządzenie|naprawi urządzenie|oryginaln", re.IGNORECASE)
        for _, phrase in self.lib.all_phrases():
            self.assertIsNone(forbidden.search(phrase["text"]), phrase["text"])

    def test_device_profile_ordering(self):
        cats = self.lib.ordered_categories(u"Odkurzacz")
        self.assertEqual(cats[0]["id"], u"vacuum")
        self.assertEqual(len(cats), len(self.lib.categories))
        self.assertEqual(self.lib.ordered_categories()[0]["id"], u"general")

    def test_device_profiles_reference_existing_categories(self):
        ids = set(c["id"] for c in self.lib.categories)
        for device in C.DEVICE_TYPES:
            self.assertIn(device, self.lib.device_profiles)
            for cat_id in self.lib.device_profiles[device]:
                self.assertIn(cat_id, ids)

    def test_custom_category_first(self):
        lib = PhraseLibrary.load(custom_phrases=[
            {"id": "custom_x", "title": u"TV – test pełny", "text": u"A / b"}])
        self.assertEqual(lib.ordered_categories(u"Telewizor")[0]["id"], "custom")


if __name__ == "__main__":
    unittest.main()
