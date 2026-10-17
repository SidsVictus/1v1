"""Round/streak counter kept outside the project. Usage: init --rounds N --streak M | record NEW_FAILURES | status"""
import json, sys
from common import *

F = STATE / "budget.json"


def load(): return json.loads(F.read_text())


def out(s):
    done = s["round"] >= s["rounds"] or s["zero_streak"] >= s["streak"]
    reason = "streak" if s["zero_streak"] >= s["streak"] else ("rounds" if s["round"] >= s["rounds"] else "")
    frac = s["round"] / s["rounds"]
    print(json.dumps({**s, "stop": done, "reason": reason, "checkpoint": frac >= 0.5 and not s.get("cp50") or frac >= 0.8 and not s.get("cp80")}))


a = sys.argv[1:]
if a[0] == "init":
    STATE.mkdir(parents=True, exist_ok=True)
    s = {"rounds": int(a[a.index("--rounds") + 1]), "streak": int(a[a.index("--streak") + 1]), "round": 0, "zero_streak": 0}
    F.write_text(json.dumps(s)); out(s)
elif a[0] == "record":
    s = load(); s["round"] += 1
    s["zero_streak"] = s["zero_streak"] + 1 if int(a[1]) == 0 else 0
    F.write_text(json.dumps(s)); out(s)
else: out(load())
