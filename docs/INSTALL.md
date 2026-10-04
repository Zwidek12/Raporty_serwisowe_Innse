# Instalacja – Raport serwisowy dla LibreOffice Writer

## Wymagania

- LibreOffice 7.0 lub nowszy (sprawdzono na LibreOffice 26.8.0.3, Windows 11).
- Python dołączony do LibreOffice (w instalatorze Windows jest domyślnie).
  Na Linuksie trzeba doinstalować pakiet `libreoffice-script-provider-python`
  (Debian/Ubuntu) lub `libreoffice-pyuno` (Fedora).
- Nie są potrzebne internet, baza danych ani zewnętrzne biblioteki.

## Instalacja na jednym komputerze (Windows)

1. Zamknij wszystkie okna LibreOffice, także ikonę szybkiego uruchamiania w zasobniku.
2. Skopiuj cały katalog projektu (wystarczy `dist\ServiceReport.oxt`, `install.bat`
   i `install.ps1`).
3. Kliknij dwukrotnie `install.bat`.
4. Uruchom Writer. Pojawi się menu **Raport serwisowy** i pasek narzędzi
   **Raport serwisowy**. Jeśli paska nie widać, włącz go:
   *Widok → Paski narzędzi → Raport serwisowy*.

Instalacja ręczna (bez skryptu): *Narzędzia → Menedżer rozszerzeń → Dodaj…* →
wskaż `dist\ServiceReport.oxt` → uruchom ponownie LibreOffice.

Instalacja z wiersza poleceń:

```
"C:\Program Files\LibreOffice\program\unopkg.com" add --suppress-license dist\ServiceReport.oxt
```

## Instalacja na wielu komputerach

- **Dla wszystkich użytkowników komputera** (jako administrator):
  `powershell -ExecutionPolicy Bypass -File install.ps1 -Shared`
- **Wdrożenie masowe** (GPO, Intune, skrypt logowania): uruchom polecenie
  `unopkg add --shared --suppress-license \\serwer\udział\ServiceReport.oxt`
  z uprawnieniami administratora, przy zamkniętym LibreOffice.
- Ustawienia i frazy własne każdego użytkownika są przechowywane w jego profilu,
  zob. niżej. Aby rozdać wspólne frazy własne, skopiuj plik
  `custom_phrases.json` do profili użytkowników lub dodaj frazy do
  `resources/phrases_default.json` i przebuduj pakiet (zob. DEVELOPMENT.md).

## Aktualizacja

Uruchom ponownie `install.bat` z nową wersją `ServiceReport.oxt` – skrypt
usuwa poprzednią wersję i instaluje nową. Ustawienia i frazy własne zostają.

## Odinstalowanie

`install.bat /u` albo *Narzędzia → Menedżer rozszerzeń → Raport serwisowy → Usuń*.

## Pliki użytkownika

Katalog `service_report` w profilu LibreOffice, na Windows zwykle:

```
%APPDATA%\LibreOffice\4\user\service_report\
    settings.json         ustawienia
    custom_phrases.json   frazy własne
    last_form.json        ostatnio wypełniony formularz
    service_report.log    dziennik zapisów i błędów
```

Domyślny katalog zapisu raportów: `Dokumenty\Raporty serwisowe`
(można zmienić w *Raport serwisowy → Ustawienia*).

## Rozwiązywanie problemów

| Objaw | Rozwiązanie |
|---|---|
| Brak menu „Raport serwisowy” | Uruchom ponownie LibreOffice; sprawdź w Menedżerze rozszerzeń, czy rozszerzenie jest włączone. Menu jest widoczne w programie Writer. |
| Komunikat o błędzie Pythona przy instalacji (Linux) | Doinstaluj obsługę skryptów Python (pakiety podane wyżej). |
| `install.bat`: „Zamknij wszystkie okna LibreOffice” | Zamknij LibreOffice, także w zasobniku systemowym. |
| Błąd przy zapisie | Szczegóły są w `service_report.log`; sprawdź uprawnienia do katalogu zapisu. |
