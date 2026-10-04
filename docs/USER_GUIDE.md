# Instrukcja użytkownika – Raport serwisowy

## Zasada najważniejsza

Program **niczego nie diagnozuje i nie dopisuje faktów**. W raporcie pojawia się
wyłącznie:

- to, co wpiszesz,
- frazy, które **świadomie wybierzesz** z biblioteki,
- stałe zdania wstępne i tekst statusu zależne od wybranego rodzaju raportu i statusu.

Związek przyczynowo-skutkowy (np. „zalanie spowodowało uszkodzenie”) może się
pojawić tylko wtedy, gdy wpiszesz go ręcznie na podstawie raportu technika.

## Krok po kroku

1. Otwórz Writer i kliknij **Utwórz raport serwisowy** na pasku narzędzi
   (lub menu *Raport serwisowy → Nowy raport…*).
2. Jeśli poprzednio wypełniano formularz, program zapyta, czy wczytać tamte dane.
   To przydaje się, gdy chcesz poprawić i wygenerować raport jeszcze raz.
3. Wypełnij dane podstawowe. Pola z gwiazdką (*) są wymagane.
4. Wybierz **Rodzaj raportu**, bo od niego zależy tytuł i nazwa sekcji 3:

   | Rodzaj raportu | Tytuł | Sekcja 3 |
   |---|---|---|
   | Naprawa, Naprawa gwarancyjna | RAPORT Z NAPRAWY SERWISOWEJ | ZAKRES WYKONANEJ NAPRAWY I ZASTOSOWANE CZĘŚCI |
   | Diagnostyka | RAPORT Z DIAGNOSTYKI SERWISOWEJ | WYKONANE CZYNNOŚCI DIAGNOSTYCZNE |
   | Brak potwierdzenia usterki, Naturalne zużycie, Przekazanie do gwaranta, Brak naprawy | RAPORT Z DIAGNOSTYKI SERWISOWEJ | ZAKRES WYKONANYCH CZYNNOŚCI SERWISOWYCH |
   | Ekspertyza | RAPORT Z EKSPERTYZY SERWISOWEJ | ZAKRES WYKONANYCH CZYNNOŚCI SERWISOWYCH |
   | Czyszczenie / konserwacja | RAPORT Z OBSŁUGI SERWISOWEJ | WYKONANE CZYNNOŚCI KONSERWACYJNE |
   | Inny | RAPORT Z OBSŁUGI SERWISOWEJ | ZAKRES WYKONANYCH CZYNNOŚCI SERWISOWYCH |

   Przy statusie „Usterka niepotwierdzona” tytuł i sekcja 3 nigdy nie mówią o naprawie.

5. Wybierz **Status końcowy**. W polu pod listą zobaczysz dokładny tekst, który
   trafi do raportu. Opcja „Własny tekst” pozwala wpisać dowolną treść.
6. Wypełnij pola A–D. **Każda linia to jeden punkt raportu**, w formacie:

   ```
   Kategoria / opis
   ```

   Przykład: `Test USB / Sprawdzono ładowanie/komunikację z komputerem.`
   W raporcie: • **Test USB:** Sprawdzono ładowanie/komunikację z komputerem.

   - Linia jest dzielona tylko po **pierwszym** znaku „/”, więc dalsze „/” zostają w opisie.
   - Linia bez „/” staje się zwykłym punktem bez pogrubienia.
   - Puste linie są pomijane.
   - Puste pole oznacza, że sekcja w ogóle nie pojawi się w raporcie, a numeracja pozostałych sekcji jest ciągła.

7. **Gotowe sformułowania** (panel po prawej):
   - wybierz kategorię (kategorie pasujące do *Typu urządzenia* są na górze),
   - zaznacz frazę i sprawdź jej treść,
   - kliknij **Wstaw frazę do pola** (albo kliknij frazę dwukrotnie).
     Fraza zostanie dopisana jako nowa linia w polu, w którym ostatnio pisałeś
     (lub w polu wskazanym na liście „Wstaw do pola”),
   - wstawioną frazę możesz dowolnie edytować.
   - Frazy ze znacznikami w nawiasach, np. `[nazwa]`, `[numer]`, trzeba uzupełnić.
     Program ostrzeże, jeśli zostaną niewypełnione.
8. Kliknij **Generuj raport**. Program sprawdzi dane:
   - **błędy** (brak numeru, daty, producenta, modelu lub diagnozy) blokują generowanie,
   - **ostrzeżenia** (np. status „Naprawiony” bez wykonanych czynności, brak numeru
     seryjnego) wymagają potwierdzenia.
9. Otworzy się gotowy dokument Writer, który **nie jest jeszcze zapisany**. Przejrzyj go
   i popraw ręcznie, jeśli trzeba.
