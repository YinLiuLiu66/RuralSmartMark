# Skill Engineering Method

Turn messy workflow material into a reusable skill without letting the entrypoint bloat. This local edition covers only `scaffold` and `production`.

## Core Loop

1. Decide whether this should be a skill at all.
2. Use one short intent dialogue to lock the real job, outputs, exclusions, and constraints.
3. Pick the smallest archetype that works.
4. Define one clear capability boundary.
5. Write and test the trigger description first, then expand the body.
6. Converge scope with authoring discipline so each change maps to a check.
7. Ship a routable first version, then pick the three highest-value next steps.

## Phase 1: Qualification

Promote to a skill only when at least one holds:

- the work recurs
- the work is easy to route wrong
- a deterministic script saves repeated effort

Refuse to build a skill for:

- explanation
- summary
- translation
- brainstorming
- a document with no agent execution
- a one-off answer with no reuse value

See [Non-Skill Decision Tree](non-skill-decision-tree.md).

## Phase 1.5: Authoring Discipline

Hold the execution discipline before expanding the package:

- clarify only assumptions that change the package design
- do not add speculative features, generic configuration, or decorative structure
- when editing an existing skill, touch only files that directly serve this change
- every meaningful change maps to a check: route evidence, sample execution, resource-boundary check

See [Authoring Discipline](authoring-discipline.md).

## Phase 1.6: Problem Diagnosis

When the user brings a fuzzy pain point instead of a clear skill request, diagnose the package shape before asking about structure.

- infer the best fit: scaffold, production, or no skill
- offer at most three candidate directions
- say why each fits, where it is limited, and what the first version should verify
- once intent is clear enough, give one concrete recommendation instead of a menu

## Phase 2: Intent Dialogue

Before deep authoring, ask only questions that change the package design.

- open like a teacher, not with a field table
- let the user describe it naturally first; a small template is only an optional shortcut
- fill non-core gaps with visible assumptions; interrupt only for core job, primary output, or an explicit direction conflict
- ask one context-relevant question per round, at most two rounds; if still unclear, give a labeled "preferred inference"
- which recurring job should this skill own
- what real inputs will the user hand it
- what must it produce
- which near-neighbor requests should be kept out
- are there systems, repos, or products worth referencing
- which constraints matter: privacy, naming, local fit

See [Intent Dialogue](intent-dialogue.md).

## Phase 3: Archetype Selection

Pick the lightest tier that is enough.

- `Scaffold`: exploratory, personal, or short-term
- `Production`: reused, easy to route wrong, still compact

`Library` and `Governed` depend on cross-platform distribution and governance review; this edition does not cover them.

See [Skill Archetypes](skill-archetypes.md).

## Phase 4: Boundary Design

Every skill answers four questions:

- which recurring job does it own
- what does it produce
- which near-neighbor requests must not route here
- which details belong outside `SKILL.md`

Boundary before wording.

## Phase 5: Reference Scan

Do one short reference scan before deep authoring.

- look at at most `3-5` references
- prefer high-star external projects and official baselines
- then user-provided references; extract patterns and standards only
- use local files last, for fit, privacy, and compatibility
- keep only what passes recurrence, generativity, distinctiveness, and boundary clarity
- record what is not borrowed, so the new skill stays light

See [Reference Scan Strategy](reference-scan.md) and [Pattern Extraction Doctrine](pattern-extraction-doctrine.md).

## Phase 5.5: Output Quality Pre-check

Before calling the package usable, predict how its final output is most likely to fail.

- tutorials: generic headings, empty examples, missing success checks
- reports and Markdown: weak tables, dense lists, broken hierarchy
- screenshots and visuals: wrong crop, missing assets, fabricated visual evidence
- research or citations: footnote piles, unsupported claims
- code or commands: hidden assumptions about cwd, inputs, outputs, side effects

Write the conclusions into `SKILL.md` guardrails or `references/`; this edition does not generate separate reports.

See [Output Quality Risk](output-quality-risk.md).

## Phase 6: Trigger-First Authoring

Write the frontmatter `description` first, then expand the body.

- start from the recurring job
- include the trigger actions that should route here
- write exclusions when confusion is likely
- try routing before expanding the file tree

Order of trigger-quality checks:

1. try 3-5 real phrasings (should trigger, should not, near neighbors)
2. if `evals/` exists, run the cases
3. fix the description, then consider the body

## Phase 7: Gate Selection

Add checks by risk, not by habit.

- low-risk scaffold: structure check + context budget
- production: add trigger tries and one sample execution

See [Gate Selection](gate-selection.md).

## Phase 8: First Iteration Philosophy

The first version is a routable baseline, not the final answer.

- fix triggers and exclusions before expanding the body
- add one execution asset before many documents
- give three highest-value next steps; avoid expanding in all directions
- prefer the smallest step where reliability gain exceeds context cost
- put unverifiable ideas into candidate next steps, not the baseline

See [Iteration Philosophy](iteration-philosophy.md) and [Authoring Discipline](authoring-discipline.md).

## Design Principle

A method is only right when rigor grows faster than context cost. If a new check or document only makes the skill heavier without making it more reliable, delete it or move it.
