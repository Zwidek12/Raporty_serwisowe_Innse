import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.lo_session import Session
from tools.make_test_letterhead import build as build_letterhead
from report_generator import constants as C
from report_generator import document, export_pdf, report_model
from report_generator.validators import validate
from com.sun.star.awt.FontWeight import BOLD

BASE = {
    "report_date": "04.10.2026", "receipt_date": "28.09.2026",
    "technician": "", "serial": "", "device_type_text": "",
    "customer": "", "diagnosis": "", "work": "", "tests": "",
    "custom_status": "", "diagnosis_intro": 0, "tests_intro": 0,
}

EXAMPLES = {
    "naprawa": dict(
        ticket="SRV/2026/001234", manufacturer="SONY", model="KE85XH9096",
        serial="S01-1234567-A", device_type_text='TV LED 4K 85"',
        technician="Jan Kowalski",
        report_type=C.RT_REPAIR, status=C.ST_REPAIRED,
        customer=(
            "Objawy usterki / Telewizor całkowicie się nie uruchamia, brak reakcji na pilota oraz przyciski lokalne.\n"
            "Stan i eksploatacja / Kabel zasilający podłączony prawidłowo i nieuszkodzony.\n"
            "Okoliczności towarzyszące / W miejscu użytkowania występowała burza z wyładowaniami atmosferycznymi."),
        diagnosis=(
            "Blok zasilacza PSU / Stwierdzono uszkodzenie płyty zasilającej.\n"
            "Podświetlenie panelu LCD / Stwierdzono nieprawidłowe działanie zespołu podświetlenia LED."),
        work=(
            "Blok zasilacza PSU / Wymieniono płytę zasilającą.\n"
            "Podświetlenie LED / Wymieniono zespół listew podświetlenia."),
        tests=(
            "Test zasilania i sterowania / Telewizor włącza się prawidłowo i reaguje na komendy.\n"
            "Test obrazu i dźwięku / Obraz wyświetlany jest prawidłowo, a dźwięk działa bez zakłóceń."),
    ),
    "niepotwierdzona": dict(
        ticket="123457", manufacturer="Samsung", model="Galaxy S23",
        report_type=C.RT_NOT_CONFIRMED, status=C.ST_NOT_CONFIRMED,
        diagnosis=(
            "Stan techniczny / W trakcie przeprowadzonych oględzin i testów urządzenie działało prawidłowo.\n"
            "Weryfikacja zgłoszenia / Zgłaszana nieprawidłowość nie wystąpiła podczas przeprowadzonych testów."),
        tests="Test funkcjonalny / Podstawowe funkcje urządzenia działają prawidłowo.",
    ),
    "zabrudzenie": dict(
        ticket="123458", manufacturer="Apple", model="iPhone 13", serial="F2LXK0ABC",
        report_type=C.RT_CLEANING, status=C.ST_OK_AFTER_CLEANING,
        diagnosis=(
            "Gniazdo ładowania / Stwierdzono silne zanieczyszczenie portu USB.\n"
            "Mikrofon / Stwierdzono zabrudzenie obszaru mikrofonu."),
        work=(
            "Gniazdo ładowania / Przeprowadzono czyszczenie portu USB.\n"
            "Mikrofon / Oczyszczono element z nagromadzonych zanieczyszczeń."),
        tests=(
            "Ładowanie / Po wykonanym czyszczeniu proces ładowania przebiega prawidłowo.\n"
            "Mikrofon / Po wykonanym czyszczeniu mikrofon działa prawidłowo."),
    ),
    "zuzycie": dict(
        ticket="123459", manufacturer="iRobot", model="Roomba i7", serial="R7-0001",
        report_type=C.RT_WEAR, status=C.ST_WEAR,
        diagnosis=(
            "Akumulator / Pomiary pojemności wskazują na zużycie eksploatacyjne akumulatora.\n"
            "Szczotka główna / Stwierdzono zużycie eksploatacyjne szczotki czyszczącej.\n"
            "Szczotka boczna / Stwierdzono zużycie eksploatacyjne szczotki bocznej."),
    ),
    "dlugi": dict(
        ticket="LONG-1", manufacturer="LG", model="OLED65C3", serial="LG-65-XYZ",
        report_type=C.RT_EXPERTISE, status=C.ST_CUSTOM,
        custom_status="Ekspertyza zakończona. Wyniki przedstawiono w raporcie.",
        diagnosis="\n".join(
            "Punkt kontrolny %d / Sprawdzono parametry/napięcia w punkcie %d; "
            "wynik zapisano w karcie pomiarów. Zażółć gęślą jaźń – test polskich "
            "znaków ĄĆĘŁŃÓŚŹŻ." % (i, i) for i in range(1, 70)),
        tests="Test funkcjonalny / Podstawowe funkcje urządzenia działają prawidłowo.",
    ),
}


