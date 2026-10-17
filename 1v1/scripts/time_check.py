"""Time the check command. Usage: time_check.py "<cmd>". Writes verify-fast if over 60s."""
import subprocess, sys, time
from common import *

cmd = sys.argv[1]
t = time.time()
r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
dt = time.time() - t
print(f"exit={r.returncode} seconds={dt:.1f}")
if dt > 60:
    p = ROOT / "verify-fast"
    p.write_text("#!/usr/bin/env bash\nset -euo pipefail\npython -m pytest -q -x\npython -m ruff check .\n")
    p.chmod(0o755)
    print("OVER 60s: wrote verify-fast for the loop; run the full command in Step 6")
sys.exit(r.returncode)
