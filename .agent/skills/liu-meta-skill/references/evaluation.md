# Evaluation

Two modes; decide which one the user wants first. Neither rewrites; gather evidence first.

- **Can it be used**: mechanical checks + trigger tries.
- **Is the design consistent**: static review; no real task needed.

## Can it be used

1. **Read**: the target `SKILL.md` + directory listing; confirm the trigger surface, boundary, and output contract it claims.
2. **Run**: `scripts/check_all.py <dir>` (structure, directory hygiene, budget; directory bundles only, `<name>/SKILL.md`, flat `<name>.md` is not supported); for a single check run `scripts/check_skill.py <dir>`, `scripts/lint_skill.py <dir>`, or `scripts/context_sizer.py <dir>`.
3. **Trigger tries**: 3-5 real requests — should trigger, should not, near neighbors.
4. **Conclude**: list findings + minimal fixes by severity; do not edit files unless asked; when asked to edit, follow `references/authoring-discipline.md` and touch only the files involved.

## Is the design consistent

Use the Reviewer Checklist in `references/authoring-discipline.md` for evidence, focusing on five areas:

- **Trigger surface**: does the description match the body; are real phrasings covered; is there a near-neighbor domain (and if so, are exclusions written).
- **Boundary**: does it own a single main line; does it take on another domain's work.
- **References**: are all `references/` reachable (`check_all` no longer checks this).
- **Contract**: do the output contract and the flow disagree; do the scripts named in the docs exist.
- **Budget and language**: tier position, non-English warning.
