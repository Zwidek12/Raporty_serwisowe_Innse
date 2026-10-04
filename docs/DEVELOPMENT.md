# Dokumentacja techniczna

## Architektura

```
report_generator/          logika (pakiet Pythona)
    constants.py           WSZYSTKIE teksty wstawiane automatycznie, nazwy zakładek i stylów
    parser.py              parser „Kategoria / opis” (bez UNO)
    validators.py          walidacja i ostrzeżenia (bez UNO)
    report_model.py        model raportu: sekcje, numeracja, tytuły, statusy (bez UNO)
    storage.py             JSON (ustawienia, frazy własne), nazwy plików, wersje (bez UNO)
    phrases.py             biblioteka fraz + kolejność kategorii wg typu urządzenia (bez UNO)
    document.py            wypełnianie szablonu Writer (UNO)
    export_pdf.py          zapis ODT / eksport PDF (UNO)
    dialog.py              okna dialogowe AWT budowane programowo (UNO)
    main.py                punkty wejścia: new / export / phrases / settings / help
extension/                 pliki pakietu .oxt
    service_report_job.py  komponent UNO (XJobExecutor) wywoływany z menu
    ServiceReport.components, Addons.xcu, description.xml, META-INF/manifest.xml
resources/
    report_template.ott    szablon (generowany przez tools/build_template.py)
    phrases_default.json   biblioteka fraz domyślnych
    logo_placeholder.png   logo zastępcze (tools/make_logo_placeholder.py)
tools/                     budowanie i weryfikacja (headless)
tests/                     testy jednostkowe (unittest, bez UNO)
```

Dodatkowy moduł `report_model.py` (spoza pierwotnej listy) oddziela logikę
składania raportu od UNO, dzięki czemu reguły (pomijanie pustych sekcji,
numeracja, tytuły, statusy) są testowane jednostkowo.

### Przepływ

1. Menu lub pasek narzędzi wywołuje `service:com.innse.servicereport.Job?new`,
   co prowadzi do `ServiceReportJob.trigger("new")`, a ten do `main.dispatch`.
2. `MainDialog` zbiera dane, a `validators.validate` zwraca błędy i ostrzeżenia.
3. `report_model.build_report` buduje model (tylko dane operatora + stałe z `constants.py`).
4. `document.create_report` otwiera szablon jako nowy dokument (`AsTemplate`),
   wypełnia zakładki i pokazuje dokument. Nie zapisuje go.
5. `main.export_current` (polecenie `export`) czyta numer zgłoszenia z właściwości
   dokumentu `RaportSerwisowy_Zgloszenie`, a `export_pdf.save_and_export`
   zapisuje ODT (`storeAsURL`) i PDF (`storeToURL`, filtr `writer_pdf_Export`).

### Szablon i zakładki

Generator nie wyszukuje tekstu. Korzysta wyłącznie z zakładek (bookmarks):

| Zakładka | Zawartość |
|---|---|
| `REPORT_TITLE` | tytuł zależny od rodzaju raportu |
| `REPORT_DATE`, `TICKET_NUMBER` | dane obowiązkowe |
| `RECEIPT_DATE`, `TECHNICIAN` | opcjonalne – pusty → akapit usuwany |
| `DEVICE_MANUFACTURER`, `DEVICE_MODEL` | wiersz „Producent / Model” |
| `DEVICE_SERIAL`, `DEVICE_TYPE`, `DEVICE_STATUS` | opcjonalne punkty danych urządzenia |
| `SECTION_CUSTOMER`, `SECTION_DIAGNOSIS`, `SECTION_WORK`, `SECTION_TESTS`, `FINAL_STATUS` | akapit zastępowany nagłówkiem, wstępem i punktami (pusta sekcja → akapit usuwany) |
| `SERVICE_NAME` (nagłówek strony), `FOOTER_TICKET` (stopka) | nazwa serwisu, numer zgłoszenia |

Obraz logo w nagłówku ma nazwę obiektu `LOGO`.

