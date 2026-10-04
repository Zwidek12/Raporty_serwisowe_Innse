import datetime
import os
import traceback

import uno
import unohelper
from com.sun.star.awt import (XActionListener, XFocusListener, XItemListener,
                              XTextListener)
from com.sun.star.awt.FontWeight import BOLD
from com.sun.star.awt.PosSize import POS

from . import constants as C
from . import storage
from .parser import append_line, split_lines
from .phrases import CUSTOM_CATEGORY_ID, PhraseLibrary
from .report_model import status_text
from .validators import status_change_warning, validate

BUTTONS_OK = 1
BUTTONS_YES_NO = 3
RESULT_YES = 2

_BOX_TYPES = {
    "info": "INFOBOX",
    "warning": "WARNINGBOX",
    "error": "ERRORBOX",
    "query": "QUERYBOX",
}


def message_box(ctx, parent, text, title=C.APP_NAME, kind="info",
                buttons=BUTTONS_OK):
    toolkit = ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.awt.Toolkit", ctx)
    box_type = uno.Enum("com.sun.star.awt.MessageBoxType", _BOX_TYPES[kind])
    box = toolkit.createMessageBox(parent, box_type, buttons, title, text)
    try:
        return box.execute()
    finally:
        box.dispose()


def ask_yes_no(ctx, parent, text, title=C.APP_NAME):
    return message_box(ctx, parent, text, title, "query",
                       BUTTONS_YES_NO) == RESULT_YES


class _Listener(unohelper.Base):
    def __init__(self, owner, callback):
        self.owner = owner
        self.callback = callback

    def _call(self, *args):
        try:
            self.callback(*args)
        except Exception:
            self.owner.show_exception()

    def disposing(self, event):
        pass


class ActionListener(_Listener, XActionListener):
    def actionPerformed(self, event):
        self._call()


class ItemListener(_Listener, XItemListener):
    def itemStateChanged(self, event):
        self._call()


class FocusListener(_Listener, XFocusListener):
    def focusGained(self, event):
        self._call()

    def focusLost(self, event):
        pass


class TextListener(_Listener, XTextListener):
    def textChanged(self, event):
        self._call()


