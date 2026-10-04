import os

import uno
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK

from . import constants as C

OPTIONAL_FIELDS = (
    C.BM_RECEIPT_DATE, C.BM_TECHNICIAN, C.BM_DEVICE_SERIAL, C.BM_DEVICE_TYPE,
    C.BM_DEVICE_STATUS,
)

LOGO_MAX_WIDTH = 4500
LOGO_MAX_HEIGHT = 1800
PROPERTY_REMOVABLE = 128


def props(**kwargs):
    result = []
    for name, value in kwargs.items():
        pv = PropertyValue()
        pv.Name = name
        pv.Value = value
        result.append(pv)
    return tuple(result)


def _utf16_len(value):
    return len(value.encode("utf-16-le")) // 2


def _bookmark(doc, name):
    marks = doc.getBookmarks()
    if marks.hasByName(name):
        return marks.getByName(name)
    return None


def _set_bookmark_text(doc, name, value, weight=NORMAL):
    mark = _bookmark(doc, name)
    if mark is None:
        return False
    anchor = mark.getAnchor()
    cur = anchor.getText().createTextCursorByRange(anchor)
    cur.setString(value or u"")
    if value:
        cur.CharWeight = weight
    return True


def delete_paragraph_at(rng):
    text = rng.getText()
    cur = text.createTextCursorByRange(rng.getStart())
    cur.gotoStartOfParagraph(False)
    if cur.goLeft(1, False):
        cur.goRight(1, True)
        cur.gotoEndOfParagraph(True)
    else:
        cur.gotoEndOfParagraph(True)
        cur.goRight(1, True)
    cur.setString(u"")


def _delete_bookmark_paragraph(doc, name):
    mark = _bookmark(doc, name)
    if mark is not None:
        delete_paragraph_at(mark.getAnchor())


def write_paragraphs(rng, paragraphs):
    text = rng.getText()
    cur = text.createTextCursorByRange(rng.getStart())
    cur.gotoStartOfParagraph(False)
    cur.gotoEndOfParagraph(True)
    cur.setString(u"")
    cur.collapseToEnd()
    for index, (style, label, body) in enumerate(paragraphs):
        if index:
            cur.gotoEndOfParagraph(False)
            text.insertControlCharacter(cur, PARAGRAPH_BREAK, False)
        cur.ParaStyleName = style
        if label:
            line = u"%s: %s" % (label, body)
        else:
            line = body
        text.insertString(cur, line, False)
        if label:
            bold = text.createTextCursorByRange(cur.getStart())
            bold.gotoStartOfParagraph(False)
            bold.goRight(_utf16_len(label) + 1, True)
            bold.CharWeight = BOLD


def _fit_size(width, height):
    if width <= 0 or height <= 0:
        return LOGO_MAX_WIDTH, LOGO_MAX_HEIGHT
    scale = min(float(LOGO_MAX_WIDTH) / width, float(LOGO_MAX_HEIGHT) / height)
    return int(width * scale), int(height * scale)


def replace_logo(ctx, doc, path):
    if not path or not os.path.isfile(path):
        return False
    objects = doc.getGraphicObjects()
    if not objects.hasByName(C.LOGO_OBJECT_NAME):
        return False
    provider = ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.graphic.GraphicProvider", ctx)
    graphic = provider.queryGraphic(props(URL=uno.systemPathToFileUrl(path)))
    if graphic is None:
        return False
    logo = objects.getByName(C.LOGO_OBJECT_NAME)
    logo.Graphic = graphic
    size = graphic.Size100thMM
    width, height = size.Width, size.Height
    if width <= 0 or height <= 0:
        pixels = graphic.SizePixel
        width = int(pixels.Width * 2540 / 96.0)
        height = int(pixels.Height * 2540 / 96.0)
    new_size = logo.Size
    new_size.Width, new_size.Height = _fit_size(width, height)
    logo.Size = new_size
    return True


def set_user_property(doc, name, value):
    udp = doc.getDocumentProperties().getUserDefinedProperties()
    if udp.getPropertySetInfo().hasPropertyByName(name):
        udp.setPropertyValue(name, value)
    else:
        udp.addProperty(name, PROPERTY_REMOVABLE, value)


def get_user_property(doc, name, default=u""):
    try:
        udp = doc.getDocumentProperties().getUserDefinedProperties()
        if udp.getPropertySetInfo().hasPropertyByName(name):
            return udp.getPropertyValue(name)
    except Exception:
        pass
    return default


def is_report_document(doc):
    return bool(get_user_property(doc, C.DOCPROP_MARKER, u""))


def fill_report(ctx, doc, model, settings):
    fields = model["fields"]

    for name, value in fields.items():
        if name in OPTIONAL_FIELDS and not value:
            _delete_bookmark_paragraph(doc, name)
        else:
            weight = BOLD if name == C.BM_REPORT_TITLE else NORMAL
            _set_bookmark_text(doc, name, value, weight)

    _set_bookmark_text(doc, C.BM_SERVICE_NAME,
                       (settings.get("service_name") or u"").strip(), BOLD)
    _set_bookmark_text(doc, C.BM_FOOTER_TICKET, model["ticket"])

    for key in C.TEXT_FIELDS:
        mark = _bookmark(doc, C.SECTION_BOOKMARKS[key])
        if mark is None:
            continue
        section = model["sections"].get(key)
        if not section:
            delete_paragraph_at(mark.getAnchor())
            continue
        paragraphs = [(C.STYLE_SECTION, u"", section["heading"])]
        if section["intro"]:
            paragraphs.append((C.STYLE_INTRO, u"", section["intro"]))
        for item in section["items"]:
            paragraphs.append((C.STYLE_ITEM, item.label, item.text))
        write_paragraphs(mark.getAnchor(), paragraphs)

    mark = _bookmark(doc, C.SECTION_BOOKMARKS["final"])
    if mark is not None:
        final = model["final"]
        if final:
            write_paragraphs(mark.getAnchor(), [
                (C.STYLE_SECTION, u"", final["heading"]),
                (C.STYLE_STATUS, u"", final["text"]),
            ])
        else:
            delete_paragraph_at(mark.getAnchor())

    replace_logo(ctx, doc, settings.get("logo_path"))

    doc.getDocumentProperties().Title = u"%s – %s" % (
        model["title"].capitalize(), model["ticket"])
    set_user_property(doc, C.DOCPROP_MARKER, u"1")
    set_user_property(doc, C.DOCPROP_TICKET, model["ticket"])


def create_report(ctx, model, settings, hidden=False):
    if not os.path.isfile(C.TEMPLATE_FILE):
        raise IOError(u"Nie znaleziono szablonu raportu: %s" % C.TEMPLATE_FILE)
    desktop = ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", ctx)
    url = uno.systemPathToFileUrl(C.TEMPLATE_FILE)
    doc = desktop.loadComponentFromURL(
        url, "_blank", 0, props(AsTemplate=True, Hidden=hidden))
    doc.lockControllers()
    try:
        fill_report(ctx, doc, model, settings)
    finally:
        doc.unlockControllers()
    doc.setModified(True)
    return doc
