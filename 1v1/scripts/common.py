"""Shared helpers. State lives OUTSIDE the project so agents cannot edit it."""
import hashlib, os, pathlib, re, tempfile

ROOT = pathlib.Path(os.environ.get("ONEV1_ROOT", os.getcwd())).resolve()
STATE = pathlib.Path(tempfile.gettempdir()) / ("1v1-" + hashlib.sha256(str(ROOT).encode()).hexdigest()[:12])
SKIP = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".mypy_cache",
        ".ruff_cache", ".pytest_cache", "site-packages", ".tox", ".hypothesis", ".egg-info"}
PROT_NAMES = {"conftest.py", "pytest.ini", "tox.ini", "setup.cfg", "mypy.ini", "ruff.toml",
              ".ruff.toml", "pyproject.toml", "verify", "verify-fast", "Makefile", "noxfile.py",
              ".gitlab-ci.yml", ".pre-commit-config.yaml", "CLAUDE.md"}
PROT_TOP = {"tests", "test", ".1v1", ".github", ".claude"}
HIDDEN = [".1v1/questions.md", ".1v1/holdout"]  # hidden from builder, outside manifest


def is_hidden(r):
    return any(r == h or r.startswith(h + "/") for h in HIDDEN)


def is_protected(r):
    parts = r.split("/")
    name = parts[-1]
    return (parts[0] in PROT_TOP or any(p in ("tests", "test") for p in parts[:-1])
            or name in PROT_NAMES or re.fullmatch(r"test_.*\.py|.*_test\.py", name) is not None)


def is_source(r):
    return r.endswith(".py") and not is_protected(r)


def walk():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP and not d.endswith(".egg-info")]
        for f in fns:
            yield (pathlib.Path(dp) / f).relative_to(ROOT).as_posix()


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def rel(p):
    try:
        return pathlib.Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None