Style akapitów: `RG Tytuł`, `RG Dane`, `RG Dane nagłówek`, `RG Dane punkt`,
`RG Sekcja` (zachowaj z następnym, bez dzielenia), `RG Wstęp` (zachowaj z
następnym), `RG Punkt` (lista `RG Punkty`), `RG Status`, `RG Treść`.
Ochrona przed sierotami i wdowami: 2 wiersze. Paginację obsługuje sam Writer.

Wygląd szablonu zmienisz na dwa sposoby:
- edytując `tools/build_template.py` i uruchamiając go ponownie (zalecane),
- albo otwierając `resources/report_template.ott` w programie Writer i zapisując
  go jako szablon. **Nie usuwaj zakładek**: *Wstaw → Zakładka* pokazuje ich listę.

### Biblioteka fraz

`resources/phrases_default.json`:

```json
{
  "categories": [
    {"id": "power", "title": "Zasilanie", "phrases": [
      {"id": "power_ok", "title": "Zasilanie prawidłowe",
       "text": "Zasilanie / Urządzenie prawidłowo reaguje na podłączenie zasilania."}
    ]}
  ],
  "device_profiles": {"Telewizor": ["display", "power", "audio"]}
}
```

Kategorie są listą, żeby zachować kolejność. `device_profiles` określa, które
kategorie trafiają na górę listy po wybraniu typu urządzenia. Test
`test_no_causal_or_future_claims` pilnuje, żeby frazy domyślne nie zawierały
sformułowań przyczynowych ani zapowiedzi działań gwaranta.

## Budowanie

Skrypty korzystające z UNO uruchamiaj Pythonem LibreOffice:

```
set LOPY="C:\Program Files\LibreOffice\program\python.exe"
%LOPY% tools\make_logo_placeholder.py     # logo zastępcze
%LOPY% tools\build_template.py            # resources\report_template.ott (headless)
%LOPY% -m unittest discover -s tests      # testy jednostkowe
%LOPY% tools\verify_generation.py         # generuje przykładowe raporty ODT+PDF do out\
%LOPY% tools\smoke_dialogs.py             # tworzy wszystkie okna i symuluje formularz
%LOPY% tools\build_oxt.py                 # dist\ServiceReport.oxt
```

Testy jednostkowe działają też zwykłym Pythonem 3 (`python -m unittest discover -s tests`).

## Co zostało przetestowane, a co nie

Automatycznie, w LibreOffice 26.8 headless na Windows 11:
- parser, walidacja, nazwy plików, wersjonowanie, mapa statusów, model raportu
  i biblioteka fraz (64 testy jednostkowe),
- generowanie raportów z przykładów 43–46 i długiego, 4-stronicowego raportu,
  zapis ODT i eksport PDF, pogrubienie wyłącznie etykiet, brak pustych
  nagłówków, polskie znaki w PDF,
- tworzenie wszystkich okien dialogowych i symulacja pracy z formularzem
  (wybór typu urządzenia, wstawianie fraz, frazy własne, status własny,
  odtworzenie formularza),
- instalacja pakietu `.oxt` przez `unopkg` i rejestracja komponentu UNO.

Wymaga sprawdzenia ręcznego w interfejsie graficznym:
- interakcje myszą (dwuklik na frazie, przełączanie pola docelowego po kliknięciu
  w pole tekstowe),
- okna wyboru plików i folderów w Ustawieniach,
- pasek informacyjny nad wygenerowanym dokumentem,
- otwieranie folderu po eksporcie.

## Uruchamianie bez instalacji rozszerzenia (dla programisty)

Moduł `main.py` eksportuje makra `NowyRaport` i `ZapiszIEksportujPDF`
(`g_exportedScripts`). Aby ich użyć, skopiuj `report_generator` do katalogu
`%APPDATA%\LibreOffice\4\user\Scripts\python\pythonpath\` i utwórz w
`Scripts\python` plik, który importuje te funkcje. Do normalnego użytku
zalecany jest pakiet `.oxt`.
