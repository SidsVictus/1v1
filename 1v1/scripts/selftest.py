"""Self-test of the anti-cheat scripts in a throwaway project. Run: python selftest.py"""
import json, os, subprocess, sys, tempfile, pathlib
S = pathlib.Path(__file__).resolve().parent
tmp = pathlib.Path(tempfile.mkdtemp())
env = {**os.environ, "ONEV1_ROOT": str(tmp)}
res = []


def run(script, *a, inp=None):
    p = subprocess.run([sys.executable, str(S / script), *a], cwd=tmp, env=env, input=inp, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def t(name, ok): res.append(ok); print(("PASS " if ok else "FAIL ") + name)


def w(p, s):
    f = tmp / p; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(s)


w("src/app.py", "def add(a, b):\n    return a + b\n")
w("tests/test_app.py", "from src.app import add\ndef test_add():\n    assert add(1, 2) == 3\n")
w("pyproject.toml", "[tool.pytest.ini_options]\n")
w(".1v1/questions.md", "G1: x\n"); w(".1v1/holdout/h.py", "x=1\n")
run("guard.py", "init")
# builder cheats
w("tests/test_app.py", "def test_add():\n    assert True\n"); w("conftest.py", "x=1\n"); (tmp / "pyproject.toml").unlink()
rc, o = run("guard.py", "check", "--role", "builder", "--revert")
t("builder tampering detected", rc == 1 and "modified: tests/test_app.py" in o and "added: conftest.py" in o and "deleted: pyproject.toml" in o)
t("tampering reverted", "assert add(1, 2) == 3" in (tmp / "tests/test_app.py").read_text() and not (tmp / "conftest.py").exists() and (tmp / "pyproject.toml").exists())
w("src/app.py", "def add(a, b):\n    return a + b + 0\n")
rc, o = run("guard.py", "check", "--role", "builder"); t("builder source edit allowed", rc == 0)
run("guard.py", "init")
w("src/app.py", "def add(a, b):\n    return 3\n")
rc, o = run("guard.py", "check", "--role", "breaker"); t("breaker source edit blocked", rc == 1)
run("guard.py", "check", "--role", "breaker", "--revert")
w(".1v1/breaker/test_g1.py", "def test_g1(): pass\n")
rc, o = run("guard.py", "check", "--role", "breaker"); t("breaker may add .1v1/breaker tests", rc == 0)
# hide / reveal
run("guard.py", "hide"); t("questions+holdout hidden", not (tmp / ".1v1/questions.md").exists() and not (tmp / ".1v1/holdout").exists())
run("guard.py", "reveal"); t("revealed", (tmp / ".1v1/questions.md").exists() and (tmp / ".1v1/holdout/h.py").exists())
# audit
w("src/bad.py", "import requests\nfrom unittest import mock\nimport unittest.mock\ndef f():\n    pass\ndef g():\n    try:\n        1/0\n    except:\n        pass\nx = 1  # type: ignore\nimport os\nif 'PYTEST_CURRENT_TEST' in os.environ: pass\n# TODO later\n")
rc, o = run("audit.py")
t("audit finds stub/mock/net/bare except/ignore/test-detect/TODO", rc == 1 and all(k in o for k in ["U3 stub", "U3 mock", "U11", "U4 bare", "U4 suppression", "U2", "TODO"]))
(tmp / "src/bad.py").unlink(); rc, o = run("audit.py"); t("audit clean on good code", rc == 0)
# budget
run("round_budget.py", "init", "--rounds", "3", "--streak", "2")
rc, o = run("round_budget.py", "record", "2"); t("budget continues on failures", not json.loads(o)["stop"])
run("round_budget.py", "record", "0"); rc, o = run("round_budget.py", "record", "0"); t("budget stops on streak", json.loads(o)["stop"] and json.loads(o)["reason"] == "streak")
# hook
run("guard.py", "role", "builder")
def hook(tool, **ti): return run("hook_guard.py", inp=json.dumps({"tool_name": tool, "tool_input": ti}))[0]
t("hook blocks builder edit of tests", hook("Edit", file_path=str(tmp / "tests/test_app.py")) == 2)
t("hook allows builder edit of src", hook("Edit", file_path=str(tmp / "src/app.py")) == 0)
t("hook blocks builder reading .1v1", hook("Read", file_path=str(tmp / ".1v1/questions.md")) == 2)
t("hook blocks builder sed -i on pyproject", hook("Bash", command="sed -i s/a/b/ pyproject.toml") == 2)
t("hook blocks rm -rf", hook("Bash", command="rm -rf build") == 2)
t("hook allows pytest", hook("Bash", command="python -m pytest -q 2>&1") == 0)
run("guard.py", "role", "breaker")
t("hook blocks breaker src write", hook("Write", file_path=str(tmp / "src/app.py")) == 2)
t("hook allows breaker test write", hook("Write", file_path=str(tmp / ".1v1/breaker/t.py")) == 0)
t("hook allows breaker pytest", hook("Bash", command="python -m pytest .1v1/breaker") == 0)
t("hook blocks breaker redirect into src", hook("Bash", command="echo x > src/app.py") == 2)
print(f"\n{sum(res)}/{len(res)} passed"); sys.exit(0 if all(res) else 1)
