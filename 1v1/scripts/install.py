"""One-time setup in the target project (run from the project root).

  python "<skill>/scripts/install.py" --dry-run     show what would change, change nothing
  python "<skill>/scripts/install.py"               install agents + blocking hook
  python "<skill>/scripts/install.py" --uninstall   remove hook + agents, restore backed-up files
  python "<skill>/scripts/install.py" --uninstall --purge   also remove .1v1/, verify (if 1v1 made it), CLAUDE.md block

Changes made by install:
  1. .claude/settings.json: adds ONE PreToolUse hook entry (hook_guard.py). Other settings untouched.
  2. .claude/agents/builder.md and breaker.md: copied in. A different existing file with the
     same name is first saved as <name>.md.1v1-bak and restored on uninstall.
  3. .1v1/: empty working folder.
"""
import importlib.util, json, pathlib, shutil, sys
from common import *

skill = pathlib.Path(__file__).resolve().parent.parent
agents_dst = ROOT / ".claude" / "agents"
sp = ROOT / ".claude" / "settings.json"
hook_script = str(skill / "scripts" / "hook_guard.py")
cmd = f'python "{hook_script}"'
MATCHER = "Write|Edit|MultiEdit|NotebookEdit|Read|Glob|Grep|Bash"
BAK = ".1v1-bak"
args = set(sys.argv[1:])
dry = "--dry-run" in args


def is_ours(h):
    return "hook_guard.py" in json.dumps(h)


def load_settings():
    return json.loads(sp.read_text()) if sp.exists() else {}


def say(msg): print(("[dry-run] " if dry else "") + msg)


def install():
    say(f"settings: add PreToolUse hook -> {sp}")
    say(f"  matcher: {MATCHER}")
    say(f"  command: {cmd}")
    for f in sorted((skill / "agents").glob("*.md")):
        dst = agents_dst / f.name
        if dst.exists() and dst.read_bytes() != f.read_bytes():
            say(f"agents: {dst} EXISTS and differs -> backup to {dst.name}{BAK}, then overwrite")
        elif dst.exists():
            say(f"agents: {dst} already identical, no change")
        else:
            say(f"agents: copy {f.name} -> {dst}")
    say(f"folder: create {ROOT / '.1v1'}")
    if dry: return
    agents_dst.mkdir(parents=True, exist_ok=True)
    for f in (skill / "agents").glob("*.md"):
        dst = agents_dst / f.name
        if dst.exists() and dst.read_bytes() != f.read_bytes():
            shutil.copy2(dst, dst.with_name(dst.name + BAK))
        shutil.copy2(f, dst)
    s = load_settings()
    hooks = s.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if not any(is_ours(h) for h in hooks):
        hooks.append({"matcher": MATCHER, "hooks": [{"type": "command", "command": cmd}]})
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(s, indent=2))
    (ROOT / ".1v1").mkdir(exist_ok=True)
    miss = [m for m in ("pytest", "hypothesis", "mypy", "ruff") if importlib.util.find_spec(m) is None]
    if miss: print("MISSING (pip install): " + " ".join(miss))
    print("installed agents + hook; restart Claude Code if agents are not listed")
    print('to remove: python "' + str(skill / "scripts" / "install.py") + '" --uninstall')


def uninstall():
    if sp.exists():
        s = load_settings()
        pre = s.get("hooks", {}).get("PreToolUse", [])
        keep = [h for h in pre if not is_ours(h)]
        say(f"settings: remove {len(pre) - len(keep)} 1v1 hook entr{'y' if len(pre) - len(keep) == 1 else 'ies'} from {sp}")
        if not dry:
            if keep: s["hooks"]["PreToolUse"] = keep
            else:
                s.get("hooks", {}).pop("PreToolUse", None)
                if not s.get("hooks"): s.pop("hooks", None)
            if s: sp.write_text(json.dumps(s, indent=2))
            else: sp.unlink()
    for f in sorted((skill / "agents").glob("*.md")):
        dst = agents_dst / f.name
        bak = dst.with_name(dst.name + BAK)
        if bak.exists():
            say(f"agents: restore {dst.name} from backup")
            if not dry: shutil.move(bak, dst)
        elif dst.exists() and dst.read_bytes() == f.read_bytes():
            say(f"agents: delete {dst}")
            if not dry: dst.unlink()
        elif dst.exists():
            say(f"agents: {dst} was modified by you, left in place")
    if "--purge" in args:
        if (ROOT / ".1v1").exists():
            say("purge: delete .1v1/")
            if not dry: shutil.rmtree(ROOT / ".1v1")
        v = ROOT / "verify"
        if v.exists() and "created by 1v1" in v.read_text():
            say("purge: delete ./verify (created by 1v1)")
            if not dry: v.unlink()
        cm = ROOT / "CLAUDE.md"
        if cm.exists():
            t = cm.read_text(); a, b = "<!-- 1v1:start -->", "<!-- 1v1:end -->"
            if a in t and b in t:
                say("purge: remove the 1v1 block from CLAUDE.md")
                if not dry:
                    t = t[:t.index(a)].rstrip("\n") + "\n" + t[t.index(b) + len(b):].lstrip("\n")
                    cm.write_text(t)
    if not dry: print("uninstalled")


(uninstall if "--uninstall" in args else install)()
