import os
import struct
import sys
import zlib

import uno
from com.sun.star.awt import Point, Size
from com.sun.star.awt.FontWeight import BOLD
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.lo_session import Session

ACCENT = 0xB3261E


def pv(name, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


def make_png(path, width, height, color):
    r, g, b = (color >> 16) & 255, (color >> 8) & 255, color & 255
    raw = b"".join(b"\x00" + bytes((r, g, b)) * width for _ in range(height))

    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n"
                 + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def build(ctx, desktop, out_dir):
    png = os.path.join(out_dir, "_znak.png")
    make_png(png, 120, 120, ACCENT)
    doc = desktop.loadComponentFromURL("private:factory/swriter", "_blank", 0,
                                       (pv("Hidden", True),))
    page = doc.getStyleFamilies().getByName("PageStyles").getByName("Standard")
    page.TopMargin = 1200
    page.BottomMargin = 1000
    page.LeftMargin = 2500
    page.RightMargin = 2000
    page.HeaderIsOn = True
    page.FooterIsOn = True
    page.HeaderBodyDistance = 800

    header = page.HeaderText
    cur = header.createTextCursor()
    provider = ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.graphic.GraphicProvider", ctx)
    graphic = provider.queryGraphic((pv("URL", uno.systemPathToFileUrl(png)),))
    img = doc.createInstance("com.sun.star.text.TextGraphicObject")
    img.Graphic = graphic
    img.AnchorType = uno.Enum("com.sun.star.text.TextContentAnchorType", "AS_CHARACTER")
    header.insertTextContent(cur, img, False)
    img.Size = Size(1400, 1400)
    header.insertString(cur, u"  PRZYKŁADOWA FIRMA SERWISOWA Sp. z o.o.", False)
    sel = header.createTextCursorByRange(header.getStart())
    sel.gotoEnd(True)
    sel.CharWeight = BOLD
    sel.CharHeight = 15.0
    sel.CharColor = ACCENT
    header.insertControlCharacter(cur, PARAGRAPH_BREAK, False)
    cur.ParaAdjust = RIGHT
    header.insertString(cur, u"Autoryzowany serwis RTV / AGD / IT • www.przyklad.pl", False)
    sel = header.createTextCursorByRange(cur)
    sel.gotoStartOfParagraph(True)
    sel.CharWeight = 100.0
    sel.CharHeight = 9.0
    sel.CharColor = 0x555555

    footer = page.FooterText
    fcur = footer.createTextCursor()
    fcur.ParaAdjust = CENTER
    footer.insertString(fcur, u"ul. Przykładowa 12, 00-001 Warszawa  |  NIP 000-000-00-00  |  "
                              u"tel. +48 000 000 000  |  serwis@przyklad.pl", False)
    sel = footer.createTextCursorByRange(footer.getStart())
    sel.gotoEnd(True)
    sel.CharHeight = 8.0
    sel.CharColor = ACCENT

    text = doc.getText()
    tcur = text.createTextCursor()
    for _ in range(3):
        text.insertControlCharacter(tcur, PARAGRAPH_BREAK, False)

    band = doc.createInstance("com.sun.star.drawing.RectangleShape")
    band.AnchorType = uno.Enum("com.sun.star.text.TextContentAnchorType", "AT_PAGE")
    band.AnchorPageNo = 1
    doc.getDrawPage().add(band)
    band.Size = Size(600, 29700)
    band.Position = Point(0, 0)
    band.FillColor = ACCENT
    band.LineStyle = uno.Enum("com.sun.star.drawing.LineStyle", "NONE")
    band.Opaque = False
    band.TextWrap = uno.Enum("com.sun.star.text.WrapTextMode", "THROUGH")

    result = []
    for ext, filt in ((".odt", "writer8"), (".docx", "MS Word 2007 XML")):
        target = os.path.join(out_dir, "papier_test" + ext)
        doc.storeToURL(uno.systemPathToFileUrl(target), (pv("FilterName", filt),))
        result.append(target)
    doc.close(True)
    os.remove(png)
    return result


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with Session() as s:
        for path in build(s.ctx, s.desktop, out_dir):
            print("Zapisano", path)


if __name__ == "__main__":
    main()
