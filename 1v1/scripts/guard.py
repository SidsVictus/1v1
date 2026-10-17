"""Tamper guard. Usage: guard.py init | check [--role builder|breaker] [--revert] | hide | reveal | role NAME"""
import json, shutil, sys
from common import *

MAN = STATE / "manifest.json"
COPIES = STATE / "files"
HID = STATE / "hidden"


def scan():
    return {r: sha(ROOT / r) for r in walk() if not is_hidden(r)}


def init():
    if COPIES.exists():
        shutil.rmtree(COPIES)
    STATE.mkdir(parents=True, exist_ok=True)
    cur = scan()
    for r in cur:
        d = COPIES / r
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / r, d)
    MAN.write_text(json.dumps(cur))
    print(f"snapshot: {len(cur)} files")


def check(role, revert):
    if not MAN.exists():
        print("ERROR: no snapshot; run init"); return 2
    old, new, bad = json.loads(MAN.read_text()), scan(), []
    for r, h in old.items():
        if r not in new:
            if is_protected(r) or role == "breaker": bad.append(("deleted", r))
        elif new[r] != h and (is_protected(r) or role == "breaker"):
            bad.append(("modified", r))
    for r in new:
        if r in old: continue
        if role == "breaker" and not r.startswith((".1v1/breaker/", ".1v1/holdout/")):
            bad.append(("added", r))
        elif role == "builder" and is_protected(r):
            bad.append(("added", r))
    for kind, r in bad:
        print(f"VIOLATION {kind}: {r}")
        if revert:
            if kind == "added": (ROOT / r).unlink(missing_ok=True)
            else:
                (ROOT / r).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(COPIES / r, ROOT / r)
    print("clean" if not bad else f"{len(bad)} violation(s)" + (" (reverted)" if revert else ""))
    return 1 if bad else 0


def move(src_root, dst_root):
    for h in HIDDEN:
        s, d = src_root / h, dst_root / h
        if s.exists():
            d.parent.mkdir(parents=True, exist_ok=True)
            if d.exists(): shutil.rmtree(d) if d.is_dir() else d.unlink()
            shutil.move(str(s), str(d))


if __name__ == "__main__":
    a = sys.argv[1:] or ["-h"]
    if a[0] == "init": init()
    elif a[0] == "check":
        role = a[a.index("--role") + 1] if "--role" in a else "builder"
        sys.exit(check(role, "--revert" in a))
    elif a[0] == "hide": move(ROOT, HID); print("hidden")
    elif a[0] == "reveal": move(HID, ROOT); print("revealed")
    elif a[0] == "role":
        STATE.mkdir(parents=True, exist_ok=True); (STATE / "role").write_text(a[1]); print("role", a[1])
    else: print(__doc__); sys.exit(2)
