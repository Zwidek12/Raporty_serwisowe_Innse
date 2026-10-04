import re

_WS_RE = re.compile(r"\s+")
_BULLET_RE = re.compile(r"^[•‣●▪\-\*–—]\s+")


class Item(object):
    __slots__ = ("label", "text")

    def __init__(self, label, text):
        self.label = label or ""
        self.text = text or ""

    @property
    def has_label(self):
        return bool(self.label)

    def as_line(self):
        if self.label:
            return u"%s: %s" % (self.label, self.text)
        return self.text

    def __eq__(self, other):
        return (isinstance(other, Item) and self.label == other.label
                and self.text == other.text)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "Item(%r, %r)" % (self.label, self.text)


def normalize_spaces(value):
    if not value:
        return u""
    return _WS_RE.sub(u" ", value).strip()


def parse_line(line):
    line = normalize_spaces(line)
    if not line:
        return None
    line = _BULLET_RE.sub(u"", line)
    if not line:
        return None
    if u"/" not in line:
        return Item(u"", line)
    label, text = line.split(u"/", 1)
    label = normalize_spaces(label).rstrip(u":").rstrip()
    text = normalize_spaces(text)
    if not label and not text:
        return None
    if not label:
        return Item(u"", text)
    if not text:
        return Item(u"", label)
    return Item(label, text)


def split_lines(value):
    if not value:
        return []
    return value.replace(u"\r\n", u"\n").replace(u"\r", u"\n").split(u"\n")


def parse_block(value):
    items = []
    for line in split_lines(value):
        item = parse_line(line)
        if item is not None:
            items.append(item)
    return items


def append_line(current, line):
    current = current or u""
    line = (line or u"").strip()
    if not line:
        return current
    stripped = current.rstrip(u"\r\n \t")
    if not stripped.strip():
        return line
    return stripped + u"\n" + line