def doc_text(doc):
    paras = []
    enum = doc.getText().createEnumeration()
    while enum.hasMoreElements():
        p = enum.nextElement()
        if p.supportsService("com.sun.star.text.Paragraph"):
            paras.append((p.ParaStyleName, p.getString(), p))
    return paras


def paras_weight(value, paras):
    for _, t, p in paras:
        if t == value:
            return p.CharWeight
    return None


def check(name, doc, model):
    problems = []
    paras = doc_text(doc)
    texts = [t for _, t, _ in paras]
    full = u"\n".join(texts)
    if u"\u00ab" in full or u"\u00bb" in full:
        problems.append("pozostały znaczniki «…»")
    for style, t, _ in paras:
        if style == C.STYLE_SECTION and not t.strip():
            problems.append("pusty nagłówek sekcji")
        if style == C.STYLE_SECTION and paras_weight(t, paras) != BOLD:
            problems.append("nagłówek bez pogrubienia: " + t)
    expected = [s["heading"] for s in model["sections"].values() if s]
    if model["final"]:
        expected.append(model["final"]["heading"])
    for heading in expected:
        if heading not in texts:
            problems.append("brak nagłówka: " + heading)
    for style, t, p in paras:
        if style != C.STYLE_ITEM or u": " not in t:
            continue
        portions = []
        enum = p.createEnumeration()
        while enum.hasMoreElements():
            portion = enum.nextElement()
            if portion.getString():
                portions.append(portion)
        label = t.split(u": ", 1)[0] + u":"
        if (portions[0].getString() != label
                or portions[0].CharWeight != BOLD):
            problems.append("niepoprawne pogrubienie w: " + t[:40])
            break
        if len(portions) > 1 and portions[1].CharWeight == BOLD:
            problems.append("opis pogrubiony w: " + t[:40])
            break
    if u"awari" in full.lower() and name != "naprawa":
        problems.append("tekst zawiera słowo 'awaria'")
    return problems, full


def check_letterhead(doc):
    problems = []
    page = doc.getStyleFamilies().getByName("PageStyles").getByName(
        doc.getText().createTextCursor().PageStyleName)
    header = page.HeaderText.getString() if page.HeaderIsOn else u""
    footer = page.FooterText.getString() if page.FooterIsOn else u""
    if u"PRZYKŁADOWA FIRMA SERWISOWA" not in header:
        problems.append("brak nagłówka papieru firmowego")
    if u"NIP 000-000-00-00" not in footer:
        problems.append("brak stopki papieru firmowego")
    if doc.getDrawPage().getCount() < 2:
        problems.append("zniknęła grafika papieru (pasek boczny lub znak)")
    first = None
    enum = doc.getText().createEnumeration()
    while enum.hasMoreElements():
        first = enum.nextElement()
        if first.getString().strip():
            break
    if first.ParaStyleName != C.STYLE_TITLE:
        problems.append("raport nie zaczyna się od tytułu (styl: %s)"
                        % first.ParaStyleName)
    last = None
    enum = doc.getText().createEnumeration()
    while enum.hasMoreElements():
        last = enum.nextElement()
    if not last.getString().strip():
        problems.append("puste akapity na końcu dokumentu")
    return problems


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    failures = 0
    with Session() as session:
        letterheads = build_letterhead(session.ctx, session.desktop, out_dir)
        variants = [("czysty", u"")] + [
            ("papier" + os.path.splitext(p)[1].replace(".", "_"), p)
            for p in letterheads]
        for variant, letterhead in variants:
            settings = dict(C.DEFAULT_SETTINGS)
            settings["letterhead_path"] = letterhead
            for name, data in EXAMPLES.items():
                form = dict(BASE)
                form.update(data)
                errors, warnings = validate(form)
                model = report_model.build_report(form)
                doc = document.create_report(session.ctx, model, settings,
                                             hidden=True)
                try:
                    problems, full = check(name, doc, model)
                    pages = doc.getCurrentController().getPropertyValue(
                        "PageCount")
                    if letterhead:
                        problems += check_letterhead(doc)
                    paths = export_pdf.save_and_export(
                        doc, out_dir,
                        "%s_%s_%s" % (model["ticket"], name, variant),
                        settings, lambda existing: export_pdf.OVERWRITE)
                finally:
                    doc.close(True)
                status = "OK" if not problems and not errors else "BŁĄD"
                failures += status != "OK"
                print("%-12s %-16s %-5s stron=%s  %s" % (
                    variant, name, status, pages,
                    os.path.basename(paths.get("pdf", u""))))
                for e in errors:
                    print("  błąd walidacji:", e)
                for p in problems:
                    print("  PROBLEM:", p)
    print("=" * 70)
    print("Wynik: %s" % ("WSZYSTKO OK" if not failures else "%d błędów" % failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
