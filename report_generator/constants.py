import os

EXTENSION_ID = "com.innse.servicereport"
APP_NAME = "Raport serwisowy"

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_root():
    candidates = [
        os.path.dirname(_PKG_DIR),
        os.path.dirname(os.path.dirname(_PKG_DIR)),
    ]
    for cand in candidates:
        if os.path.isdir(os.path.join(cand, "resources")):
            return cand
    return candidates[0]


ROOT_DIR = _find_root()
RESOURCES_DIR = os.path.join(ROOT_DIR, "resources")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
TEMPLATE_FILE = os.path.join(RESOURCES_DIR, "report_template.ott")
PHRASES_DEFAULT_FILE = os.path.join(RESOURCES_DIR, "phrases_default.json")

USER_DIR_NAME = "service_report"
SETTINGS_FILE_NAME = "settings.json"
CUSTOM_PHRASES_FILE_NAME = "custom_phrases.json"
LOG_FILE_NAME = "service_report.log"
LETTERHEAD_BASENAME = "papier_firmowy"
LETTERHEAD_EXTENSIONS = (".ott", ".odt", ".dotx", ".docx", ".dot", ".doc", ".rtf")

RT_REPAIR = "Naprawa"
RT_DIAGNOSTICS = "Diagnostyka"
RT_EXPERTISE = "Ekspertyza"
RT_NOT_CONFIRMED = "Brak potwierdzenia usterki"
RT_CLEANING = "Czyszczenie / konserwacja"
RT_WEAR = "Naturalne zużycie"
RT_WARRANTY_REPAIR = "Naprawa gwarancyjna"
RT_TO_WARRANTOR = "Przekazanie do gwaranta"
RT_NO_REPAIR = "Brak naprawy"
RT_OTHER = "Inny"

REPORT_TYPES = [
    RT_REPAIR, RT_DIAGNOSTICS, RT_EXPERTISE, RT_NOT_CONFIRMED, RT_CLEANING,
    RT_WEAR, RT_WARRANTY_REPAIR, RT_TO_WARRANTOR, RT_NO_REPAIR, RT_OTHER,
]
REPAIR_REPORT_TYPES = (RT_REPAIR, RT_WARRANTY_REPAIR)

TITLE_REPAIR = "RAPORT Z NAPRAWY SERWISOWEJ"
TITLE_DIAGNOSTICS = "RAPORT Z DIAGNOSTYKI SERWISOWEJ"
TITLE_EXPERTISE = "RAPORT Z EKSPERTYZY SERWISOWEJ"
TITLE_SERVICE = "RAPORT Z OBSŁUGI SERWISOWEJ"

REPORT_TITLES = {
    RT_REPAIR: TITLE_REPAIR,
    RT_WARRANTY_REPAIR: TITLE_REPAIR,
    RT_DIAGNOSTICS: TITLE_DIAGNOSTICS,
    RT_NOT_CONFIRMED: TITLE_DIAGNOSTICS,
    RT_WEAR: TITLE_DIAGNOSTICS,
    RT_TO_WARRANTOR: TITLE_DIAGNOSTICS,
    RT_NO_REPAIR: TITLE_DIAGNOSTICS,
    RT_EXPERTISE: TITLE_EXPERTISE,
    RT_CLEANING: TITLE_SERVICE,
    RT_OTHER: TITLE_SERVICE,
}

HEAD_CUSTOMER = "OPIS ZGŁOSZENIA KLIENTA"
HEAD_DIAGNOSIS = "DIAGNOZA SERWISOWA (EKSPERTYZA)"
HEAD_WORK_DEFAULT = "ZAKRES WYKONANYCH CZYNNOŚCI SERWISOWYCH"
HEAD_WORK_REPAIR = "ZAKRES WYKONANEJ NAPRAWY I ZASTOSOWANE CZĘŚCI"
HEAD_WORK_DIAGNOSTICS = "WYKONANE CZYNNOŚCI DIAGNOSTYCZNE"
HEAD_WORK_CLEANING = "WYKONANE CZYNNOŚCI KONSERWACYJNE"
HEAD_TESTS = "WYNIK TESTÓW I WERYFIKACJA KOŃCOWA"
HEAD_FINAL = "STATUS KOŃCOWY"

