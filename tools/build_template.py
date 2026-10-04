import os
import sys

import uno
from com.sun.star.awt.FontSlant import ITALIC
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.lang import Locale
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT
from com.sun.star.table import BorderLine2
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.lo_session import Session
from report_generator import constants as C

FONT = "Liberation Sans"
COLOR_ACCENT = 0x1F3864
COLOR_TEXT = 0x1A1A1A
COLOR_MUTED = 0x6B7280
COLOR_STATUS_BG = 0xEEF2F8
PAGE_W, PAGE_H = 21000, 29700
MARGIN_LR, MARGIN_TB = 1800, 1500
TEXT_W = PAGE_W - 2 * MARGIN_LR


def pv(name, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


def line(color, width):
    b = BorderLine2()
    b.Color = color
    b.LineWidth = width
    b.OuterLineWidth = width
    return b


def set_props(obj, **kwargs):
    for key, value in kwargs.items():
        obj.setPropertyValue(key, value)


def setup_page(doc):
    page = doc.getStyleFamilies().getByName("PageStyles").getByName("Standard")
    set_props(page, Width=PAGE_W, Height=PAGE_H,
              LeftMargin=MARGIN_LR, RightMargin=MARGIN_LR,
              TopMargin=MARGIN_TB, BottomMargin=1200,
              HeaderIsOn=False, FooterIsOn=True,
              HeaderBodyDistance=600, FooterBodyDistance=400,
              HeaderIsDynamicHeight=True, FooterIsDynamicHeight=True)
    return page


def base_char_props(style, size=10.5):
    loc = Locale("pl", "PL", "")
    set_props(style, CharFontName=FONT, CharFontNameAsian=FONT,
              CharFontNameComplex=FONT, CharHeight=size, CharColor=COLOR_TEXT,
              CharLocale=loc)


def setup_list_style(doc):
    styles = doc.getStyleFamilies().getByName("NumberingStyles")
    style = doc.createInstance("com.sun.star.style.NumberingStyle")
    styles.insertByName(C.LIST_STYLE, style)
    rules = style.NumberingRules
    level = list(rules.getByIndex(0))
    values = {
        "NumberingType": 6,
        "BulletChar": u"\u2022",
        "PositionAndSpaceMode": 1,
        "LabelFollowedBy": 0,
        "ListtabStopPosition": 900,
        "FirstLineIndent": -450,
        "IndentAt": 900,
        "BulletColor": COLOR_ACCENT,
        "BulletRelSize": 100,
    }
    names = [p.Name for p in level]
    for key, value in values.items():
        if key in names:
            level[names.index(key)].Value = value
        else:
            level.append(pv(key, value))
    font_idx = names.index("BulletFont") if "BulletFont" in names else -1
    if font_idx >= 0:
        font = level[font_idx].Value
        font.Name = FONT
        level[font_idx].Value = font
    uno.invoke(rules, "replaceByIndex",
               (0, uno.Any("[]com.sun.star.beans.PropertyValue", tuple(level))))
    style.NumberingRules = rules


def para_style(doc, name, parent="Standard", **kwargs):
    styles = doc.getStyleFamilies().getByName("ParagraphStyles")
    if styles.hasByName(name):
        style = styles.getByName(name)
    else:
        style = doc.createInstance("com.sun.star.style.ParagraphStyle")
        styles.insertByName(name, style)
    style.ParentStyle = parent
    style.FollowStyle = name
    spacing = uno.createUnoStruct("com.sun.star.style.LineSpacing")
    spacing.Mode = 0
    spacing.Height = 100
    defaults = dict(CharHeight=10.5, CharColor=COLOR_TEXT, ParaTopMargin=0,
                    ParaBottomMargin=0, ParaLeftMargin=0, ParaRightMargin=0,
                    ParaFirstLineIndent=0, ParaLineSpacing=spacing,
                    ParaAdjust=LEFT, ParaOrphans=2, ParaWidows=2)
    if kwargs.get("NumberingStyleName"):
        for key in ("ParaLeftMargin", "ParaFirstLineIndent"):
            defaults.pop(key)
    defaults.update(kwargs)
    set_props(style, **defaults)
    return style


def setup_styles(doc):
    pstyles = doc.getStyleFamilies().getByName("ParagraphStyles")
    standard = pstyles.getByName("Standard")
    base_char_props(standard)
    set_props(standard, ParaOrphans=2, ParaWidows=2, ParaTopMargin=0,
              ParaBottomMargin=0)

    setup_list_style(doc)

    para_style(doc, C.STYLE_BODY, ParaBottomMargin=150)
    para_style(doc, C.STYLE_TITLE, CharHeight=16.0, CharWeight=BOLD,
               CharColor=COLOR_ACCENT, ParaAdjust=CENTER, ParaTopMargin=100,
               ParaBottomMargin=450, ParaKeepTogether=True)
    para_style(doc, C.STYLE_META, ParaBottomMargin=60)
    para_style(doc, C.STYLE_META_HEAD, CharWeight=BOLD, ParaTopMargin=200,
               ParaBottomMargin=80, ParaKeepTogether=True)
    para_style(doc, C.STYLE_DEVICE_ITEM, ParaBottomMargin=50,
               NumberingStyleName=C.LIST_STYLE)
    sec = para_style(doc, C.STYLE_SECTION, CharHeight=12.0, CharWeight=BOLD,
                     CharColor=COLOR_ACCENT, ParaTopMargin=500,
                     ParaBottomMargin=200, ParaKeepTogether=True,
                     ParaSplit=False, BottomBorderDistance=60)
    sec.BottomBorder = line(0xB4BCCB, 18)
    para_style(doc, C.STYLE_INTRO, ParaBottomMargin=150,
               ParaKeepTogether=True, CharPosture=ITALIC)
    para_style(doc, C.STYLE_ITEM, ParaBottomMargin=90,
               NumberingStyleName=C.LIST_STYLE, ParaAdjust=LEFT)
    status = para_style(doc, C.STYLE_STATUS, ParaBottomMargin=100,
                        ParaBackColor=COLOR_STATUS_BG, ParaBackTransparent=False,
                        LeftBorderDistance=250, RightBorderDistance=200,
                        TopBorderDistance=150, BottomBorderDistance=150,
                        CharWeight=BOLD, ParaSplit=False)
    status.LeftBorder = line(COLOR_ACCENT, 70)


def run(text, cur, value, bold=False, bookmark=None, doc=None, weight=True):
    text.insertString(cur, value, False)
    sel = text.createTextCursorByRange(cur.getEnd())
    sel.goLeft(len(value.encode("utf-16-le")) // 2, True)
    if weight:
        sel.CharWeight = BOLD if bold else NORMAL
    if bookmark:
        mark = doc.createInstance("com.sun.star.text.Bookmark")
        mark.setName(bookmark)
        text.insertTextContent(sel, mark, True)


def placeholder(name):
    return u"\u00ab%s\u00bb" % name


def new_par(text, cur, style, first=False):
    if not first:
        text.insertControlCharacter(cur, PARAGRAPH_BREAK, False)
    cur.ParaStyleName = style


def build_body(doc):
    text = doc.getText()
    cur = text.createTextCursor()

    new_par(text, cur, C.STYLE_TITLE, first=True)
    run(text, cur, placeholder(C.BM_REPORT_TITLE), True, C.BM_REPORT_TITLE, doc)

    for label, bm in ((u"Data sporządzenia: ", C.BM_REPORT_DATE),
                      (u"Numer zgłoszenia: ", C.BM_TICKET_NUMBER),
                      (u"Data przyjęcia: ", C.BM_RECEIPT_DATE),
                      (u"Serwis / technik: ", C.BM_TECHNICIAN)):
        new_par(text, cur, C.STYLE_META)
        run(text, cur, label, True)
        run(text, cur, placeholder(bm), False, bm, doc)

    new_par(text, cur, C.STYLE_META_HEAD)
    run(text, cur, u"Dane urządzenia:", True)

    new_par(text, cur, C.STYLE_DEVICE_ITEM)
    run(text, cur, u"Producent / Model: ", True)
    run(text, cur, placeholder(C.BM_DEVICE_MANUFACTURER), False,
        C.BM_DEVICE_MANUFACTURER, doc)
    run(text, cur, u" ")
    run(text, cur, placeholder(C.BM_DEVICE_MODEL), False, C.BM_DEVICE_MODEL, doc)

    for label, bm in ((u"Numer seryjny: ", C.BM_DEVICE_SERIAL),
                      (u"Rodzaj urządzenia: ", C.BM_DEVICE_TYPE),
                      (u"Status: ", C.BM_DEVICE_STATUS)):
        new_par(text, cur, C.STYLE_DEVICE_ITEM)
        run(text, cur, label, True)
        run(text, cur, placeholder(bm), False, bm, doc)

    for bm in (C.BM_SECTION_CUSTOMER, C.BM_SECTION_DIAGNOSIS, C.BM_SECTION_WORK,
               C.BM_SECTION_TESTS, C.BM_FINAL_STATUS):
        new_par(text, cur, C.STYLE_BODY)
        run(text, cur, placeholder(bm), False, bm, doc, weight=False)

    new_par(text, cur, C.STYLE_BODY)
    mark = doc.createInstance("com.sun.star.text.Bookmark")
    mark.setName(C.BM_REPORT_END)
    text.insertTextContent(cur, mark, False)


def build_footer(doc, page):
    text = page.FooterText
    cur = text.createTextCursor()
    cur.ParaAdjust = CENTER
    cur.TopBorder = line(0xC8CDD6, 9)
    cur.TopBorderDistance = 100
    run(text, cur, u"Raport serwisowy – zgłoszenie nr ")
    run(text, cur, placeholder(C.BM_FOOTER_TICKET), False, C.BM_FOOTER_TICKET, doc)
    run(text, cur, u"   |   Strona ")
    num = doc.createInstance("com.sun.star.text.TextField.PageNumber")
    num.NumberingType = 4
    num.SubType = uno.Enum("com.sun.star.text.PageNumberType", "CURRENT")
    text.insertTextContent(cur, num, False)
    run(text, cur, u" z ")
    count = doc.createInstance("com.sun.star.text.TextField.PageCount")
    count.NumberingType = 4
    text.insertTextContent(cur, count, False)
    sel = text.createTextCursorByRange(text.getStart())
    sel.gotoEnd(True)
    sel.CharFontName = FONT
    sel.CharHeight = 8.5
    sel.CharColor = COLOR_MUTED


def build(ctx, desktop, target):
    doc = desktop.loadComponentFromURL(
        "private:factory/swriter", "_blank", 0, (pv("Hidden", True),))
    try:
        setup_styles(doc)
        page = setup_page(doc)
        build_body(doc)
        build_footer(doc, page)
        info = doc.getDocumentProperties()
        info.Title = u"Szablon raportu serwisowego"
        info.Language = Locale("pl", "PL", "")
        if os.path.exists(target):
            os.remove(target)
        doc.storeToURL(uno.systemPathToFileUrl(target),
                       (pv("FilterName", "writer8_template"),))
    finally:
        doc.close(True)


def main():
    with Session() as session:
        build(session.ctx, session.desktop, C.TEMPLATE_FILE)
    print("Zapisano", C.TEMPLATE_FILE)


if __name__ == "__main__":
    main()
