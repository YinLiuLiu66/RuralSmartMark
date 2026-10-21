---
name: frontend-craft
description: 写前端界面、搭页面或修 UI 时使用：新页面、Dashboard、表单、设置页、列表、H5/小程序/管理后台，以及 vibe coding 后界面很丑/很怪/不专业的审查与返工。先定平台惯例、设计 token 和信息层级，再写代码，最后按七类丑（惯例、预期、原生、脆弱、组织、一致、审美）自检。不用于后端/API、纯业务逻辑、无界面的脚本，也不用于 DSH 内置插件面板（那是 cordis-plugin-development）。
---

# Frontend Craft

Most "AI-generated UI is ugly" complaints are structural, not decorative: a familiar control in the wrong place, a control that does not match its data, a container that never met a long name, a screen with no priority. Fix those before choosing colors.

## Route

Use for a new page, dashboard, form, list, settings screen, onboarding flow, H5/mini-program UI, or admin panel — and for fixing an interface that feels off, unprofessional, or "vibe-coded".

Not for backend/API work, data logic with no UI, or the Harness's own plugin panels (use `cordis-plugin-development`).

## Flow

**1. Contract, before markup.** Write six lines: platform and surface; the user's one job; the one primary action; the one value the screen leads with; the states in scope; the platform patterns you will borrow. If the brief is silent, state the assumption in one line and proceed. Template: `references/design-contract.md`. For a one-component fix, skip the contract but keep the diff local.

**2. Read the codebase first.** Reuse the existing design system, component library, and tokens; never introduce a second system. Match the stack's router, state, and file conventions. On greenfield, start from the token starter in `references/design-contract.md`.

**3. Assemble from conventions.** For each element, name the native pattern it uses: dialog, action sheet, toast, segmented control, date picker, empty state. Prefer platform and accessible primitives over hand-built ones. Choose a control by data shape and cardinality, not by looks.

**4. Build hierarchy.** One primary action and one lead value per screen. Establish order with position, size/weight, and spacing before color or boxes. If every card has equal weight, the screen has no hierarchy.

**5. Stress the containers.** Before calling it done, put in extreme fixtures: longest name, 12-digit amount, zero/one/many rows, three-line error, unbroken URL, 320px width, 200% zoom. Fix with wrapping, clamping, `min-width: 0`, explicit column widths, reserved heights, and designed empty/loading/error states.

**6. Gate on the seven tests.** Run `references/ugly-taxonomy.md` end to end: uncanny, unexpected, detached, fragile, unorganized, inconsistent, plain ugly. Fix failures; record deliberate exceptions.

**7. Verify visually.** Render at 375 / 768 / 1440 (or the target platform) with real extreme data and inspect the screenshots. If the environment cannot render, say so — never claim visual polish you did not see.

## Output contract

- Working code in the project's stack; no lorem ipsum, no dead placeholder buttons.
- The six-line contract, token names introduced, and states actually covered.
- A pass / fixed / known-gap line for each of the seven tests.
- Screenshots, or an explicit "not visually verified" note.

## References

- `references/ugly-taxonomy.md` — seven failure modes with symptoms, causes, code-level rules, and before/after examples. Read before step 6; consult when a screen feels wrong but you cannot name why.
- `references/design-contract.md` — contract template with a worked example, token starter, state matrix, and platform convention tables.
