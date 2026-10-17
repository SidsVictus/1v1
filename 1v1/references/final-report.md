# Final report

Written by the orchestrator from command output only. Never from the builder's or breaker's own claims. Keep it short.

```markdown
# 1v1 report: <task>

## Verdict
<GREEN | NOT GREEN | STOPPED EARLY (reason)>
GREEN only if every gate below passed on a run I started. Otherwise say exactly what did not.

## Gates (all run by orchestrator)
| Gate | Result |
|---|---|
| guard.py (protected paths unchanged) | pass/fail |
| audit.py (U3, U4, U11 static scan) | pass/fail |
| Full check command | pass/fail |
| Breaker tests | n passed / n failed |
| Holdout tests | n passed / n failed |

## Questions
| ID | Question (verbatim) | Outcome | Test | Evidence |
|---|---|---|---|---|
Every ID from `.1v1/questions.md`. Q rows (the user's) first so they can check the test asks what they meant.
Any "cannot be tested" or judgement-only question is listed again under "Needs you".

## Contract rules
| Rule | Result | Test |
|---|---|---|
All U and task rules.

## Still failing or unverified
- <BLOCKING failures with one-line reproduction>
- <untested, assumed, or invented-data items>

## Logged, not fixed (MINOR)
- <items>

## Needs you
- <irreversible actions awaiting approval, judgement questions, BLOCKED reasons>

## Run summary
Rounds used: x/limit | Strikes: n | Stop reason: <streak | rounds | budget | user>
Estimated cost vs cap: <range> / <cap> (token use is approximate; rounds and attempts are counted exactly)
```

Rules: never write "done" or "complete" outside a GREEN verdict. Omitting a failure, a skipped gate, or an assumption is a violation of U16.
