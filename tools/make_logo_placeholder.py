import os
import struct
import zlib

WIDTH, HEIGHT = 450, 180
SCALE = 10
BG = (245, 246, 248)
BORDER = (170, 176, 186)
INK = (150, 156, 166)

GLYPHS = {
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
}
TEXT = "LOGO"


def build_pixels():
    px = [[BG for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for x in range(WIDTH):
        for t in range(3):
            px[t][x] = BORDER
            px[HEIGHT - 1 - t][x] = BORDER
    for y in range(HEIGHT):
        for t in range(3):
            px[y][t] = BORDER
            px[y][WIDTH - 1 - t] = BORDER
    text_w = (len(TEXT) * 6 - 1) * SCALE
    x0 = (WIDTH - text_w) // 2
    y0 = (HEIGHT - 7 * SCALE) // 2
    for i, ch in enumerate(TEXT):
        for gy, row in enumerate(GLYPHS[ch]):
            for gx, bit in enumerate(row):
                if bit != "1":
                    continue
                for dy in range(SCALE):
                    for dx in range(SCALE):
                        px[y0 + gy * SCALE + dy][x0 + (i * 6 + gx) * SCALE + dx] = INK
    return px


def write_png(path, px):
    raw = b"".join(b"\x00" + bytes(c for p in row for c in p) for row in px)

    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
    png += chunk(b"pHYs", struct.pack(">IIB", 11811, 11811, 1))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(root, "resources", "logo_placeholder.png")
    write_png(target, build_pixels())
    print("Zapisano", target)