10. Kliknij **Zapisz i eksportuj PDF** (pasek informacyjny nad dokumentem, pasek
    narzędzi albo menu). Powstaną pliki `Raport_<numer>.odt` i `Raport_<numer>.pdf`.
    Jeśli pliki już istnieją, wybierz **Nadpisz** albo **Zapisz jako nową wersję**
    (`Raport_<numer>_v2.pdf`, `_v3` …).

Po zapisie dokument jest powiązany z plikiem ODT. Kolejne poprawki zapisujesz
zwykłym Ctrl+S, a PDF odświeżasz ponownym kliknięciem „Zapisz i eksportuj PDF”.

## Papier firmowy

Raport może być tworzony bezpośrednio na papierze firmowym.

1. Przygotuj papier firmowy jako plik Writer lub Word: `.ott`, `.odt`, `.docx`, `.doc`, `.dotx` lub `.rtf`.
   Logo, adres, NIP itp. powinny być w **nagłówku i stopce** albo jako grafiki. Treść strony zostaw pustą.
2. Wskaż plik przy pierwszym raporcie (program o to zapyta) albo w *Raport serwisowy → Ustawienia → Papier firmowy*.
3. Program kopiuje plik do profilu użytkownika, więc późniejsze przeniesienie lub usunięcie oryginału nie psuje raportów.
   Po zmianie papieru wskaż nowy plik w Ustawieniach. Przycisk **Usuń** wyłącza papier.

Jak to działa:
- nagłówek, stopka, logo, grafiki, marginesy i rozmiar strony pochodzą z papieru i nie są zmieniane,
- treść raportu (tytuł, dane, sekcje) jest wstawiana w miejsce pustej treści papieru,
- raport przejmuje krój czcionki z papieru, a układ (rozmiary, odstępy, punktory) jest zawsze taki sam,
- przy długim raporcie papier jest na każdej stronie, tak jak w zwykłym dokumencie,
- jeśli w treści papieru jest jakiś tekst, raport zostanie dopisany pod nim.

Bez papieru firmowego raport powstaje na czystej stronie A4 ze stopką z numerem zgłoszenia i numeracją stron.

## Własne frazy

- W formularzu: zaznacz frazę albo wpisz linię w polu i kliknij
  **Zapisz jako własną frazę…**, a następnie podaj nazwę, np. „TV – test pełny”.
- Menu *Raport serwisowy → Biblioteka fraz…* pozwala przeglądać wszystkie frazy
  oraz dodawać i usuwać frazy własne.
- Frazy własne są zapisane lokalnie w pliku `custom_phrases.json` w profilu
  użytkownika i pojawiają się jako pierwsza kategoria „★ Własne frazy”.

## Ustawienia

*Raport serwisowy → Ustawienia…*:

- domyślny katalog zapisu,
- papier firmowy (zob. niżej),
- domyślny technik i domyślny rodzaj raportu,
- otwieranie folderu po eksporcie,
- zapis ODT i/lub generowanie PDF.

## Przykładowe sformułowania statusu

| Status | Tekst w raporcie |
|---|---|
| Naprawiony | Urządzenie zostało przywrócone do prawidłowej sprawności technicznej i funkcjonalnej. Sprzęt jest gotowy do dalszego użytkowania. |
| Sprawny bez naprawy | W toku przeprowadzonych oględzin i testów urządzenie działało prawidłowo. Nie stwierdzono nieprawidłowości wpływających na jego podstawowe funkcjonowanie. |
| Sprawny po czyszczeniu | Po wykonaniu opisanych czynności czyszczących urządzenie działa prawidłowo i jest gotowe do dalszego użytkowania. |
| Usterka niepotwierdzona | W toku przeprowadzonych oględzin i testów nie potwierdzono występowania zgłaszanej nieprawidłowości. |
| Usterka potwierdzona – bez naprawy | Diagnostyka potwierdziła występowanie opisanej nieprawidłowości. W ramach niniejszej obsługi nie wykonano naprawy urządzenia. |
| Naturalne zużycie | Diagnostyka wykazała zużycie eksploatacyjne wskazanego elementu. |
| Oczekuje na części | Diagnostyka została zakończona. Dalsze czynności serwisowe wymagają dostępności właściwych części. |
| Przekazano do gwaranta | Urządzenie zostało skierowane do dalszej obsługi w ramach właściwej procedury gwarancyjnej. |
| Nienaprawiony | Urządzenie nie zostało przywrócone do pełnej sprawności w ramach przeprowadzonych czynności serwisowych. |
| Diagnostyka zakończona | Proces diagnostyczny został zakończony. Wyniki przeprowadzonych oględzin i testów przedstawiono w niniejszym raporcie. |
