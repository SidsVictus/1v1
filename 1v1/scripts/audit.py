"""Static scan of shipped code for U2/U3/U4/U11 cheating patterns. Exit 1 on findings."""
import ast, re, sys
from common import *

NET = {"socket", "requests", "httpx", "aiohttp", "urllib3", "http.client", "ftplib", "smtplib", "urllib.request"}
MOCK = {"unittest.mock", "mock", "pytest_mock"}
SUPPRESS = re.compile(r"#\s*(type:\s*ignore|noqa|pylint:\s*disable|pragma:\s*no cover)")
TODO = re.compile(r"#.*\b(TODO|FIXME|XXX|HACK)\b")


def allowed(name):
    p = ROOT / ".1v1" / name
    return set(p.read_text().split()) if p.exists() else set()


def trivial(fn):
    body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant) and isinstance(s.value.value, str))]
    if not body: return True
    if len(body) == 1:
        s = body[0]
        if isinstance(s, ast.Pass): return True
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is Ellipsis: return True
        if isinstance(s, ast.Raise) and "NotImplementedError" in ast.dump(s): return True
    return False


def exempt(fn):
    d = " ".join(ast.dump(x) for x in fn.decorator_list)
    return "abstractmethod" in d or "overload" in d


def scan(r, net_ok, ign_ok):
    out, src = [], (ROOT / r).read_text(errors="ignore")
    try: tree = ast.parse(src)
    except SyntaxError as e: return [f"{r}: syntax error {e}"]
    for i, line in enumerate(src.splitlines(), 1):
        if SUPPRESS.search(line) and r not in ign_ok: out.append(f"{r}:{i} U4 suppression comment")
        if TODO.search(line): out.append(f"{r}:{i} U3 TODO/FIXME")
        if re.search(r"PYTEST_CURRENT_TEST|sys\.modules.*pytest|['\"]pytest['\"] in sys", line): out.append(f"{r}:{i} U2 detects test runner")
    protocol = {c.name for c in ast.walk(tree) if isinstance(c, ast.ClassDef) and any(b in ast.dump(x) for x in c.bases for b in ("Protocol", "ABC"))}
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
            for m in mods:
                if any(m == x or m.startswith(x + ".") for x in MOCK): out.append(f"{r}:{n.lineno} U3 mock import {m}")
                if any(m == x or m.startswith(x + ".") for x in NET) and r not in net_ok: out.append(f"{r}:{n.lineno} U11 network import {m}")
        if isinstance(n, ast.ExceptHandler):
            broad = n.type is None or (isinstance(n.type, ast.Name) and n.type.id in ("Exception", "BaseException"))
            silent = all(isinstance(s, (ast.Pass, ast.Continue)) or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)) for s in n.body)
            if n.type is None: out.append(f"{r}:{n.lineno} U4 bare except")
            elif broad and silent: out.append(f"{r}:{n.lineno} U4 swallowed exception")
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and trivial(n) and not exempt(n):
            if not (n.name.startswith("__") and n.name.endswith("__")):
                out.append(f"{r}:{n.lineno} U3 stub body in {n.name}")
    return out


if __name__ == "__main__":
    net_ok, ign_ok = allowed("allow-network.txt"), allowed("allow-ignores.txt")
    res = [f for r in walk() if is_source(r) for f in scan(r, net_ok, ign_ok)]
    print("\n".join(res) if res else "clean")
    sys.exit(1 if res else 0)
