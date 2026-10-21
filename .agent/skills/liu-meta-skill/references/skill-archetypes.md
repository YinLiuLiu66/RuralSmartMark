# Skill Archetypes

Decide which kind of skill to build before deciding how many files or checks to add.

## Scaffold

Use for:

- real workflows that are still exploratory; get them running first

Default assets:

- `SKILL.md`
- one `references/` file when needed

Fits when:

- reuse is possible but unproven
- the cost of failure is low
- the flow will keep changing

## Production

Use for:

- compact skills that will be reused and are easy to route wrong

Default assets:

- lean `SKILL.md`
- selective `references/`
- one deterministic script when truly needed
- optional `evals/`

Fits when:

- a wrong route wastes time
- a checklist or script would clearly improve reliability

## Local scope

`Library` and `Governed` depend on cross-platform distribution, an evidence ledger, and governance review; this local edition does not cover them. Introduce them separately when the need is real.

## Anti-Archetypes

Do not force the skill shape onto:

- a one-off answer
- a document
- a brainstorming session
- an implementation task with no reusable flow

See [Non-Skill Decision Tree](non-skill-decision-tree.md).
