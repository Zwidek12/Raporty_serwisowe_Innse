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

    doc.getDocumentProperties().Title = u"%s – %s" % (
        model["title"].capitalize(), model["ticket"])
    set_user_property(doc, C.DOCPROP_MARKER, u"1")
    set_user_property(doc, C.DOCPROP_TICKET, model["ticket"])


def letterhead_path(settings):
    path = (settings.get("letterhead_path") or u"").strip()
    return path if path and os.path.isfile(path) else u""


def _has_anchored_content(paragraph):
    try:
        return paragraph.createContentEnumeration(
            "com.sun.star.text.TextContent").hasMoreElements()
    except Exception:
        return False


def _paragraphs(text):
    result = []
    enum = text.createEnumeration()
    while enum.hasMoreElements():
        result.append(enum.nextElement())
    return result


def _remove_end_marker(doc):
    mark = _bookmark(doc, C.BM_REPORT_END)
    if mark is None:
        return
    anchor = mark.getAnchor()
    cursor = anchor.getText().createTextCursorByRange(anchor)
    cursor.gotoStartOfParagraph(False)
    cursor.gotoEndOfParagraph(True)
    if cursor.getString().strip():
        return
    for para in _paragraphs(doc.getText()):
        if (para.supportsService("com.sun.star.text.Paragraph")
                and doc.getText().compareRegionStarts(para.getStart(),
                                                      cursor.getStart()) == 0):
            if _has_anchored_content(para):
                return
            break
    doc.getText().removeTextContent(mark)
    delete_paragraph_at(cursor)


def _collapse_paragraph(para):
    spacing = uno.createUnoStruct("com.sun.star.style.LineSpacing")
    spacing.Mode = 3
    spacing.Height = 10
    para.ParaTopMargin = 0
    para.ParaBottomMargin = 0
    para.ParaLineSpacing = spacing
    para.CharHeight = 1.0


def insert_report_body(doc, template_url):
    text = doc.getText()
    page_style = text.createTextCursorByRange(text.getStart()).PageStyleName
    original = _paragraphs(text)
    body_empty = all(p.supportsService("com.sun.star.text.Paragraph")
                     and not p.getString().strip() for p in original)
    cursor = text.createTextCursorByRange(text.getEnd())
    text.insertControlCharacter(cursor, PARAGRAPH_BREAK, False)
    cursor.insertDocumentFromURL(template_url, ())
    if body_empty:
        for para in reversed(original):
            if _has_anchored_content(para):
                _collapse_paragraph(para)
            else:
                delete_paragraph_at(para)
    first = text.createTextCursorByRange(text.getStart())
    if page_style and first.PageStyleName != page_style:
        first.PageDescName = page_style


def create_report(ctx, model, settings, hidden=False):
    if not os.path.isfile(C.TEMPLATE_FILE):
        raise IOError(u"Nie znaleziono szablonu raportu: %s" % C.TEMPLATE_FILE)
    desktop = ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", ctx)
    template_url = uno.systemPathToFileUrl(C.TEMPLATE_FILE)
    letterhead = letterhead_path(settings)
    base_url = uno.systemPathToFileUrl(letterhead) if letterhead else template_url
    doc = desktop.loadComponentFromURL(
        base_url, "_blank", 0, props(AsTemplate=True, Hidden=hidden))
    if doc is None:
        raise IOError(u"Nie udało się otworzyć pliku: %s" % (letterhead or C.TEMPLATE_FILE))
    doc.lockControllers()
    try:
        if letterhead:
            insert_report_body(doc, template_url)
        fill_report(ctx, doc, model, settings)
        _remove_end_marker(doc)
    finally:
        doc.unlockControllers()
    doc.setModified(True)
    return doc
