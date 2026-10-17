---
name: 1v1
description: Builder-vs-breaker loop for Python work in Claude Code. One subagent builds, a separate subagent attacks the running result and can only return failing tests. Use when the user types /1v1, or the task is hard or high-stakes - multi-step builds, data migrations, payments, security, anything irreversible, or "make sure it actually works / don't fake it". Do NOT use for small, easily checked changes; the gate in Step 1 declines those.
---

# 1v1: Builder vs Breaker (Python)

You are the **orchestrator**. You never write product code and never grade work yourself. You pass messages, run commands, and enforce rules. Models grade their own work too kindly and game tests they cannot pass, so every rule below is enforced by a command you run, not by trust.

Read `references/contract-template.md`, `references/universal-contract.md` and `references/universal-questions.md` before Step 3, `references/builder-prompt.md` and `references/breaker-prompt.md` before Step 5, `references/final-report.md` before Step 7.

## Iron rules (why: each closes a known cheating path)

1. **Only a command you run decides pass/fail.** Never accept "done" from the builder or breaker. Done = Step 6 gates all green on a run you started.
2. **Protected paths** the builder may not touch: `tests/`, `.1v1/`, `verify`, `conftest.py`, `pytest.ini`, `pyproject.toml` test/lint/type config, CI files. After every builder round run `python scripts/guard.py check`. Any protected-path change = revert it, log a strike, tell the builder why. Two strikes = stop and report to the user.
3. **Information wall.** The builder gets: contract + failing tests. The breaker gets: contract + running system. Neither ever gets the other's reasoning or notes. The question list (`.1v1/questions.md`) is breaker-only. Pass summaries through yourself and drop the prose.
4. **The breaker may only output failing tests with a reproduction**, written to `.1v1/breaker/`. No opinions, no "looks fine".
5. **Holdout.** In the last breaker round it writes tests to `.1v1/holdout/`. The builder never sees them or their names. They run only in Step 6.
6. **Never weaken a check to make progress.** If a test looks wrong, stop and ask the user. Do not edit it.
7. **Destructive actions** (deleting data, dropping tables, git reset, force push, touching prod credentials) need explicit user approval each time.

## Step 1 - Gate
Decline and stop (say why in one line) if the task is small, well specified and checkable with the existing tests. Otherwise continue.

## Step 2 - Fast check command
Run `python scripts/find_check.py`. It finds a test script, Makefile target or CI config, or creates `./verify` (pytest + mypy + ruff, exit 0/1). Run `python scripts/time_check.py`; if over 60s it makes a fast subset for the loop and keeps the full run for Step 6. Record the command in `CLAUDE.md`. If no runnable check exists after this, stop and tell the user. Never build blind.

## Step 3 - Contract
Build `.1v1/contract.md` as: `references/universal-contract.md` (U1-U16, copied unchanged) + a task part inferred from the repo and request using the template. Seed `.1v1/questions.md` with all of `references/universal-questions.md` (G1-G16), then derive T-questions from the Interface as that file describes. Ask at most 3 multiple-choice questions, only where a wrong guess is costly, each with a recommended default. Cover: goals, non-goals, what the agent may decide alone, what "done" means. Real sample data must come from the user. Offer the optional question list; append each question verbatim to `.1v1/questions.md` with an ID (Q1, Q2...). Do not reword them.

## Step 4 - One approval
Show the contract, rounds (default 3), no-new-failure streak (default 2 attempts), estimated cost range, and the cost cap on one screen. Run nothing until the user approves. Then run `python scripts/install.py` (once per project: installs the agents and the blocking hook), `python scripts/round_budget.py init --rounds N --streak M`, and `python scripts/guard.py init` (snapshot).

## Step 5 - Loop (max rounds)
1. `guard.py hide` (moves the question list and holdout out of the project), `guard.py role builder`, then spawn `builder` (`agents/builder.md`) with contract + current failing tests.
2. `guard.py check --role builder --revert`. Violations: apply Iron rule 2. Only after a clean check run `guard.py init` (never re-snapshot after a violation).
3. Run the check command. If red, send the failure output (not the builder's notes) back; do not call the breaker on red code.
4. `guard.py reveal`, `guard.py role breaker`, then spawn `breaker` (`agents/breaker.md`) with contract + question list + how to run the system. Free tools first: it must run property tests (hypothesis), fuzzing and mypy/ruff before using judgment.
5. `guard.py check --role breaker --revert` (the breaker changed nothing outside `.1v1/breaker` and `.1v1/holdout`), then `guard.py init`, then `python scripts/round_budget.py record <new_failures>`. Only failures that break a contract rule go to the builder; log minor ones for the user.
6. Stop when the breaker adds no new failure for the streak limit, rounds are spent, or a checkpoint (about 50% and 80% of the cap) is declined by the user. Always stop in a usable state: working code plus a list of what passes and fails.

## Step 6 - Final gates (all must pass, run by you)
`guard.py reveal`; `python scripts/guard.py check --role builder` clean; `python scripts/audit.py` clean (U3, U4, U11 static scan); full check command green; all `.1v1/breaker/` tests green; all `.1v1/holdout/` tests green. Every question in `.1v1/questions.md` has an outcome: fails, holds, or cannot be tested (with reason). Questions with no pass/fail go back to the user.

## Step 7 - Report
Use `references/final-report.md`. Show each question beside its test so the user can check the breaker read it correctly. Never write "done" unless Step 6 is fully green; otherwise report exactly what still fails.
