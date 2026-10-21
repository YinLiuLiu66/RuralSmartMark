---
name: liu-meta-skill
description: 把重复发生的工作流、提示词、SOP、对话记录沉淀成可复用的 agent skill；也用于评估/改进已有 skill、补触发描述、收敛边界、设计自我改进循环。管的是 skill 包本身——要不要做、结构、触发面、预算、迭代；单个工具定义或提示词的写法不在此列。适用于"把这个做成 skill""沉淀成可复用能力""评估这个 skill""优化这个 skill""给 skill 加触发用例""给 skill 加自我改进/回归"。
---

# Liu Meta Skill

Turn "we finished this once" into "we can reuse it". By default produce only `SKILL.md` and, when needed, `references/`; add `<name>-improver/` only when the target domain is verifiable. No reports, no packaging, no distribution.

## Routing boundary

- The target is a plugin/UI/service/tool → outside this skill; find the matching skill by its catalog description
- The target is a `SKILL.md` package → use this skill

## Prerequisites

- It recurs, and the output has a stable shape → make a skill
- One-off, pure explanation/translation/summary/brainstorming → skip; answer directly
- Unsure → read `references/non-skill-decision-tree.md`

## Flow

- **New skill** → steps 1-6
- **Evaluating an existing skill** → use the evaluation modes directly; do not ask about intent or pick an archetype

1. **Qualification**: what actually happened last time? Will it recur? What does the output look like?
2. **Intent**: ask only questions that change the design, at most two rounds; record explicit assumptions for the rest.
3. **Archetype**: default `scaffold`; use `production` only when routing is often wrong and a deterministic script or checklist clearly improves reliability.
4. **Boundary**: state owns / produces / does not take / what goes into `references/`.
5. **Description first**: include trigger actions and exclusions, then write the body.
6. **Self-check**: run `scripts/check_all.py <dir>` first (`<dir>` is the target skill, default current directory; it covers structure, directory hygiene, and budget); run `scripts/check_skill.py <dir>` or `scripts/context_sizer.py <dir>` for a single check; then follow `references/qa-ladder.md` and run one real request end to end; for description changes, run `check_regression.py` per `references/self-improvement.md` (prefer git for the baseline; if the user explicitly does not use git, keep a manual copy of the old file).

## Output contract

- Required: `<name>/SKILL.md` (`name` in kebab-case, `description` required)
- As needed: `references/`, `scripts/`, `assets/`, `evals/trigger-cases.jsonl` (for description regression)
- Only when the target domain is verifiable: also `<name>-improver/SKILL.md` + `<name>/feedback.md` (skeleton and fields in `references/self-improvement.md`)
- Not by default: `reports/`, `manifest.json`, `agents/interface.yaml`, cross-platform adapters; add them when actually needed

## Evaluation

Two modes; decide which one the user wants first. Neither rewrites; gather evidence first.

- **Can it be used**: mechanical checks + trigger tries.
- **Is the design consistent**: static review; no real task needed.

Output quality is not evaluated here — that needs a real task. If asked, only list trial cases and what to watch, without a verdict. Evaluation produces no scores, reports, or evidence files.

Steps: `references/evaluation.md`.

## Authoring discipline

- `SKILL.md` holds only the trigger surface, execution skeleton, and output contract; detail goes into `references/`
- Do not add structure for "might be useful later"; for every new file, say which uncertainty it removes
- Do not hard-code host details (local paths, tool names) into a general skill; when unavoidable, label them "local only"
- A skill records procedural knowledge; runtime facts (paths, session ids, this run's result) do not belong in it
- Do not auto-improve without regression cases: optimization without an objective function only fits noise
- New skills: body and `references/` in English, `description` in the user's language (Chinese in this profile), trigger phrases kept verbatim; existing Chinese bodies migrate as they are touched
- When speaking Chinese, sound natural, not like filling a form

## Reference

Read on demand; do not read all at once:

| File | When to read |
|---|---|
| `references/intent-dialogue.md` | the user cannot say what they want |
| `references/skill-archetypes.md` | choosing scaffold or production |
| `references/skill-engineering-method.md` | when the full method is needed |
| `references/resource-boundaries.md` | deciding where something belongs, or how long the body may be |
| `references/qa-ladder.md` | deciding how far to verify |
| `references/pattern-extraction-doctrine.md` | extracting a general pattern from a specific case |
| `references/reference-scan.md` | looking for external references (skippable) |
| `references/output-quality-risk.md` | the output is a document or report for people |
| `references/iteration-philosophy.md` | first version done, choosing the next step |
| `references/self-improvement.md` | improving a skill over time, or adding an improver |
| `references/gate-selection.md` | adding a check |
| `references/authoring-discipline.md` | editing an existing skill |
| `references/evaluation.md` | running an evaluation |
