---
name: agents-md-craft
description: 编写、重写或审查仓库级 AGENTS.md（含 CLAUDE.md、GEMINI.md、copilot-instructions.md）时使用：给新仓库起草、给老仓库补写、拆分 monorepo 的多层文件、判断现有文件是否太长/太空/自相矛盾/已过期。做法是先扫仓库取真实命令，按六领域加三层边界写，控制在一到两屏内，再逐条验证命令与路径。也用于解释这些建议的出处。不用于 README/架构文档、单个任务提示词或 skill 编写（后者用 liu-meta-skill）。
---

# Agents MD Craft

`AGENTS.md` is a brief for a capable new teammate, not a manual. Every line costs attention, so it earns its place only by saying what the code cannot: how to run the thing, how to know a change is good, what not to touch. Most weak files were copied from a template, padded with what the tree already shows, and shipped without running a single command.

## Route

Use when writing, rewriting, or reviewing a repository's `AGENTS.md`: drafting from scratch, retrofitting a legacy repo, splitting a monorepo, or judging a file that is too long, too vague, self-contradictory, or stale. The same content serves `CLAUDE.md`, `GEMINI.md`, and `.github/copilot-instructions.md` — keep one source of truth and point the others at it.

Not for READMEs and architecture docs, not for a single task's prompt, not for authoring a skill package (use `liu-meta-skill`).

## Flow

**1. Read the repo before writing a word.** Gather what the file will assert: runtime versions, package manager, workspace layout, the real build, test, lint, and typecheck commands from `package.json`, `Makefile`, `pyproject.toml`, and CI workflows, plus single-test invocation, codegen, migrations, and local setup. Prefer CI over memory — it is the command set that has to pass. On a large repo, sample the paths a change usually touches.

**2. Choose the layout.** One root file when one toolchain runs the repo; nested files under package roots when packages differ in manager, commands, or rules. The nearest file wins and a user's explicit instruction beats any file, so never repeat root text in a child; prefer one file per directory over a chain. Keep the root global: setup, cross-cutting workflow, repo-wide boundaries.

**3. Fill six domains, then cut.** Commands; test practice; project map; code style; git and PR workflow; boundaries. The map covers only non-obvious routing (where handlers live, what is generated); style covers only what a formatter does not enforce. Delete empty headings instead of keeping them. Per-domain prompts and templates: `references/authoring-guide.md`.

**4. Write at instruction granularity.** Each line must be checkable by an agent that cannot ask: name the command, the file pattern, the exact rule, and give the reason when a rule looks arbitrary. Imperative mood, one rule per line, commands fenced and copy-pasteable. One screen is the target, two the limit; 200 lines is a ceiling, not a goal.

**5. Audit against the repo.** Every command exists in config and, when cheap, runs; every path exists; no placeholders, invented scripts, or contradictions across levels; the file does not restate the README or the tree. For each hard rule, name what stops a violation — if the answer is this document, add a CI check, hook, or protected path: the file is context, not enforcement.

**6. Hand back what is unverified.** Say which commands you ran, which you only found in config, and what you assumed. Never deliver a filled template with `<your test command>` still in it.

## What separates a good one

- **Non-obvious wins.** Build quirks, generated-files rules, why tests run serially. Dependency lists are noise.
- **Boundaries pay best:** always / ask first / never — routine steps, actions that need a human, hard prohibitions (secrets, vendored code, shared databases).
- **Specific beats sincere.** "Run `pnpm test` before committing" survives; "test your changes" does not.
- **Short is a feature.** Every line dilutes the others; cut stale rules before adding new ones.
- **Living, not launched.** Add a rule after the same mistake twice, not when it is imagined.

Frequent failures: a pasted README, an 800-line architecture tour, task-level instructions ("this refactor should use X"), conflicting commands across levels, slogans with no command. Rewrites: `references/authoring-guide.md`.

## Reviewing an existing file

Answer five questions, then report the weakest two with the smallest diff, not a rewrite: can an agent start the app and run the tests from this file alone? is every command real? which lines only restate the tree? do the levels contradict each other? which rules are unenforceable wishes?

## Reference

| file | when |
|---|---|
| `references/authoring-guide.md` | writing section by section, monorepo placement, templates, weak-vs-strong examples |
| `references/evidence.md` | the user asks where the advice comes from, or why experts disagree |
| `evals/trigger-cases.jsonl` | re-run routing cases after editing the description |
