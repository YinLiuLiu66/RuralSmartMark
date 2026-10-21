# Self-Improvement

A skill is a file, so it can be changed. But being changeable does not mean it should change itself. This page is only about when an improvement loop is worth running, and how not to break the skill while running it.

## Two kinds of iteration

- **Manual iteration**: a human reads the output and edits. Fits low-frequency, judgment-heavy, one-off work.
- **Automatic evolution**: feedback is collected → an improver summarizes it → proposes one minimal change → a human reviews before merging. Fits high-frequency, verifiable work.

The choice is not about enthusiasm; it is about **verifiability**.

## Admission: a baseline first, evolution second

- Clear success criteria (tests pass, assertions hold, golden output) → build the verification set first, then allow automatic proposals.
- No right answer (tone, quality, judgment) → manual edits only.

Why: automatic improvement is an optimizer. Without an objective function it optimizes noise — a writing skill that gets worse with each edit is not bad luck, it is the inevitable result of having no objective function.

## Feedback must be low-friction and carry a why

- Write where people already write: say "this is wrong because…" in the conversation; do not add a form or a survey.
- Collect only "what is wrong + why"; binary good/bad ratings do not generalize, so the next model can only guess.
- The feedback sink must be part of the output contract (a fixed file or directory), otherwise it disappears when the session ends.

Why: low friction decides whether the signal keeps coming; the reason decides whether the signal transfers.

## The two-skill shape

- **base skill**: the domain knowledge that does the work.
- **improver skill**: periodically reads feedback, proposes **one** minimal change, and produces a diff for human review.

Why not merge them: execution and observation differ in frequency, context, and permissions. Merged, the base slowly turns into a log.

On this machine there is no scheduler and no remote/PR flow; git lives in the workspace repository that contains this skill (single machine, no remote). So the improver is triggered by hand: changes are shown as `git diff` and committed only after a human reviews them. Do not pretend there is CI.

## Minimal improver skeleton

`<name>-improver/SKILL.md` needs only this:

```markdown
---
name: <name>-improver
description: Read feedback for <name>, find the recurring class of problem, and propose one minimal change for human review.
---

## When to run
Triggered by hand; wait for 3+ same-direction feedback items.

## Flow
1. Read `../<name>/feedback.md`
2. Find only the recurring class; do not touch single items
3. Propose one minimal change, with the reason and a diff
4. Do not edit the base directly; output a diff and wait for review
5. Run check_regression.py after the change; do not merge a regression

## Output
One diff, why this one, and the regression result (or "no cases; back to manual")
```

The template's description is English here; when the user works in Chinese, write the generated description in Chinese.

Feedback lands in the base skill's `feedback.md`, not in the improver. Three lines each:

```markdown
## 2026-10-19
- What was wrong: treated "service active" as "registration succeeded" again
- Why: never distinguished active from registered
- Expected: check Tool.listTools or a 200 route first
```

## Two failure modes that will happen

- **Bloat**: every improvement adds text until `SKILL.md` becomes an incident archive. Guardrail: delete one line for every line added, or move it into `references/`.
- **Negative optimization**: looks better, measures worse. Guardrail: run `check_regression.py` before merging; do not merge a regression.

The bar for one improvement: turn one existing failing case into a pass, and turn no passing case into a failure. Anything less is not an improvement.

## What does not belong in a skill

- Runtime facts (which path this run used, which session id, this run's result) — that is memory or a log.
- One-off exceptions — wait until they happen a second time.

Why: a skill is procedural knowledge: stable, reviewable, changed deliberately. Writing volatile facts into it means editing the skill every time.

## Minimal setup on this machine

1. Leave a feedback-sink convention in the skill (where to write, which fields to record).
2. Wait for 3+ same-direction items; do not change anything for a single item.
3. Run the regression after the change. Prefer git for the baseline: it guarantees the "old version" is the last commit, with no manual copy.

   ```bash
   git show HEAD:./SKILL.md > /tmp/liu-old.md
   python3 scripts/check_regression.py . \
     --baseline /tmp/liu-old.md --cases evals/trigger-cases.jsonl
   rm -f /tmp/liu-old.md
   ```

   - Delete the temp file after the run: the old version is in git; fetch it again when needed.
   - `./` makes the path relative to the current directory; a plain path in `rev:path` is relative to the repo root, so `HEAD:SKILL.md` breaks once the skill moves into a subdirectory.
   - If this change is already committed, use `HEAD~1` (also written `HEAD~1:./SKILL.md`).
   - **Ask the user to use git first**; only when the user explicitly says no git, fall back to "save a copy of the old `SKILL.md` before editing and pass that path to `--baseline`". The script itself does not require git.
   - Cases default to `evals/trigger-cases.jsonl`; point `--cases` elsewhere if needed. With no cases the script exits 2 on purpose: no baseline means no pretending it was verified.
   - It only covers the description/trigger surface; body changes still need a real task run.
   - The scripts are stdlib-only; any Python 3.9+ works.