WORK_HEADINGS = {
    RT_REPAIR: HEAD_WORK_REPAIR,
    RT_WARRANTY_REPAIR: HEAD_WORK_REPAIR,
    RT_DIAGNOSTICS: HEAD_WORK_DIAGNOSTICS,
    RT_CLEANING: HEAD_WORK_CLEANING,
}

DIAGNOSIS_INTROS = [
    "Diagnostyka przeprowadzona przez Centrum Serwisowe wykazała następujący "
    "stan urządzenia:",
    "W wyniku przeprowadzonych oględzin oraz testów funkcjonalnych ustalono "
    "następujący stan techniczny urządzenia:",
]

WORK_INTRO_REPAIR = (
    "W ramach procesu serwisowego wykonano następujące czynności oraz, jeżeli "
    "było to konieczne, wymieniono wskazane podzespoły:")
WORK_INTRO_DIAGNOSTICS = (
    "W ramach przeprowadzonej diagnostyki wykonano następujące czynności "
    "kontrolne i weryfikacyjne:")
WORK_INTRO_CLEANING = (
    "W toku obsługi serwisowej wykonano następujące czynności konserwacyjne "
    "i czyszczące:")
WORK_INTRO_DEFAULT = (
    "W ramach obsługi serwisowej wykonano następujące czynności:")

WORK_INTROS = {
    RT_REPAIR: WORK_INTRO_REPAIR,
    RT_WARRANTY_REPAIR: WORK_INTRO_REPAIR,
    RT_DIAGNOSTICS: WORK_INTRO_DIAGNOSTICS,
    RT_CLEANING: WORK_INTRO_CLEANING,
}

TESTS_INTROS = [
    "Po zakończeniu czynności serwisowych urządzenie poddano testom "
    "funkcjonalnym:",
    "Po wykonaniu wskazanych czynności przeprowadzono końcową weryfikację "
    "działania urządzenia:",
]

INTRO_VARIANT_LABELS = ["Wariant 1", "Wariant 2"]

ST_NONE = "— nie wybrano —"
ST_REPAIRED = "Naprawiony"
ST_OK_NO_REPAIR = "Sprawny bez naprawy"
ST_OK_AFTER_CLEANING = "Sprawny po czyszczeniu"
ST_NOT_CONFIRMED = "Usterka niepotwierdzona"
ST_CONFIRMED_NO_REPAIR = "Usterka potwierdzona – bez naprawy"
ST_WEAR = "Naturalne zużycie"
ST_WAITING_PARTS = "Oczekuje na części"
ST_TO_WARRANTOR = "Przekazano do gwaranta"
ST_NOT_REPAIRED = "Nienaprawiony"
ST_DIAG_DONE = "Diagnostyka zakończona"
ST_CUSTOM = "Własny tekst"

STATUSES = [
    ST_NONE, ST_REPAIRED, ST_OK_NO_REPAIR, ST_OK_AFTER_CLEANING,
    ST_NOT_CONFIRMED, ST_CONFIRMED_NO_REPAIR, ST_WEAR, ST_WAITING_PARTS,
    ST_TO_WARRANTOR, ST_NOT_REPAIRED, ST_DIAG_DONE, ST_CUSTOM,
]

STATUS_TEXTS = {
    ST_REPAIRED:
        "Urządzenie zostało przywrócone do prawidłowej sprawności technicznej "
        "i funkcjonalnej. Sprzęt jest gotowy do dalszego użytkowania.",
    ST_OK_NO_REPAIR:
        "W toku przeprowadzonych oględzin i testów urządzenie działało "
        "prawidłowo. Nie stwierdzono nieprawidłowości wpływających na jego "
        "podstawowe funkcjonowanie.",
    ST_OK_AFTER_CLEANING:
        "Po wykonaniu opisanych czynności czyszczących urządzenie działa "
        "prawidłowo i jest gotowe do dalszego użytkowania.",
    ST_NOT_CONFIRMED:
        "W toku przeprowadzonych oględzin i testów nie potwierdzono "
        "występowania zgłaszanej nieprawidłowości.",
    ST_CONFIRMED_NO_REPAIR:
        "Diagnostyka potwierdziła występowanie opisanej nieprawidłowości. "
        "W ramach niniejszej obsługi nie wykonano naprawy urządzenia.",
    ST_WEAR:
        "Diagnostyka wykazała zużycie eksploatacyjne wskazanego elementu.",
    ST_WAITING_PARTS:
        "Diagnostyka została zakończona. Dalsze czynności serwisowe wymagają "
        "dostępności właściwych części.",
    ST_TO_WARRANTOR:
        "Urządzenie zostało skierowane do dalszej obsługi w ramach właściwej "
        "procedury gwarancyjnej.",
    ST_NOT_REPAIRED:
        "Urządzenie nie zostało przywrócone do pełnej sprawności w ramach "
        "przeprowadzonych czynności serwisowych.",
    ST_DIAG_DONE:
        "Proces diagnostyczny został zakończony. Wyniki przeprowadzonych "
        "oględzin i testów przedstawiono w niniejszym raporcie.",
}