class DialogBase(object):
    def __init__(self, ctx, parent, title, width, height):
        self.ctx = ctx
        self.parent = parent
        self.smgr = ctx.ServiceManager
        self.model = self.smgr.createInstanceWithContext(
            "com.sun.star.awt.UnoControlDialogModel", ctx)
        self.model.PositionX = 40
        self.model.PositionY = 20
        self.model.Width = width
        self.model.Height = height
        self.model.Title = title
        self.model.Closeable = True
        self.model.Moveable = True
        self.dialog = self.smgr.createInstanceWithContext(
            "com.sun.star.awt.UnoControlDialog", ctx)
        self.dialog.setModel(self.model)
        self._listeners = []
        self._peer_created = False

    def add(self, kind, name, x, y, w, h, **properties):
        model = self.model.createInstance(
            "com.sun.star.awt.UnoControl%sModel" % kind)
        model.PositionX = x
        model.PositionY = y
        model.Width = w
        model.Height = h
        model.Name = name
        for key, value in properties.items():
            setattr(model, key, value)
        self.model.insertByName(name, model)
        return self.dialog.getControl(name)

    def label(self, name, x, y, w, text, h=9, bold=False, **kw):
        ctrl = self.add("FixedText", name, x, y, w, h, Label=text, **kw)
        if bold:
            ctrl.getModel().FontWeight = BOLD
        return ctrl

    def edit(self, name, x, y, w, h=12, text=u"", multiline=False, **kw):
        if multiline:
            kw.setdefault("MultiLine", True)
            kw.setdefault("VScroll", True)
            kw.setdefault("AutoVScroll", False)
        return self.add("Edit", name, x, y, w, h, Text=text, **kw)

    def listbox(self, name, x, y, w, h, items, dropdown=True, **kw):
        if dropdown:
            kw.setdefault("Dropdown", True)
            kw.setdefault("LineCount", 16)
        return self.add("ListBox", name, x, y, w, h,
                        StringItemList=tuple(items), **kw)

    def button(self, name, x, y, w, text, callback, h=14, **kw):
        ctrl = self.add("Button", name, x, y, w, h, Label=text, **kw)
        listener = ActionListener(self, callback)
        self._listeners.append(listener)
        ctrl.addActionListener(listener)
        return ctrl

    def checkbox(self, name, x, y, w, text, checked=False, h=10):
        return self.add("CheckBox", name, x, y, w, h, Label=text,
                        State=1 if checked else 0)

    def on_item(self, name, callback):
        listener = ItemListener(self, callback)
        self._listeners.append(listener)
        self.ctrl(name).addItemListener(listener)

    def on_action(self, name, callback):
        listener = ActionListener(self, callback)
        self._listeners.append(listener)
        self.ctrl(name).addActionListener(listener)

    def on_focus(self, name, callback):
        listener = FocusListener(self, callback)
        self._listeners.append(listener)
        self.ctrl(name).addFocusListener(listener)

    def ctrl(self, name):
        return self.dialog.getControl(name)

    def get_text(self, name):
        return self.ctrl(name).getModel().Text or u""

    def set_text(self, name, value):
        self.ctrl(name).getModel().Text = value or u""

    def get_checked(self, name):
        return self.ctrl(name).getModel().State == 1

    def selected_pos(self, name):
        return self.ctrl(name).getSelectedItemPos()

    def selected_item(self, name):
        return self.ctrl(name).getSelectedItem() or u""

    def select_pos(self, name, pos):
        ctrl = self.ctrl(name)
        if 0 <= pos < ctrl.getItemCount():
            ctrl.selectItemPos(pos, True)

    def select_item(self, name, value):
        items = list(self.ctrl(name).getModel().StringItemList)
        if value in items:
            self.select_pos(name, items.index(value))

    def set_items(self, name, items):
        self.ctrl(name).getModel().StringItemList = tuple(items)

    def enable(self, name, enabled=True):
        self.ctrl(name).getModel().Enabled = bool(enabled)

    @property
    def peer(self):
        return self.dialog.getPeer() if self._peer_created else self.parent

    def create_peer(self):
        if self._peer_created:
            return
        toolkit = self.smgr.createInstanceWithContext(
            "com.sun.star.awt.Toolkit", self.ctx)
        self.dialog.setVisible(False)
        self.dialog.createPeer(toolkit, self.parent)
        self._peer_created = True
        self._center()
        self.after_peer()

    def after_peer(self):
        pass

    def _center(self):
        try:
            if self.parent is None:
                return
            p = self.parent.getPosSize()
            d = self.dialog.getPosSize()
            x = p.X + max(0, (p.Width - d.Width) // 2)
            y = p.Y + max(0, (p.Height - d.Height) // 2)
            self.dialog.setPosSize(x, y, 0, 0, POS)
        except Exception:
            pass

    def execute(self):
        self.create_peer()
        return self.dialog.execute()

    def close(self):
        self.dialog.endExecute()

    def dispose(self):
        try:
            self.dialog.dispose()
        except Exception:
            pass

    def info(self, text, kind="info"):
        return message_box(self.ctx, self.peer, text, C.APP_NAME, kind)

    def ask(self, text):
        return ask_yes_no(self.ctx, self.peer, text)

    def show_exception(self):
        self.info(u"Wystąpił nieoczekiwany błąd:\n\n" + traceback.format_exc(),
                  "error")


def _last_nonempty_line(value):
    for line in reversed(split_lines(value)):
        if line.strip():
            return line.strip()
    return u""


def file_url_to_path(url):
    return uno.fileUrlToSystemPath(url) if url else u""


class MainDialog(DialogBase):
    W, H = 700, 334
    FIELD_CTRLS = {
        C.FIELD_CUSTOMER: "txtCustomer",
        C.FIELD_DIAGNOSIS: "txtDiagnosis",
        C.FIELD_WORK: "txtWork",
        C.FIELD_TESTS: "txtTests",
    }
    DEVICE_NONE = u"(nie wybrano)"

    def __init__(self, ctx, parent, settings, user_dir, draft=None):
        DialogBase.__init__(self, ctx, parent,
                            u"Utwórz raport serwisowy", self.W, self.H)
        self.settings = settings
        self.user_dir = user_dir
        self.draft = draft or {}
        self.result = None
        self.library = None
        self.categories = []
        self._build()
        self.reload_library()

    def _build(self):
        x1, x2, cw = 6, 124, 112
        fw = 230

        def pair(y, left, right):
            for x, (name, text, kind, extra) in ((x1, left), (x2, right)):
                self.label("lbl_" + name, x, y, cw, text)
                if kind == "edit":
                    self.edit(name, x, y + 9, cw, **extra)
                else:
                    self.listbox(name, x, y + 9, cw, 12, extra["items"])

        today = datetime.date.today().strftime("%d.%m.%Y")
        pair(6, ("edTicket", u"Numer zgłoszenia *", "edit", {}),
                ("edReportDate", u"Data sporządzenia * (DD.MM.RRRR)", "edit",
                 {"text": today}))
        pair(31, ("edReceiptDate", u"Data przyjęcia (DD.MM.RRRR)", "edit", {}),
                 ("edTechnician", u"Serwis / technik", "edit",
                  {"text": self.settings.get("default_technician", u"")}))
        pair(56, ("edManufacturer", u"Producent *", "edit", {}),
                 ("edModel", u"Model *", "edit", {}))
        pair(81, ("edSerial", u"Numer seryjny", "edit", {}),
                 ("lbDeviceType", u"Typ urządzenia (kolejność fraz)", "list",
                  {"items": [self.DEVICE_NONE] + C.DEVICE_TYPES}))
        self.label("lbl_devtext", x1, 106, fw,
                   u"Rodzaj urządzenia (tekst w raporcie, np. TV LED 4K 85\")")
        self.edit("edDeviceText", x1, 115, fw)
        pair(131, ("lbReportType", u"Rodzaj raportu", "list",
                   {"items": C.REPORT_TYPES}),
                  ("lbStatus", u"Status końcowy", "list",
                   {"items": C.STATUSES}))
        self.label("lbl_status_text", x1, 156, fw,
                   u"Treść statusu końcowego (podgląd / własny tekst)")
        self.edit("edStatusText", x1, 165, fw, 46, multiline=True,
                  ReadOnly=True)
        pair(217, ("lbDiagIntro", u"Wstęp do diagnozy", "list",
                   {"items": C.INTRO_VARIANT_LABELS}),
                  ("lbTestsIntro", u"Wstęp do testów", "list",
                   {"items": C.INTRO_VARIANT_LABELS}))
        self.label("lbl_hint", x1, 246, fw,
                   u"Format wpisu w polach A–D:  Kategoria / opis\n"
                   u"Każda linia to osobny punkt raportu. Tekst przed "
                   u"pierwszym „/” zostanie pogrubiony.\n"
                   u"Program niczego nie dopisuje sam – w raporcie znajdzie "
                   u"się tylko to, co wpiszesz lub wybierzesz.\n"
                   u"Pola oznaczone * są wymagane.", h=56, MultiLine=True)

        x, w, h = 242, 270, 60
        for i, key in enumerate(C.TEXT_FIELDS):
            y = 6 + i * 75
            self.label("lbl_" + key, x, y, w, C.FIELD_LABELS[key], bold=True)
            self.edit(self.FIELD_CTRLS[key], x, y + 9, w, h, multiline=True,
                      HelpText=u"Każda linia = jeden punkt. Format: "
                               u"Kategoria / opis")

        px, pw = 518, 176
        self.label("lbl_phr", px, 6, pw, u"Gotowe sformułowania", bold=True)
        self.label("lbl_cat", px, 17, pw, u"Kategoria:")
        self.listbox("lbCategory", px, 26, pw, 12, [])
        self.listbox("lbPhrases", px, 42, pw, 118, [], dropdown=False,
                     HelpText=u"Dwuklik wstawia frazę do wskazanego pola.")
        self.label("lbl_prev", px, 164, pw, u"Treść frazy:")
        self.edit("edPreview", px, 173, pw, 40, multiline=True, ReadOnly=True)
        self.label("lbl_target", px, 217, pw, u"Wstaw do pola:")
        self.listbox("lbTarget", px, 226, pw, 12,
                     [C.FIELD_LABELS[k].rstrip(u" *") for k in C.TEXT_FIELDS])
        self.button("btnInsert", px, 244, pw, u"Wstaw frazę do pola",
                    self.insert_phrase)
        self.button("btnSavePhrase", px, 262, pw,
                    u"Zapisz jako własną frazę…", self.save_custom_phrase)
        self.button("btnDeletePhrase", px, 280, pw, u"Usuń własną frazę",
                    self.delete_custom_phrase)

        self.button("btnClear", 6, 314, 90, u"Wyczyść formularz", self.clear)
        self.button("btnGenerate", 520, 314, 84, u"Generuj raport",
                    self.generate)
        self.button("btnCancel", 610, 314, 84, u"Anuluj", self.close)

        self.on_item("lbCategory", self.refresh_phrases)
        self.on_item("lbPhrases", self.refresh_preview)
        self.on_action("lbPhrases", self.insert_phrase)
        self.on_item("lbStatus", self.status_changed)
        self.on_item("lbDeviceType", self.device_type_changed)
        for index, key in enumerate(C.TEXT_FIELDS):
            self.on_focus(self.FIELD_CTRLS[key],
                          lambda i=index: self.select_pos("lbTarget", i))

    def after_peer(self):
        self.select_item("lbReportType",
                         self.settings.get("default_report_type", C.RT_REPAIR))
        self.select_pos("lbStatus", 0)
        self.select_pos("lbDeviceType", 0)
        self.select_pos("lbDiagIntro", 0)
        self.select_pos("lbTestsIntro", 0)
        self.select_pos("lbTarget", 1)
        if self.draft:
            self.set_form(self.draft)
        self.refresh_categories()
        self.update_status_text()

    def reload_library(self):
        custom = storage.load_custom_phrases(self.user_dir)
        self.library = PhraseLibrary.load(custom_phrases=custom)

    def current_device_type(self):
        value = self.selected_item("lbDeviceType")
        return u"" if value == self.DEVICE_NONE else value

    def refresh_categories(self, select_id=None):
        self.categories = self.library.ordered_categories(
            self.current_device_type())
        self.set_items("lbCategory", [c["title"] for c in self.categories])
        pos = 0
        if select_id:
            for i, cat in enumerate(self.categories):
                if cat["id"] == select_id:
                    pos = i
        self.select_pos("lbCategory", pos)
        self.refresh_phrases()

    def current_category(self):
        pos = self.selected_pos("lbCategory")
        if 0 <= pos < len(self.categories):
            return self.categories[pos]
        return None

    def current_phrase(self):
        cat = self.current_category()
        pos = self.selected_pos("lbPhrases")
        if cat and 0 <= pos < len(cat["phrases"]):
            return cat["phrases"][pos]
        return None

    def refresh_phrases(self):
        cat = self.current_category()
        phrases = cat["phrases"] if cat else []
        self.set_items("lbPhrases", [p["title"] for p in phrases])
        self.set_text("edPreview", u"")
        is_custom = bool(cat and cat["id"] == CUSTOM_CATEGORY_ID)
        self.enable("btnDeletePhrase", is_custom)

    def refresh_preview(self):
        phrase = self.current_phrase()
        self.set_text("edPreview", phrase["text"] if phrase else u"")

    def target_field(self):
        pos = self.selected_pos("lbTarget")
        if pos < 0:
            pos = 1
        return C.TEXT_FIELDS[pos]

    def insert_phrase(self):
        phrase = self.current_phrase()
        if phrase is None:
            self.info(u"Najpierw wybierz frazę z listy.")
            return
        ctrl_name = self.FIELD_CTRLS[self.target_field()]
        self.set_text(ctrl_name, append_line(self.get_text(ctrl_name),
                                             phrase["text"]))
        if self.target_field() == C.FIELD_WORK:
            self.update_status_text()

    def save_custom_phrase(self):
        text = self.get_text("edPreview").strip()
        if not text:
            field = self.FIELD_CTRLS[self.target_field()]
            text = _last_nonempty_line(self.get_text(field))
        dlg = CustomPhraseDialog(self.ctx, self.peer, u"", text)
        try:
            data = dlg.run()
        finally:
            dlg.dispose()
        if not data:
            return
        phrases = storage.load_custom_phrases(self.user_dir)
        phrases = storage.add_custom_phrase(phrases, data["title"],
                                            data["text"])
        storage.save_custom_phrases(self.user_dir, phrases)
        self.reload_library()
        self.refresh_categories(CUSTOM_CATEGORY_ID)

    def delete_custom_phrase(self):
        cat = self.current_category()
        phrase = self.current_phrase()
        if not cat or cat["id"] != CUSTOM_CATEGORY_ID or not phrase:
            self.info(u"Wybierz frazę z kategorii „Własne frazy”.")
            return
        if not self.ask(u"Usunąć własną frazę „%s”?" % phrase["title"]):
            return
        phrases = storage.remove_custom_phrase(
            storage.load_custom_phrases(self.user_dir), phrase["id"])
        storage.save_custom_phrases(self.user_dir, phrases)
        self.reload_library()
        self.refresh_categories()

    def update_status_text(self):
        status = self.selected_item("lbStatus")
        ctrl = self.ctrl("edStatusText").getModel()
        if status == C.ST_CUSTOM:
            if ctrl.ReadOnly:
                ctrl.ReadOnly = False
                ctrl.Text = self.draft.get("custom_status", u"") \
                    if self.draft.get("status") == C.ST_CUSTOM else u""
        else:
            ctrl.ReadOnly = True
            ctrl.Text = status_text(status)

    def status_changed(self):
        self.update_status_text()
        warning = status_change_warning(self.selected_item("lbStatus"),
                                        self.get_text("txtWork"))
        if warning:
            self.info(warning, "warning")

    def device_type_changed(self):
        device = self.current_device_type()
        if device and device != u"Inne" and not self.get_text(
                "edDeviceText").strip():
            self.set_text("edDeviceText", device)
        self.refresh_categories()

    def get_form(self):
        status = self.selected_item("lbStatus") or C.ST_NONE
        return {
            "ticket": self.get_text("edTicket"),
            "report_date": self.get_text("edReportDate"),
            "receipt_date": self.get_text("edReceiptDate"),
            "technician": self.get_text("edTechnician"),
            "manufacturer": self.get_text("edManufacturer"),
            "model": self.get_text("edModel"),
            "serial": self.get_text("edSerial"),
            "device_type": self.current_device_type(),
            "device_type_text": self.get_text("edDeviceText"),
            "report_type": self.selected_item("lbReportType") or C.RT_OTHER,
            "status": status,
            "custom_status": self.get_text("edStatusText")
            if status == C.ST_CUSTOM else u"",
            "diagnosis_intro": max(0, self.selected_pos("lbDiagIntro")),
            "tests_intro": max(0, self.selected_pos("lbTestsIntro")),
            C.FIELD_CUSTOMER: self.get_text("txtCustomer"),
            C.FIELD_DIAGNOSIS: self.get_text("txtDiagnosis"),
            C.FIELD_WORK: self.get_text("txtWork"),
            C.FIELD_TESTS: self.get_text("txtTests"),
        }

    def set_form(self, form):
        simple = {
            "edTicket": "ticket", "edReportDate": "report_date",
            "edReceiptDate": "receipt_date", "edTechnician": "technician",
            "edManufacturer": "manufacturer", "edModel": "model",
            "edSerial": "serial", "edDeviceText": "device_type_text",
        }
        for ctrl_name, key in simple.items():
            if key in form:
                self.set_text(ctrl_name, form.get(key))
        for key, ctrl_name in self.FIELD_CTRLS.items():
            self.set_text(ctrl_name, form.get(key, u""))
        if form.get("device_type"):
            self.select_item("lbDeviceType", form["device_type"])
        self.select_item("lbReportType", form.get("report_type"))
        self.select_item("lbStatus", form.get("status"))
        self.select_pos("lbDiagIntro", int(form.get("diagnosis_intro", 0) or 0))
        self.select_pos("lbTestsIntro", int(form.get("tests_intro", 0) or 0))
        self.update_status_text()
        if form.get("status") == C.ST_CUSTOM:
            self.set_text("edStatusText", form.get("custom_status", u""))

    def clear(self):
        if not self.ask(u"Wyczyścić wszystkie pola formularza?"):
            return
        self.draft = {}
        empty = dict((k, u"") for k in (
            "ticket", "receipt_date", "manufacturer", "model", "serial",
            "device_type_text"))
        empty.update({
            "report_date": datetime.date.today().strftime("%d.%m.%Y"),
            "technician": self.settings.get("default_technician", u""),
            "report_type": self.settings.get("default_report_type",
                                             C.RT_REPAIR),
            "status": C.ST_NONE,
        })
        self.set_form(empty)
        self.select_pos("lbDeviceType", 0)
        self.refresh_categories()

    def generate(self):
        form = self.get_form()
        errors, warnings = validate(form)
        if errors:
            self.info(u"Popraw następujące pola:\n\n• " + u"\n• ".join(errors),
                      "error")
            return
        if warnings:
            question = (u"Uwagi do raportu:\n\n• " + u"\n• ".join(warnings)
                        + u"\n\nCzy mimo to wygenerować raport?")
            if not self.ask(question):
                return
        self.result = form
        self.close()

    def run(self):
        self.execute()
        return self.result


class CustomPhraseDialog(DialogBase):
    def __init__(self, ctx, parent, title=u"", text=u""):
        DialogBase.__init__(self, ctx, parent, u"Zapisz własną frazę", 300, 150)
        self.result = None
        self.label("lbl_title", 6, 6, 288, u"Nazwa frazy (widoczna na liście):")
        self.edit("edTitle", 6, 15, 288, text=title)
        self.label("lbl_text", 6, 33, 288,
                   u"Treść (format: Kategoria / opis):")
        self.edit("edText", 6, 42, 288, 70, text=text, multiline=True)
        self.button("btnOk", 150, 130, 70, u"Zapisz", self.save)
        self.button("btnCancel", 224, 130, 70, u"Anuluj", self.close)

    def save(self):
        title = self.get_text("edTitle").strip()
        text = u" ".join(l.strip() for l in split_lines(self.get_text("edText"))
                         if l.strip())
        if not title or not text:
            self.info(u"Podaj nazwę i treść frazy.", "warning")
            return
        self.result = {"title": title, "text": text}
        self.close()

    def run(self):
        self.execute()
        return self.result


class PhraseLibraryDialog(DialogBase):
    def __init__(self, ctx, parent, user_dir):
        DialogBase.__init__(self, ctx, parent, u"Biblioteka fraz", 420, 250)
        self.user_dir = user_dir
        self.categories = []
        self.label("lbl_cat", 6, 6, 130, u"Kategoria:", bold=True)
        self.listbox("lbCategory", 6, 16, 130, 200, [], dropdown=False)
        self.label("lbl_phr", 142, 6, 272, u"Frazy:", bold=True)
        self.listbox("lbPhrases", 142, 16, 272, 120, [], dropdown=False)
        self.label("lbl_text", 142, 140, 272, u"Treść:")
        self.edit("edText", 142, 149, 272, 44, multiline=True, ReadOnly=True)
        self.label("lbl_info", 142, 196, 272,
                   u"Frazy własne: %s\nFrazy domyślne: %s" % (
                       os.path.join(user_dir, C.CUSTOM_PHRASES_FILE_NAME),
                       C.PHRASES_DEFAULT_FILE), h=20, MultiLine=True)
        self.button("btnAdd", 6, 228, 100, u"Dodaj własną frazę…", self.add_phrase)
        self.button("btnDelete", 110, 228, 100, u"Usuń własną frazę",
                    self.delete_phrase)
        self.button("btnClose", 344, 228, 70, u"Zamknij", self.close)
        self.on_item("lbCategory", self.refresh_phrases)
        self.on_item("lbPhrases", self.refresh_text)

    def after_peer(self):
        self.reload()

    def reload(self, select_id=None):
        library = PhraseLibrary.load(
            custom_phrases=storage.load_custom_phrases(self.user_dir))
        self.categories = library.ordered_categories()
        self.set_items("lbCategory", [c["title"] for c in self.categories])
        pos = 0
        for i, cat in enumerate(self.categories):
            if cat["id"] == select_id:
                pos = i
        self.select_pos("lbCategory", pos)
        self.refresh_phrases()

    def current_category(self):
        pos = self.selected_pos("lbCategory")
        return self.categories[pos] if 0 <= pos < len(self.categories) else None

    def current_phrase(self):
        cat = self.current_category()
        pos = self.selected_pos("lbPhrases")
        if cat and 0 <= pos < len(cat["phrases"]):
            return cat["phrases"][pos]
        return None

    def refresh_phrases(self):
        cat = self.current_category()
        self.set_items("lbPhrases",
                       [p["title"] for p in (cat["phrases"] if cat else [])])
        self.set_text("edText", u"")
        self.enable("btnDelete", bool(cat and cat["id"] == CUSTOM_CATEGORY_ID))

    def refresh_text(self):
        phrase = self.current_phrase()
        self.set_text("edText", phrase["text"] if phrase else u"")

    def add_phrase(self):
        dlg = CustomPhraseDialog(self.ctx, self.peer)
        try:
            data = dlg.run()
        finally:
            dlg.dispose()
        if not data:
            return
        phrases = storage.add_custom_phrase(
            storage.load_custom_phrases(self.user_dir),
            data["title"], data["text"])
        storage.save_custom_phrases(self.user_dir, phrases)
        self.reload(CUSTOM_CATEGORY_ID)

    def delete_phrase(self):
        cat = self.current_category()
        phrase = self.current_phrase()
        if not cat or cat["id"] != CUSTOM_CATEGORY_ID or not phrase:
            self.info(u"Wybierz frazę z kategorii „Własne frazy”.")
            return
        if not self.ask(u"Usunąć własną frazę „%s”?" % phrase["title"]):
            return
        storage.save_custom_phrases(self.user_dir, storage.remove_custom_phrase(
            storage.load_custom_phrases(self.user_dir), phrase["id"]))
        self.reload(CUSTOM_CATEGORY_ID)

    def run(self):
        self.execute()


def pick_letterhead_file(ctx, current=u""):
    picker = ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.ui.dialogs.FilePicker", ctx)
    patterns = u";".join(u"*" + e for e in C.LETTERHEAD_EXTENSIONS)
    picker.appendFilter(u"Papier firmowy (Writer / Word)", patterns)
    picker.appendFilter(u"Wszystkie pliki", u"*.*")
    folder = os.path.dirname(current) if current else u""
    if folder and os.path.isdir(folder):
        picker.setDisplayDirectory(uno.systemPathToFileUrl(folder))
    if picker.execute() == 1:
        files = picker.getSelectedFiles()
        if files:
            return file_url_to_path(files[0])
    return u""


class SettingsDialog(DialogBase):
    def __init__(self, ctx, parent, settings, user_dir):
        DialogBase.__init__(self, ctx, parent, u"Ustawienia – Raport serwisowy",
                            320, 232)
        self.settings = dict(settings)
        self.user_dir = user_dir
        self.result = None
        s = self.settings
        self.label("lbl_letter", 6, 6, 308,
                   u"Papier firmowy (.ott, .odt, .docx, .doc):", bold=True)
        self.edit("edLetter", 6, 15, 194, text=s.get("letterhead_path", u""))
        self.button("btnLetter", 204, 14, 54, u"Wybierz…", self.pick_letter)
        self.button("btnLetterClear", 262, 14, 52, u"Usuń", self.clear_letter)
        self.label("lbl_letter_info", 6, 30, 308,
                   u"Raport jest tworzony na tym papierze: jego nagłówek, stopka, "
                   u"logo i marginesy zostają bez zmian. Plik jest kopiowany do "
                   u"profilu użytkownika.", h=18, MultiLine=True)
        self.label("lbl_dir", 6, 52, 308, u"Domyślny katalog zapisu raportów:")
        self.edit("edDir", 6, 61, 250,
                  text=s.get("output_dir") or storage.default_output_dir())
        self.button("btnDir", 260, 60, 54, u"Wybierz…", self.pick_dir)
        self.label("lbl_tech", 6, 79, 308, u"Domyślny serwis / technik:")
        self.edit("edTech", 6, 88, 308, text=s.get("default_technician", u""))
        self.label("lbl_type", 6, 106, 308, u"Domyślny rodzaj raportu:")
        self.listbox("lbType", 6, 115, 150, 12, C.REPORT_TYPES)
        self.checkbox("cbOpen", 6, 135, 308,
                      u"Otwórz folder po eksporcie",
                      s.get("open_folder_after_export", True))
        self.checkbox("cbOdt", 6, 149, 308, u"Zapisuj kopię ODT",
                      s.get("save_odt", True))
        self.checkbox("cbPdf", 6, 163, 308, u"Generuj PDF",
                      s.get("export_pdf", True))
        self.label("lbl_note", 6, 180, 308,
                   u"Ustawienia są zapisywane lokalnie w profilu użytkownika "
                   u"LibreOffice.", h=18, MultiLine=True)
        self.button("btnOk", 170, 212, 70, u"Zapisz", self.save)
        self.button("btnCancel", 244, 212, 70, u"Anuluj", self.close)

    def after_peer(self):
        self.select_item("lbType", self.settings.get("default_report_type",
                                                     C.RT_REPAIR))

    def pick_dir(self):
        picker = self.smgr.createInstanceWithContext(
            "com.sun.star.ui.dialogs.FolderPicker", self.ctx)
        current = self.get_text("edDir").strip()
        if current and os.path.isdir(current):
            picker.setDisplayDirectory(uno.systemPathToFileUrl(current))
        if picker.execute() == 1:
            self.set_text("edDir", file_url_to_path(picker.getDirectory()))

    def pick_letter(self):
        path = pick_letterhead_file(self.ctx, self.get_text("edLetter").strip())
        if path:
            self.set_text("edLetter", path)

    def clear_letter(self):
        self.set_text("edLetter", u"")

    def save(self):
        letter = self.get_text("edLetter").strip()
        if letter and not os.path.isfile(letter):
            self.info(u"Nie znaleziono pliku papieru firmowego:\n" + letter,
                      "warning")
            return
        if letter and not storage.is_letterhead_file(letter):
            self.info(u"Nieobsługiwany format papieru firmowego. Dozwolone: "
                      + u", ".join(C.LETTERHEAD_EXTENSIONS), "warning")
            return
        if not self.get_checked("cbOdt") and not self.get_checked("cbPdf"):
            self.info(u"Zaznacz co najmniej jedną opcję: zapis ODT lub PDF.",
                      "warning")
            return
        if letter:
            letter = storage.install_letterhead(self.user_dir, letter)
        else:
            storage.remove_letterhead(self.user_dir)
        out_dir = self.get_text("edDir").strip()
        self.settings.update({
            "letterhead_path": letter,
            "letterhead_asked": True,
            "output_dir": u"" if out_dir == storage.default_output_dir()
            else out_dir,
            "default_technician": self.get_text("edTech").strip(),
            "default_report_type": self.selected_item("lbType") or C.RT_REPAIR,
            "open_folder_after_export": self.get_checked("cbOpen"),
            "save_odt": self.get_checked("cbOdt"),
            "export_pdf": self.get_checked("cbPdf"),
        })
        self.result = self.settings
        self.close()

    def run(self):
        self.execute()
        return self.result


class ConflictDialog(DialogBase):
    def __init__(self, ctx, parent, existing):
        DialogBase.__init__(self, ctx, parent, u"Plik już istnieje", 290, 104)
        self.result = None
        names = u"\n".join(os.path.basename(p) for p in existing)
        self.label("lbl_msg", 6, 6, 278,
                   u"W katalogu docelowym istnieją już pliki:\n%s\n\n"
                   u"Co zrobić?" % names, h=64, MultiLine=True)
        self.button("btnOverwrite", 6, 84, 80, u"Nadpisz",
                    lambda: self._finish("overwrite"))
        self.button("btnVersion", 90, 84, 120, u"Zapisz jako nową wersję",
                    lambda: self._finish("version"))
        self.button("btnCancel", 214, 84, 70, u"Anuluj", self.close)

    def _finish(self, value):
        self.result = value
        self.close()

    def run(self):
        self.execute()
        return self.result


class InputDialog(DialogBase):
    def __init__(self, ctx, parent, title, prompt, value=u""):
        DialogBase.__init__(self, ctx, parent, title, 240, 64)
        self.result = None
        self.label("lbl", 6, 6, 228, prompt)
        self.edit("ed", 6, 16, 228, text=value)
        self.button("btnOk", 90, 44, 70, u"OK", self.ok)
        self.button("btnCancel", 164, 44, 70, u"Anuluj", self.close)

    def ok(self):
        value = self.get_text("ed").strip()
        if not value:
            return
        self.result = value
        self.close()

    def run(self):
        self.execute()
        return self.result
