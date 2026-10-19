# 1v1: what is tested and what is not

Built without access to Claude Code. The scripts are tested; the Claude Code integration is not.

## Verified (sandbox)
`python "<skill>/scripts/test_install.py"` covers installation beside a same-named foreign hook, shared hook entries, prompt hooks, repeat installation, agent backup/restore and dry-run behavior in disposable projects.
`python "<skill>/scripts/test_time_check.py"` covers quoted arguments, literal shell syntax and propagation of a failing check's exit code.

`python "<skill>/scripts/selftest.py"` -> 21/21: tamper detection and revert, breaker write limits, hide/reveal of questions and holdout, static audit (stubs, mocks, network, swallowed errors, suppressions, test-runner detection, TODOs), round and streak budget, hook allow/block decisions on simulated input.

## Not verified: please check in Claude Code
1. **Hook format.** Does PreToolUse pass `tool_name` and `tool_input` as JSON on stdin as `hook_guard.py` assumes, and does exit code 2 block the call? Does `matcher` accept the tool list in `install.py`?
2. **Subagents.** Are `.claude/agents/builder.md` and `breaker.md` picked up? Do the `tools:` lists hold (breaker has no Edit)?
3. **Orchestration.** Does the main session follow SKILL.md in order: gate, check command, contract, one approval, loop with hide/reveal/role/guard calls, final gates?
4. **Information wall.** Does the orchestrator pass only failing test output to the builder, and never the breaker's reasoning?
5. **Hook limits.** Shell-command blocking is pattern based. Try to make the builder edit a test via a Python one-liner; `guard.py check --revert` should catch and undo it.
6. **Trigger.** Does `/1v1` load the skill, and does a hard task trigger it while a rename does not (see `evals/evals.json`)?

## Setup (target project)
`pip install pytest hypothesis mypy ruff`, then `python "<skill>/scripts/install.py" --dry-run` to preview, `python "<skill>/scripts/install.py"` to install, and `python "<skill>/scripts/install.py" --uninstall --purge` to remove the hook, agents and marked setup files (`verify-fast`, if created, is removed manually). Run the three prompts in `evals/evals.json` with the skill and without it, and compare.

## Known limits
Token spend cannot be capped by a skill; only rounds and attempts are counted. The skill is a proposal: its benefit is unmeasured.
