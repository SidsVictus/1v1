"""Find (or create) the one-command check. Usage: find_check.py [--create]"""
import importlib.util, os, re, stat, sys
from common import *


def find():
    if (ROOT / "verify").exists(): return "./verify"
    mk = ROOT / "Makefile"
    if mk.exists():
        for t in ("check", "test", "verify"):
            if re.search(rf"^{t}:", mk.read_text(), re.M): return f"make {t}"
    if (ROOT / "noxfile.py").exists(): return "nox"
    if (ROOT / "tox.ini").exists(): return "tox"
    if (ROOT / "pytest.ini").exists() or "[tool.pytest" in (ROOT / "pyproject.toml").read_text() if (ROOT / "pyproject.toml").exists() else False: return "python -m pytest -q"
    return None


def create():
    missing = [m for m in ("pytest", "mypy", "ruff", "hypothesis") if importlib.util.find_spec(m) is None]
    if missing: print("MISSING TOOLS (ask user to install): " + ", ".join(missing)); return None
    p = ROOT / "verify"
    p.write_text("#!/usr/bin/env bash\nset -euo pipefail\npython -m pytest -q\npython -m mypy .\npython -m ruff check .\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return "./verify"


if __name__ == "__main__":
    c = find()
    if not c and "--create" in sys.argv: c = create()
    if not c: print("NO CHECK COMMAND"); sys.exit(1)
    print(c)
