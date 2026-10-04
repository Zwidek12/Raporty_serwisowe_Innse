import io
import json
import os
import re
import shutil
import tempfile

from . import constants as C

_INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
_WS_RE = re.compile(r"\s+")
_RESERVED_NAMES = set(
    ["CON", "PRN", "AUX", "NUL"]
    + ["COM%d" % i for i in range(1, 10)]
    + ["LPT%d" % i for i in range(1, 10)])
_VERSION_RE = re.compile(r"^(?P<base>.+)_v(?P<num>\d+)$")


def read_json(path, default=None):
    try:
        with io.open(path, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (IOError, OSError, ValueError):
        return default


def write_json(path, data):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=folder or None)
    try:
        with io.open(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(data, ensure_ascii=False, indent=2))
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def default_output_dir():
    home = os.path.expanduser("~")
    docs = os.path.join(home, "Documents")
    base = docs if os.path.isdir(docs) else home
    return os.path.join(base, C.DEFAULT_OUTPUT_SUBDIR)


def load_settings(user_dir):
    data = read_json(os.path.join(user_dir, C.SETTINGS_FILE_NAME), {}) or {}
    settings = dict(C.DEFAULT_SETTINGS)
    for key, default in C.DEFAULT_SETTINGS.items():
        if key in data and isinstance(data[key], type(default)):
            settings[key] = data[key]
    if settings["default_report_type"] not in C.REPORT_TYPES:
        settings["default_report_type"] = C.DEFAULT_SETTINGS["default_report_type"]
    return settings


def save_settings(user_dir, settings):
    clean = dict(C.DEFAULT_SETTINGS)
    for key in clean:
        if key in settings:
            clean[key] = settings[key]
    write_json(os.path.join(user_dir, C.SETTINGS_FILE_NAME), clean)


def effective_output_dir(settings):
    path = (settings.get("output_dir") or u"").strip()
    return path or default_output_dir()


def is_letterhead_file(path):
    return os.path.splitext(path or u"")[1].lower() in C.LETTERHEAD_EXTENSIONS


def install_letterhead(user_dir, source):
    source = (source or u"").strip()
    if not source:
        return u""
    if not os.path.isfile(source):
        raise IOError(u"Nie znaleziono pliku papieru firmowego:\n%s" % source)
    if not is_letterhead_file(source):
        raise ValueError(u"Nieobsługiwany format papieru firmowego. Dozwolone: %s"
                         % u", ".join(C.LETTERHEAD_EXTENSIONS))
    ext = os.path.splitext(source)[1].lower()
    target = os.path.join(user_dir, C.LETTERHEAD_BASENAME + ext)
    if os.path.normcase(os.path.abspath(source)) == os.path.normcase(
            os.path.abspath(target)):
        return target
    for old_ext in C.LETTERHEAD_EXTENSIONS:
        old = os.path.join(user_dir, C.LETTERHEAD_BASENAME + old_ext)
        if os.path.exists(old):
            os.remove(old)
    shutil.copyfile(source, target)
    return target


def remove_letterhead(user_dir):
    for ext in C.LETTERHEAD_EXTENSIONS:
        old = os.path.join(user_dir, C.LETTERHEAD_BASENAME + ext)
        if os.path.exists(old):
            os.remove(old)


def load_custom_phrases(user_dir):
    data = read_json(os.path.join(user_dir, C.CUSTOM_PHRASES_FILE_NAME), {}) or {}
    phrases = data.get("phrases") if isinstance(data, dict) else None
    result = []
    for entry in phrases or []:
        if (isinstance(entry, dict) and entry.get("title")
                and entry.get("text")):
            result.append({
                "id": entry.get("id") or _make_id(entry["title"]),
                "title": entry["title"],
                "text": entry["text"],
            })
    return result


def save_custom_phrases(user_dir, phrases):
    write_json(os.path.join(user_dir, C.CUSTOM_PHRASES_FILE_NAME),
               {"version": 1, "phrases": phrases})


def _make_id(title):
    slug = re.sub(r"[^0-9a-zA-Z]+", "_", title).strip("_").lower()
    return "custom_" + (slug or "fraza")


def add_custom_phrase(phrases, title, text):
    title = (title or u"").strip()
    text = (text or u"").strip()
    if not title or not text:
        raise ValueError(u"Nazwa i treść frazy nie mogą być puste.")
    result = [p for p in phrases if p["title"] != title]
    ids = set(p["id"] for p in result)
    new_id = base_id = _make_id(title)
    n = 2
    while new_id in ids:
        new_id = "%s_%d" % (base_id, n)
        n += 1
    result.append({"id": new_id, "title": title, "text": text})
    return result


def remove_custom_phrase(phrases, phrase_id):
    return [p for p in phrases if p["id"] != phrase_id]


def sanitize_filename_part(value):
    value = _INVALID_CHARS_RE.sub(u"", value or u"")
    value = _WS_RE.sub(u"_", value.strip())
    value = value.strip(u". _")
    if value.upper() in _RESERVED_NAMES:
        value = u"_" + value
    return value[:100] or u"bez_numeru"


def report_base_name(ticket):
    return u"Raport_" + sanitize_filename_part(ticket)


def versioned_name(base, version):
    return base if version <= 1 else u"%s_v%d" % (base, version)


def _exists_any(folder, name, extensions):
    return any(os.path.exists(os.path.join(folder, name + ext))
               for ext in extensions)


def find_existing(folder, base, extensions):
    return [os.path.join(folder, base + ext) for ext in extensions
            if os.path.exists(os.path.join(folder, base + ext))]


def next_free_version(folder, base, extensions):
    version = 2
    while _exists_any(folder, versioned_name(base, version), extensions):
        version += 1
    return versioned_name(base, version)


def target_paths(folder, name, save_odt=True, export_pdf=True):
    paths = {}
    if save_odt:
        paths["odt"] = os.path.join(folder, name + ".odt")
    if export_pdf:
        paths["pdf"] = os.path.join(folder, name + ".pdf")
    return paths


def selected_extensions(save_odt, export_pdf):
    exts = []
    if save_odt:
        exts.append(".odt")
    if export_pdf:
        exts.append(".pdf")
    return exts
