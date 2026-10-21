# Gate Selection

Add checks by risk, not by habit. Tier definitions live in `references/qa-ladder.md`; this page only answers when a check is worth adding.

## Risk and tier

| Risk | Typical archetype | Tier |
|---|---|---|
| Low | Scaffold | Basic |
| Medium | Production | Standard |

## Trigger checks

Use when:

- the route can be confused with a nearby skill
- the trigger wording is unclear
- the description just changed

How:

1. try real phrasings: should trigger, should not, near neighbors
2. if `evals/` exists, run the cases; otherwise check by hand
3. fix the description before touching the body

## Context

If rigor increases but initial load crosses the budget, move detail into `references/` instead of adding more checks.
