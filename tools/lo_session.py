import os
import subprocess
import sys
import tempfile
import time
import uuid

import uno
from com.sun.star.connection import NoConnectException

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)


def _soffice_path():
    program_dir = os.path.dirname(sys.executable)
    for name in ("soffice.exe", "soffice.bin", "soffice"):
        cand = os.path.join(program_dir, name)
        if os.path.exists(cand):
            return cand
    return "soffice"


class Session(object):
    def __init__(self):
        self.pipe = "rg_" + uuid.uuid4().hex[:12]
        self.profile = os.path.join(tempfile.gettempdir(), "rg_lo_profile")
        self.proc = None
        self.ctx = None

    def __enter__(self):
        profile_url = uno.systemPathToFileUrl(self.profile)
        self.proc = subprocess.Popen([
            _soffice_path(), "--headless", "--invisible", "--nologo",
            "--norestore", "--nodefault", "--nolockcheck",
            "-env:UserInstallation=" + profile_url,
            "--accept=pipe,name=%s;urp;StarOffice.ComponentContext" % self.pipe,
        ])
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local)
        url = ("uno:pipe,name=%s;urp;StarOffice.ComponentContext" % self.pipe)
        for _ in range(120):
            try:
                self.ctx = resolver.resolve(url)
                break
            except NoConnectException:
                time.sleep(0.5)
        if self.ctx is None:
            raise RuntimeError("Nie udało się połączyć z LibreOffice.")
        return self

    @property
    def desktop(self):
        return self.ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.ctx)

    def __exit__(self, *exc):
        try:
            self.desktop.terminate()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=30)
        except Exception:
            self.proc.kill()
        return False
