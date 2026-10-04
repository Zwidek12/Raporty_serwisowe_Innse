import datetime
import re

from . import constants as C
from .parser import parse_block

_DATE_RE = re.compile(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\s*$")
_ISO_DATE_RE = re.compile(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*$")
_PLACEHOLDER_RE = re.compile(r"\[[^\[\]\n]{1,40}\]")
_REPAIR_WORDS_RE = re.compile(r"napraw|wymien|wymian", re.IGNORECASE)


def parse_date(value):
    if not value:
        return None
    m = _DATE_RE.match(value)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = _ISO_DATE_RE.match(value)
        if not m:
            return None
        y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return datetime.date(y, mth, d)
    except ValueError:
        return None


def normalize_date(value):
    parsed = parse_date(value)
    if parsed is None:
        return (value or u"").strip()
    return parsed.strftime("%d.%m.%Y")


def _text(form, key):
    return (form.get(key) or u"").strip()


def validate(form):
    errors = []
    warnings = []

    if not _text(form, "ticket"):
        errors.append(u"Podaj numer zgłoszenia.")

    report_date = _text(form, "report_date")
    if not report_date:
        errors.append(u"Podaj datę sporządzenia raportu.")
    elif parse_date(report_date) is None:
        errors.append(u"Data sporządzenia ma niepoprawny format "
                      u"(oczekiwany %s)." % C.DATE_FORMAT_HINT)

    receipt_date = _text(form, "receipt_date")
    if receipt_date and parse_date(receipt_date) is None:
        errors.append(u"Data przyjęcia ma niepoprawny format "
                      u"(oczekiwany %s)." % C.DATE_FORMAT_HINT)

    if not _text(form, "manufacturer"):
        errors.append(u"Podaj producenta urządzenia.")
    if not _text(form, "model"):
        errors.append(u"Podaj model urządzenia.")

    diagnosis = parse_block(form.get("diagnosis"))
    work = parse_block(form.get("work"))
    tests = parse_block(form.get("tests"))

    if not diagnosis:
        errors.append(u"Pole „B. Diagnoza serwisowa” musi zawierać "
                      u"przynajmniej jeden wpis.")

    status = form.get("status") or C.ST_NONE
    report_type = form.get("report_type") or C.RT_OTHER

    if status == C.ST_CUSTOM and not _text(form, "custom_status"):
        errors.append(u"Wybrano status „Własny tekst”, ale nie wpisano "
                      u"treści statusu.")

    if not _text(form, "serial"):
        warnings.append(u"Nie podano numeru seryjnego urządzenia.")

    if status == C.ST_NONE:
        warnings.append(u"Nie wybrano statusu końcowego – sekcja „Status "
                        u"końcowy” zostanie pominięta.")

    if status == C.ST_REPAIRED and not work:
        warnings.append(u"Wybrano status „Naprawiony”, ale pole "
                        u"„C. Wykonane czynności” jest puste.")
    if status == C.ST_REPAIRED and not tests:
        warnings.append(u"Wybrano status „Naprawiony”, ale pole "
                        u"„D. Testy końcowe” jest puste.")

    if status == C.ST_NOT_CONFIRMED:
        if work:
            warnings.append(u"Status „Usterka niepotwierdzona”, a pole "
                            u"„C. Wykonane czynności” zawiera wpisy – "
                            u"sprawdź spójność raportu.")
        if _REPAIR_WORDS_RE.search(form.get("diagnosis") or u""):
            warnings.append(u"Status „Usterka niepotwierdzona”, a w diagnozie "
                            u"występują słowa związane z naprawą/wymianą – "
                            u"sprawdź spójność raportu.")

    if (report_type in C.REPAIR_REPORT_TYPES
            and status in C.NON_REPAIR_STATUSES):
        warnings.append(u"Rodzaj raportu „%s” nie pasuje do statusu „%s” – "
                        u"sprawdź spójność raportu." % (report_type, status))

    for key in C.TEXT_FIELDS:
        found = _PLACEHOLDER_RE.findall(form.get(key) or u"")
        if found:
            warnings.append(u"Pole „%s” zawiera niewypełnione znaczniki: %s"
                            % (C.FIELD_LABELS[key].rstrip(u" *"),
                               u", ".join(sorted(set(found)))))

    return errors, warnings


def status_change_warning(status, work_text):
    if status == C.ST_REPAIRED and not parse_block(work_text):
        return (u"Wybrano status „Naprawiony”, ale pole „C. Wykonane "
                u"czynności” jest puste.\n\nUzupełnij wykonane czynności – "
                u"bez nich raport z tym statusem będzie niespójny.")
    return None
