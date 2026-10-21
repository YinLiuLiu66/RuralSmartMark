# QA Ladder

Use the smallest check set that still stops the most likely failure. This local edition has two tiers.

Start with `scripts/check_all.py <dir>` (structure, directory hygiene, budget); the tiers below say what to do beyond it.

## Basic

Use when:

- the skill is exploratory or one-off
- the route is obvious
- imperfect output is cheap

Checks:

- `scripts/check_all.py`
- read the boundary once for clarity
- run one real request end to end

## Standard

Use when:

- the skill will be reused
- near-neighbor prompts are plausible
- `references/` or `scripts/` could drift from the main instructions

Checks:

- everything in Basic
- 3-5 trigger tries: should trigger, should not, near neighbors
- one realistic sample run
- re-run the trigger tries after a description change

## Escalation heuristics

- add trigger tries before writing more instruction text
- tighten the boundary before adding directories
- do not escalate without real reuse pressure
- do not add checks to look professional
