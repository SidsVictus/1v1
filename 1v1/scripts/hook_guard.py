"""Claude Code PreToolUse hook. Blocks (exit 2) forbidden actions for the active role. First line of defence; guard.py is the backstop."""
import json, re, shlex, sys
from common import *

role_f = STATE / "role"
role = role_f.read_text().strip() if role_f.exists() else ""
if role not in ("builder", "breaker"): sys.exit(0)
d = json.load(sys.stdin)
tool, ti = d.get("tool_name", ""), d.get("tool_input", {}) or {}
WRITE = re.compile(r"(^|[\s;&|(])(sed\s+-i|tee|mv|cp|rm|truncate|touch|chmod|dd|ln|install|patch|git\s+(apply|checkout|restore|reset|clean|stash|commit|rm|mv|add))\b")
DESTR = re.compile(r"\brm\s+-\w*r|git\s+(reset|clean|stash)|shutil\.rmtree|os\.remove|os\.unlink")


def block(msg): print(f"1v1 guard ({role}): {msg}", file=sys.stderr); sys.exit(2)


def has_write(cmd): return bool(WRITE.search(cmd)) or bool(re.search(r"[^2&]>|>>", re.sub(r"\d?>\s*&\d|>\s*/dev/null", "", cmd)))


def paths(cmd):
    try: toks = shlex.split(cmd)
    except ValueError: toks = cmd.split()
    return [t for t in toks if "/" in t or t.endswith((".py", ".toml", ".ini", ".md", ".cfg"))]


def norm(p):
    r = rel(p)
    if r is not None: return r
    p = str(p)
    return p[2:] if p.startswith("./") else p


def okbreaker(r): return r is not None and r.startswith((".1v1/breaker/", ".1v1/holdout/"))


path = ti.get("file_path") or ti.get("path") or ti.get("notebook_path")
if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit") and path:
    r = rel(path)
    if str(STATE) in str(path): block("state dir is off limits")
    if role == "builder" and r is not None and is_protected(r): block(f"{r} is protected")
    if role == "breaker" and not okbreaker(r): block("breaker may write only in .1v1/breaker/ or .1v1/holdout/")
elif tool in ("Read", "Glob", "Grep"):
    p = path or ti.get("pattern", "")
    if str(STATE) in str(p): block("state dir is off limits")
    if role == "builder" and norm(p).startswith(".1v1"): block(".1v1 is off limits")
elif tool == "Bash":
    cmd = ti.get("command", "")
    if str(STATE) in cmd: block("state dir is off limits")
    if DESTR.search(cmd): block("destructive command needs user approval via the orchestrator")
    if role == "builder":
        if ".1v1" in cmd: block(".1v1 is off limits")
        if has_write(cmd) and any(is_protected(norm(p)) for p in paths(cmd)): block("write to a protected path")
    if role == "breaker" and has_write(cmd) and not all(okbreaker(norm(p)) for p in paths(cmd)):
        block("breaker may write only in .1v1/breaker/ or .1v1/holdout/")
sys.exit(0)
