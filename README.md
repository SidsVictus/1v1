<p align="center">
  <img src="assets/banner.png" alt="1v1: Builder vs Breaker for Claude Code" width="100%">
</p>

# 1v1: Builder vs Breaker

A Claude Code skill where one subagent builds the code and a separate subagent attacks the running result and can only return failing tests. Use it for hard or high-stakes tasks.

📄 **[Read the full report](1v1-report.pdf)**

## Install

**Claude Code:** copy the `1v1` folder into `~/.claude/skills/`.

**claude.ai:** zip the `1v1` folder, then go to Customize → Skills → Add → Upload a skill.

## Use

Type `/1v1`, or say things like "make sure it actually works" or "stress test this".

## What it does

Models tend to grade their own work too kindly. 1v1 splits the job in two:

- **Builder** writes the code, guided by a contract and a set of failing tests.
- **Breaker** attacks the running result and can only return failing tests with a reproduction, never opinions.

A separate orchestrator runs the checks itself, so "done" only means the final test gates actually passed.

## Who it's for

- Developers who use Claude Code for work where a silent bug is costly.
- People who have been burned by "it works!" claims that weren't true.
- Anyone who wants proof of what passes and what fails, not a confident summary.

## Where it's most useful

- Multi-step builds with many moving parts
- Data migrations and anything irreversible
- Payments and money-handling code
- Security-sensitive features
- Tasks where you'd normally say "make sure it actually works"

## Where it's not useful

- Small, easily checked changes. The skill declines these on its own (Step 1 gate).
- Non-Python projects. The tooling is built around Python.
- Quick prototypes or throwaway scripts, where the extra rounds cost more than they save.
- Work you can't run. The skill needs a runnable check, and it stops if none exists.

## Good to know

- You approve the contract, number of rounds and estimated cost once, before anything runs.
- More rounds mean more tokens, so expect it to cost more than a normal Claude Code session.

## Commands

**In Claude Code**

| Command | What it does |
|---|---|
| `/1v1` | Starts the skill. It first checks whether the task is hard enough, then runs setup and the builder/breaker rounds. |

**Scripts** (the skill runs these for you; run them from your project root, using the full path to the skill folder, for example `~/.claude/skills/1v1/scripts/`)

| Script | What it does |
|---|---|
| `install.py` | One-time setup: adds the hook and agent files. `--dry-run` previews, `--uninstall` removes the hook and agents, `--uninstall --purge` also removes `.1v1/`, `verify` and the `CLAUDE.md` block. |
| `find_check.py` | Finds your project's one-command check (`verify`, Makefile, nox, tox or pytest). With `--create` it writes `./verify` (pytest + mypy + ruff). |
| `time_check.py "<cmd>"` | Times the check. If it takes over 60 seconds, it writes a fast subset (`verify-fast`) for the loop. |
| `round_budget.py` | Counts rounds and the no-new-failure streak. `init --rounds N --streak M` starts it, `record N` logs new failures, `status` shows progress. |
| `guard.py` | Detects tampering with protected files (tests, config, CI). `init` snapshots, `check [--role builder\|breaker] [--revert]` verifies and can undo changes, `hide`/`reveal` move the question list and holdout tests out of and back into the project, `role NAME` sets the active role. |
| `hook_guard.py` | The Claude Code hook. Blocks actions the active role isn't allowed to take, such as the builder editing tests. |
| `audit.py` | Scans the finished code for cheating patterns (stubs, mocks, swallowed errors, suppressions). Exits 1 on findings. |
| `selftest.py` | Tests the scripts above in a throwaway project (21 checks). |


## License

MIT
