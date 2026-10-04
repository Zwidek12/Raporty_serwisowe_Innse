import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.lo_session import Session
from report_generator import constants as C
from report_generator import dialog, document, report_model, storage
from report_generator.validators import validate


def main():
    user_dir = tempfile.mkdtemp(prefix="rg_user_")
    try:
        with Session() as s:
            ctx = s.ctx
            settings = storage.load_settings(user_dir)
            storage.save_custom_phrases(user_dir, storage.add_custom_phrase(
                [], u"TV – test pełny",
                u"Test urządzenia / Sprawdzono działanie obrazu, dźwięku, wejść "
                u"sygnałowych oraz podstawowych funkcji sterowania."))

            dlg = dialog.MainDialog(ctx, None, settings, user_dir)
            dlg.create_peer()
            assert dlg.selected_item("lbReportType") == C.RT_REPAIR
            assert dlg.selected_item("lbStatus") == C.ST_NONE

            dlg.select_item("lbDeviceType", u"Telewizor")
            dlg.device_type_changed()
            cats = [c["id"] for c in dlg.categories]
            assert cats[0] == "custom" and cats[1] == "display", cats
            assert dlg.get_text("edDeviceText") == u"Telewizor"

            dlg.select_pos("lbCategory", 1)
            dlg.refresh_phrases()
            dlg.select_pos("lbPhrases", 0)
            dlg.refresh_preview()
            assert dlg.get_text("edPreview").startswith(u"Wyświetlacz /")
            dlg.select_pos("lbTarget", 1)
            dlg.insert_phrase()
            dlg.insert_phrase()
            assert dlg.get_text("txtDiagnosis").count(u"\n") == 1

            dlg.select_pos("lbCategory", 0)
            dlg.refresh_phrases()
            dlg.select_pos("lbPhrases", 0)
            dlg.select_pos("lbTarget", 3)
            dlg.insert_phrase()
            assert dlg.get_text("txtTests").startswith(u"Test urządzenia /")

            dlg.set_text("edTicket", u"ZG/2026/77")
            dlg.set_text("edManufacturer", u"SONY")
            dlg.set_text("edModel", u"KE85XH9096")
            dlg.set_text("txtWork", u"Matryca / Wymieniono moduł matrycy.")
            dlg.select_item("lbStatus", C.ST_REPAIRED)
            dlg.update_status_text()
            assert dlg.get_text("edStatusText") == C.STATUS_TEXTS[C.ST_REPAIRED]
            dlg.select_item("lbStatus", C.ST_CUSTOM)
            dlg.update_status_text()
            assert not dlg.ctrl("edStatusText").getModel().ReadOnly
            dlg.set_text("edStatusText", u"Status własny.")

            form = dlg.get_form()
            errors, warnings = validate(form)
            assert not errors, errors
            print("Formularz:", {k: form[k] for k in ("ticket", "status",
                                                      "device_type")})
            print("Ostrzeżenia:", warnings)

            dlg2 = dialog.MainDialog(ctx, None, settings, user_dir, form)
            dlg2.create_peer()
            assert dlg2.get_form() == form, (dlg2.get_form(), form)
            dlg2.dispose()
            dlg.dispose()

            model = report_model.build_report(form)
            doc = document.create_report(ctx, model, settings, hidden=True)
            text = doc.getText().getString()
            doc.close(True)
            assert u"Wyświetlacz: Obraz jest wyświetlany" in text
            assert u"Status własny." in text

            for cls, args in ((dialog.SettingsDialog, (settings,)),
                              (dialog.PhraseLibraryDialog, (user_dir,)),
                              (dialog.CustomPhraseDialog, ()),
                              (dialog.ConflictDialog, (["C:\\x\\Raport_1.pdf"],)),
                              (dialog.InputDialog, (u"T", u"Podaj:"))):
                d = cls(ctx, None, *args)
                d.create_peer()
                d.dispose()
            print("Wszystkie okna utworzone poprawnie.")
    finally:
        shutil.rmtree(user_dir, ignore_errors=True)
    print("SMOKE TEST OK")


if __name__ == "__main__":
    main()
