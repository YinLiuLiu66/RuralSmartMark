# Resource Boundary Spec

This spec defines where information belongs inside a skill package.

## Principle

Keep the main skill small enough to route and execute clearly. Move detail out of `SKILL.md` as soon as it stops helping routing or branch selection.

Do not add structure for imagined future needs. A folder, script, eval, or governance file belongs in the package only when it reduces current ambiguity, execution burden, route risk, or maintenance risk.

## Context Budget Tiers

Use the lightest budget that still fits the package.

- `scaffold`: `700` initial-load tokens
- `production`: `1000` initial-load tokens

Numbers are produced by `scripts/context_sizer.py` and defined once in `scripts/limits.py`; do not restate them elsewhere. This local edition keeps the first two of yao's four tiers.

The report states where the estimate sits relative to each tier instead of deciding which tier applies. A tier is a claim the author makes, not something the checker can infer, and the local package has no manifest to carry it.

Platform limits are separate from budgets. A rendered `skill` tool result above 8192 characters has its middle replaced by the tool-result pruner (4096 head + 1024 tail kept), and a catalog description above 500 characters is truncated to 497 + `...`.

## Placement Rules

### Put content in `SKILL.md` when it is:

- part of the trigger surface
- part of the core execution skeleton
- part of the output contract
- necessary for branch selection or safe defaults

### Put content in `references/` when it is:

- domain guidance
- long examples
- policy material
- schemas or templates humans or agents may read on demand

### Put content in `scripts/` when it is:

- deterministic
- repetitive
- brittle if rewritten from prose
- easier to validate as code than as instructions

### Put content in `evals/` when:

- the skill is reused enough that routing mistakes matter
- near-neighbor confusion is likely
- quality claims should be reproducible

### Put content in `assets/` when:

- the package includes output artifacts, examples, or static files that should not bloat prompt context

## Anti-Patterns

Avoid these:

- storing long policy text directly in `SKILL.md`
- adding `references/` with no files that are actually used
- adding `scripts/` for logic that is still best expressed in prose
- adding `evals/` for one-off or disposable skills
- creating every folder by default even when empty
- keeping folders that are neither referenced in `SKILL.md` nor declared as factory components
- adding broad configuration knobs before a real variation exists
- adding governance or reports to make a scaffold look mature when no reuse pressure exists

## Heuristics

### `SKILL.md`

- should stay focused
- should not become the full knowledge base
- should mention any optional directory that materially affects execution

### `references/`

- should earn their keep
- should usually be named and discoverable from `SKILL.md`

### `scripts/`

- should exist only when deterministic logic or formatting logic is real
- should be referenced explicitly from `SKILL.md` when required for execution

### `evals/`

- should exist when routing or quality claims need to be defended
- should be skipped for disposable personal drafts

## 自检

- `scripts/check_skill.py`：frontmatter、name、引用路径、正文预算
- `scripts/context_sizer.py`：初始加载 token

这两个检查只回答"包是否还能被路由、是否还够轻"，不评价质量。

## Quality Intent

最好的 skill 不是文件最多的那个，而是"小到刚好让重复工作可靠、可复用"的那个。

见 [Authoring Discipline](authoring-discipline.md)。
