# Evidence

Read this when the user asks where the advice comes from, whether it is authoritative, or why guides disagree. It is a reading list with dates, not a citation table — the field has no single authority, and the primary format spec leaves most choices open.

## Primary sources

**agents.md** — the format's own site, now stewarded by the Agentic AI Foundation under the Linux Foundation (announced December 2025). Core claims: it is "a README for agents", not a replacement for the README; no required fields, plain Markdown, headings are free-form; the file nearest the edited code applies; user instructions in the conversation override any file; monorepos use nested files; the file is living documentation. No publication date — the site is updated in place, so read the current version rather than looking for a year. Early copies (August 2025) lack the override file, the global layer, and the per-directory loading rules that current vendor docs describe.

**OpenAI Codex — Custom instructions with AGENTS.md** — the operational detail for multi-level loading: a global file under `CODEX_HOME`, the repo root, then subdirectories; roughly one file per directory; `AGENTS.override.md` and a configurable fallback filename list. Undated, actively maintained. Read it for loading behavior, not for writing style.

**Claude Code — How Claude remembers your project** — the most specific public "what makes it effective" text, written for `CLAUDE.md` but applying to `AGENTS.md`, which it also reads. Its hard recommendations: make each instruction concrete and verifiable ("Use 2-space indentation" over "Format code properly"; "Run `npm test` before committing" over "Test your changes"); keep a single file under about 200 lines, because length costs context and lowers adherence; load path-specific rules lazily instead of growing the root file; and treat the file as context, not enforcement — use hooks or permissions when something must be forbidden. It also names when to add a line: the same mistake twice, the same correction twice, or context a new colleague would need. Undated and still being rewritten.

**GitHub Changelog, 2025-08-28** — Copilot's coding agent begins reading `AGENTS.md`, alongside `CLAUDE.md`, `GEMINI.md`, and `.github/copilot-instructions.md`. This is the moment the file stopped being Codex-specific, and therefore the cutoff for judging secondary tutorials.

## Secondary sources worth using

**GitHub Blog, "How to write a great agents.md — lessons from over 2,500 repositories"** (published 2025-11-19, updated 2025-11-25) — the only widely cited guide backed by a stated corpus rather than opinion. It is the usual origin of the "six domains" (commands, testing, project structure, code style, git workflow, boundaries) and of the always / ask-first / never split. Caveat: those two framings circulate mostly through retellings; the original wording was not verified here, so present them as a useful checklist, not as a quoted finding.

**Mintlify, "What to Include in AGENTS.md"** — the most complete template-style guide. Its framing (an onboarding brief for a new teammate), its required/optional section split, and its insistence on copying real commands out of CI rather than writing placeholders all match practice elsewhere. Undated.

**Alibaba Cloud developer article (2026-05-06)** — the clearest statement of "map, not manual": the root file holds global hard rules only, architecture detail moves to `docs/` and is reached through an index.

## Where the field disagrees

- **Minimalist vs contract.** One camp (Claude Code's docs, context-engineering writing) wants only non-obvious information and treats length as the main enemy. Another (parts of Codex/Copilot practice) wants a fuller contract with definition-of-done, review rules, and boundaries. Both agree that anything the code already states is waste; they differ on how much workflow belongs in the file. The 200-line ceiling is the practical compromise, not a law.
- **How strict to be.** "Never" lists are cheap to write and easy to ignore. The enforceable version is a CI check, a hook, or a protected path; several guides say plainly that the document cannot stop anything.
- **Maintenance cadence.** One author's "rewrite every six months" is plausible but unevidenced. What is well supported is narrower: stale and contradictory lines are worse than missing ones, and Claude Code ships a prompt-audit command to find conflicts.

## Judging freshness

For official docs, dates do not help — read the current page. For secondary tutorials, require August 2025 or later; earlier ones describe Codex-only configuration and miss the cross-tool present. When a date is unavailable, read for markers instead: override files, a global layer, one-file-per-directory loading, and AAIF stewardship indicate a late-2025-or-later version; "put a file at the repo root with your build commands" alone usually means the August 2025 wave.
