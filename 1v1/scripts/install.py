"""One-time setup in the target project: copies agents and registers the hook. Usage: python <skill>/scripts/install.py"""
import json, pathlib, shutil, sys
from common import *

skill = pathlib.Path(__file__).resolve().parent.parent
(ROOT / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
for f in (skill / "agents").glob("*.md"): shutil.copy2(f, ROOT / ".claude" / "agents" / f.name)
sp = ROOT / ".claude" / "settings.json"
s = json.loads(sp.read_text()) if sp.exists() else {}
cmd = f'python "{skill / "scripts" / "hook_guard.py"}"'
hooks = s.setdefault("hooks", {}).setdefault("PreToolUse", [])
if not any(cmd in json.dumps(h) for h in hooks):
    hooks.append({"matcher": "Write|Edit|MultiEdit|NotebookEdit|Read|Glob|Grep|Bash", "hooks": [{"type": "command", "command": cmd}]})
sp.write_text(json.dumps(s, indent=2))
(ROOT / ".1v1").mkdir(exist_ok=True)
import importlib.util
miss = [m for m in ("pytest", "hypothesis", "mypy", "ruff") if importlib.util.find_spec(m) is None]
if miss: print("MISSING (pip install): " + " ".join(miss))
print("installed agents + hook; restart Claude Code if agents are not listed")
