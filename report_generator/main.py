import datetime
import io
import os
import traceback

import uno

from . import constants as C
from . import storage
from .dialog import (ConflictDialog, InputDialog, MainDialog,
                     PhraseLibraryDialog, SettingsDialog, ask_yes_no,
                     message_box)
from .document import create_report
from .export_pdf import report_ticket, save_and_export
from .report_model import build_report

JOB_URL = "service:com.innse.servicereport.Job?"
DRAFT_FILE_NAME = "last_form.json"


def user_data_dir(ctx):
    try:
        subst = ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.util.PathSubstitution", ctx)
        base = uno.fileUrlToSystemPath(subst.substituteVariables("$(user)", True))
    except Exception:
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                            "LibreOffice")
    path = os.path.join(base, C.USER_DIR_NAME)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def _desktop(ctx):
    return ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", ctx)


def _parent_window(ctx):
    try:
        frame = _desktop(ctx).getCurrentFrame()
        if frame is not None:
            return frame.getContainerWindow()
    except Exception:
        pass
    return None


def _log(ctx, text):
    try:
        path = os.path.join(user_data_dir(ctx), C.LOG_FILE_NAME)
        with io.open(path, "a", encoding="utf-8") as fh:
            fh.write(u"[%s] %s\n" % (datetime.datetime.now().isoformat(), text))
    except Exception:
        pass


def new_report(ctx):
    user_dir = user_data_dir(ctx)
    settings = storage.load_settings(user_dir)
    parent = _parent_window(ctx)
    draft_path = os.path.join(user_dir, DRAFT_FILE_NAME)
    draft = storage.read_json(draft_path, None)
    if draft and not ask_yes_no(
            ctx, parent,
            u"Wczytać dane z poprzednio wypełnionego formularza "
            u"(zgłoszenie: %s)?" % (draft.get("ticket") or u"—")):
        draft = None

    dlg = MainDialog(ctx, parent, settings, user_dir, draft)
    try:
        form = dlg.run()
    finally:
        dlg.dispose()
    if not form:
        return None

    storage.write_json(draft_path, form)
    model = build_report(form)
    doc = create_report(ctx, model, settings)
    _show_infobar(doc)
    return doc


def _show_infobar(doc):
    try:
        controller = doc.getCurrentController()
        pair = uno.createUnoStruct("com.sun.star.beans.StringPair")
        pair.First = u"Zapisz i eksportuj PDF"
        pair.Second = JOB_URL + "export"
        controller.appendInfobar(
            "service_report_info",
            u"Raport wygenerowany – nie został jeszcze zapisany.",
            u"Sprawdź dokument i w razie potrzeby popraw go ręcznie, "
            u"a następnie kliknij „Zapisz i eksportuj PDF”.",
            uno.getConstantByName("com.sun.star.frame.InfobarType.INFO"),
            (pair,), True)
    except Exception:
        pass


def export_current(ctx):
    user_dir = user_data_dir(ctx)
    settings = storage.load_settings(user_dir)
    parent = _parent_window(ctx)
    doc = _desktop(ctx).getCurrentComponent()
    if doc is None or not doc.supportsService(
            "com.sun.star.text.TextDocument"):
        message_box(ctx, parent, u"Otwórz raport w programie Writer, "
                                 u"a następnie ponów zapis.", kind="warning")
        return None

    ticket = report_ticket(doc)
    if not ticket:
        dlg = InputDialog(ctx, parent, u"Zapis raportu",
                          u"Dokument nie zawiera numeru zgłoszenia. "
                          u"Podaj numer:")
        try:
            ticket = dlg.run()
        finally:
            dlg.dispose()
        if not ticket:
            return None

    def ask_conflict(existing):
        dlg = ConflictDialog(ctx, parent, existing)
        try:
            return dlg.run()
        finally:
            dlg.dispose()

    folder = storage.effective_output_dir(settings)
    paths = save_and_export(doc, folder, ticket, settings, ask_conflict)
    if not paths:
        return None
    try:
        doc.getCurrentController().removeInfobar("service_report_info")
    except Exception:
        pass
    _log(ctx, u"Zapisano: %s" % u", ".join(paths.values()))
    if settings.get("open_folder_after_export"):
        _open_folder(ctx, folder)
    message_box(ctx, parent, u"Zapisano raport:\n\n" +
                u"\n".join(paths[k] for k in ("odt", "pdf") if k in paths))
    return paths


def _open_folder(ctx, folder):
    try:
        shell = ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.system.SystemShellExecute", ctx)
        shell.execute(uno.systemPathToFileUrl(folder), "", 1)
    except Exception:
        _log(ctx, u"Nie udało się otworzyć folderu:\n" + traceback.format_exc())


def phrase_library(ctx):
    dlg = PhraseLibraryDialog(ctx, _parent_window(ctx), user_data_dir(ctx))
    try:
        dlg.run()
    finally:
        dlg.dispose()


def settings_dialog(ctx):
    user_dir = user_data_dir(ctx)
    dlg = SettingsDialog(ctx, _parent_window(ctx), storage.load_settings(user_dir))
    try:
        result = dlg.run()
    finally:
        dlg.dispose()
    if result:
        storage.save_settings(user_dir, result)


HELP_TEXT = u"""RAPORT SERWISOWY – POMOC

1. Raport serwisowy → Nowy raport – otwiera formularz.
2. Wypełnij dane urządzenia i pola A–D. Każda linia to jeden punkt
   w formacie:  Kategoria / opis   (tekst przed pierwszym „/” jest pogrubiony).
3. Gotowe sformułowania: wybierz kategorię i frazę, a następnie
   „Wstaw frazę do pola” (lub dwuklik). Fraza trafia do pola, które
   ostatnio edytowałeś (albo wskazanego na liście „Wstaw do pola”).
4. „Generuj raport” tworzy dokument Writer – NIE zapisuje go.
   Sprawdź raport i popraw go ręcznie, jeśli trzeba.
5. Raport serwisowy → Zapisz i eksportuj PDF – zapisuje
   Raport_<numer>.odt oraz Raport_<numer>.pdf.

Program nie dopisuje żadnych faktów: w raporcie są wyłącznie dane
wpisane lub świadomie wybrane przez operatora.

Pliki użytkownika: %s
Dokumentacja: %s"""


def show_help(ctx):
    message_box(ctx, _parent_window(ctx),
                HELP_TEXT % (user_data_dir(ctx),
                             os.path.join(C.DOCS_DIR, "USER_GUIDE.md")),
                title=u"Pomoc – Raport serwisowy")


COMMANDS = {
    "new": new_report,
    "export": export_current,
    "phrases": phrase_library,
    "settings": settings_dialog,
    "help": show_help,
}


def dispatch(ctx, command):
    command = (command or "new").strip().lower()
    handler = COMMANDS.get(command)
    if handler is None:
        return None
    try:
        return handler(ctx)
    except Exception:
        details = traceback.format_exc()
        _log(ctx, details)
        try:
            message_box(ctx, _parent_window(ctx),
                        u"Wystąpił błąd:\n\n%s" % details, kind="error")
        except Exception:
            pass
        return None


def _script_ctx():
    return XSCRIPTCONTEXT.getComponentContext()


def NowyRaport(*args):
    dispatch(_script_ctx(), "new")


def ZapiszIEksportujPDF(*args):
    dispatch(_script_ctx(), "export")


g_exportedScripts = (NowyRaport, ZapiszIEksportujPDF)
