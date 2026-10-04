import io
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT_DIR = os.path.join(ROOT, "extension")
DIST_DIR = os.path.join(ROOT, "dist")
OXT_NAME = "ServiceReport.oxt"

REQUIRED_RESOURCES = ("report_template.ott", "phrases_default.json")


def version():
    with io.open(os.path.join(ROOT, "report_generator", "__init__.py"),
                 encoding="utf-8") as fh:
        return re.search(r'__version__\s*=\s*"([^"]+)"', fh.read()).group(1)


def add_tree(zf, src_dir, arc_prefix, patterns=None):
    for base, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in sorted(files):
            if patterns and not any(name.endswith(p) for p in patterns):
                continue
            full = os.path.join(base, name)
            rel = os.path.relpath(full, src_dir).replace(os.sep, "/")
            zf.write(full, arc_prefix + rel)


def build():
    for res in REQUIRED_RESOURCES:
        if not os.path.isfile(os.path.join(ROOT, "resources", res)):
            sys.exit("Brak pliku resources/%s – uruchom najpierw "
                     "tools/build_template.py" % res)
    if not os.path.isdir(DIST_DIR):
        os.makedirs(DIST_DIR)
    target = os.path.join(DIST_DIR, OXT_NAME)
    ver = version()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        with io.open(os.path.join(EXT_DIR, "description.xml"),
                     encoding="utf-8") as fh:
            zf.writestr("description.xml",
                        fh.read().replace("@VERSION@", ver).encode("utf-8"))
        for name in ("META-INF/manifest.xml", "Addons.xcu",
                     "ServiceReport.components", "service_report_job.py",
                     "description-pl.txt"):
            zf.write(os.path.join(EXT_DIR, *name.split("/")), name)
        add_tree(zf, os.path.join(ROOT, "report_generator"),
                 "pythonpath/report_generator/", (".py",))
        add_tree(zf, os.path.join(ROOT, "resources"), "resources/")
        add_tree(zf, os.path.join(ROOT, "docs"), "docs/", (".md",))
    print("Zbudowano %s (wersja %s)" % (target, ver))
    return target


if __name__ == "__main__":
    build()