NON_REPAIR_STATUSES = (
    ST_OK_NO_REPAIR, ST_NOT_CONFIRMED, ST_CONFIRMED_NO_REPAIR, ST_NOT_REPAIRED,
)

DEVICE_TYPES = [
    "Telewizor", "Telefon", "Laptop", "Odkurzacz", "AGD", "Ekspres do kawy",
    "Smartwatch", "Konsola", "Inne",
]

FIELD_CUSTOMER = "customer"
FIELD_DIAGNOSIS = "diagnosis"
FIELD_WORK = "work"
FIELD_TESTS = "tests"

FIELD_LABELS = {
    FIELD_CUSTOMER: "A. Opis zgłoszenia klienta",
    FIELD_DIAGNOSIS: "B. Diagnoza serwisowa *",
    FIELD_WORK: "C. Wykonane czynności",
    FIELD_TESTS: "D. Testy końcowe",
}
TEXT_FIELDS = [FIELD_CUSTOMER, FIELD_DIAGNOSIS, FIELD_WORK, FIELD_TESTS]

BM_REPORT_TITLE = "REPORT_TITLE"
BM_REPORT_DATE = "REPORT_DATE"
BM_TICKET_NUMBER = "TICKET_NUMBER"
BM_RECEIPT_DATE = "RECEIPT_DATE"
BM_TECHNICIAN = "TECHNICIAN"
BM_DEVICE_MANUFACTURER = "DEVICE_MANUFACTURER"
BM_DEVICE_MODEL = "DEVICE_MODEL"
BM_DEVICE_SERIAL = "DEVICE_SERIAL"
BM_DEVICE_TYPE = "DEVICE_TYPE"
BM_DEVICE_STATUS = "DEVICE_STATUS"
BM_SECTION_CUSTOMER = "SECTION_CUSTOMER"
BM_SECTION_DIAGNOSIS = "SECTION_DIAGNOSIS"
BM_SECTION_WORK = "SECTION_WORK"
BM_SECTION_TESTS = "SECTION_TESTS"
BM_FINAL_STATUS = "FINAL_STATUS"
BM_FOOTER_TICKET = "FOOTER_TICKET"
BM_REPORT_END = "REPORT_END"

SECTION_BOOKMARKS = {
    FIELD_CUSTOMER: BM_SECTION_CUSTOMER,
    FIELD_DIAGNOSIS: BM_SECTION_DIAGNOSIS,
    FIELD_WORK: BM_SECTION_WORK,
    FIELD_TESTS: BM_SECTION_TESTS,
    "final": BM_FINAL_STATUS,
}

STYLE_TITLE = "RG Tytuł"
STYLE_META = "RG Dane"
STYLE_META_HEAD = "RG Dane nagłówek"
STYLE_DEVICE_ITEM = "RG Dane punkt"
STYLE_SECTION = "RG Sekcja"
STYLE_INTRO = "RG Wstęp"
STYLE_ITEM = "RG Punkt"
STYLE_STATUS = "RG Status"
STYLE_BODY = "RG Treść"
LIST_STYLE = "RG Punkty"

DOCPROP_TICKET = "RaportSerwisowy_Zgloszenie"
DOCPROP_MARKER = "RaportSerwisowy"

DEFAULT_SETTINGS = {
    "output_dir": "",
    "letterhead_path": "",
    "letterhead_asked": False,
    "default_technician": "",
    "default_report_type": RT_REPAIR,
    "open_folder_after_export": True,
    "save_odt": True,
    "export_pdf": True,
}

DEFAULT_OUTPUT_SUBDIR = "Raporty serwisowe"
DATE_FORMAT_HINT = "DD.MM.RRRR"
