# Authoring Guide

Detail behind the steps in `SKILL.md`. Read the section you are working on, not the whole file.

## 1. Where the facts live

The point of this table is to replace guessing with a lookup. If a fact is not in one of these places, it is an assumption — label it.

| Fact | Source |
|---|---|
| Runtime version | `.nvmrc`, `.tool-versions`, `engines` in `package.json`, `.python-version`, `rust-toolchain.toml`, `go.mod` |
| Package manager | lockfile (`pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `uv.lock`, `poetry.lock`, `go.sum`) — the lockfile is the answer |
| Commands | `package.json` scripts, `Makefile`/`justfile` targets, `tox.ini`, `Cargo.toml` aliases, `.github/workflows/*.yml` |
| What CI enforces | workflow files and branch protection notes; this is the authoritative "must pass" list |
| One-test invocation | test runner config (`vitest.config.ts`, `jest.config.js`, `pytest.ini`, `conftest.py`) and CI args |
| Local setup | README quickstart, `docker-compose.yml`, `.env.example`, `devcontainer.json` |
| Generated code | `.gitignore`, codegen config (`graphql-codegen`, `prisma generate`, `buf.gen.yaml`), "do not edit" headers |
| Conventions not in config | recent `git log`, PR template, `CONTRIBUTING.md`, lint overrides scoped to directories |
| Ownership | `CODEOWNERS`, `catalog-info.yaml`, packages' `README.md` |

Scan with targeted reads, not a whole-repo dump: read the lockfile name, `package.json` scripts, one CI workflow, `.env.example`, and the PR template first. That is usually enough to write 80% of the file.

## 2. The six domains

Use the list to decide what to look for, then delete everything that turns out to be obvious once written down.

| Domain | Include | Leave out |
|---|---|---|
| Commands | Install, dev, build, test, single test, lint, typecheck, format, migrate — exactly as CI runs them | A full script table copied from `package.json`; the agent can read it |
| Test practice | Runner, file naming and location, fixtures, how to run a subset, what CI requires, known flaky areas | "Write good tests", coverage targets nobody enforces |
| Project map | Where a change of type X goes; generated vs hand-written; package boundaries that are not obvious from names | A 60-line tree, a module-by-module architecture tour |
| Code style | Rules a formatter or linter does not cover: naming, error handling, import direction, API versioning | Anything Prettier, ESLint, Ruff, gofmt already enforces — point at the command instead |
| Git and PR | Branch naming, commit convention, PR size and title, review requirements, what must be green before push | Generic GitHub advice |
| Boundaries | always / ask first / never (next section) | Aspirational process that nothing enforces |

If the repo has an unusual workflow, it belongs in the map or in boundaries, with the reason. "Why" is the part a new teammate cannot recover from code.

## 3. Boundaries in three tiers

Three tiers, because "be careful" collapses two very different cases.

- **Always** — mechanical, every task, cheap to verify: install before running scripts; run the formatter; add the changeset; update `.env.example` when adding a variable.
- **Ask first** — destructive, cross-cutting, or expensive to reverse: new dependency, schema migration, deleting or renaming a public export, changing CI, touching auth, infra, or payment code, a refactor across package boundaries.
- **Never** — hard prohibitions with no legitimate exception: commit `.env` or credentials, edit generated or vendored directories, force-push a shared branch, run migrations against shared environments, disable a test or lint rule to get CI green.

Each never rule should name the alternative, because a prohibition without a path forward gets worked around: "Never edit `packages/db/generated/`; change `schema.prisma` and run `pnpm db:generate`."

## 4. Placement and precedence

- **One toolchain, one root file.** A small repo does not need nesting.
- **Monorepo:** root gets global setup, the package map with one line each, cross-cutting workflow, and repo-wide boundaries. Each package gets a file only when its commands or rules differ. Do not put "web uses pnpm, api uses uv" in the root — that is what the child files are for.
- **Precedence is proximity:** the file nearest the edited path applies, and any explicit instruction in the current conversation outranks every file. Say so once in the root so a reader knows the rule.
- **One file per directory.** A chain of `AGENTS.md` inside one package rarely helps; consolidate.
- **Multiple names:** if `CLAUDE.md`, `GEMINI.md`, and `AGENTS.md` coexist, pick one as source and make the others point at it (symlink or a one-line include). Three copies will diverge within a month.

Layout example:

```
AGENTS.md                  # setup, commands that apply repo-wide, package map, global boundaries
apps/web/AGENTS.md         # Vite + pnpm commands, route conventions, design tokens
apps/api/AGENTS.md         # uv commands, schema-first handlers, migration rules
packages/db/AGENTS.md      # prisma workflow, "never edit generated client"
```

## 5. Template: single repository

Real content, no placeholders. Replace every line with a verified fact or delete it.

```markdown
# AGENTS.md

Node 20 + pnpm 9. Install: `pnpm install` at the repo root.
Copy `.env.example` to `.env`; the API reads `DATABASE_URL` at boot.

## Commands
- Dev: `pnpm dev` — web on :3000, api on :4000
- Test: `pnpm test`; one file: `pnpm test src/orders.test.ts`
- Check before push: `pnpm lint && pnpm typecheck && pnpm test` (same as CI)
- Build: `pnpm build`

## Layout
- `src/routes/` — one file per endpoint, schema validated with zod
- `src/db/schema.ts` — source of truth; `src/db/migrations/` is generated, never hand-edit
- `src/components/` — presentational only; data fetching lives in `src/pages/`

## Conventions
- TypeScript strict. No `any` in exported signatures; use `unknown` + a parser.
- Tests are colocated as `*.test.ts`. DB tests need `docker compose up -d db`.

## Git
- Branch `feat/<slug>` or `fix/<slug>` from `main`; PR title `type(scope): summary`.
- Squash merge; the PR body keeps the "why".

## Boundaries
- Always: update `.env.example` when adding a variable; add a test beside new logic.
- Ask first: new dependencies, schema changes, anything under `infra/`.
- Never: commit `.env`, edit `src/db/migrations/`, push to `main`.
```

## 6. Template: monorepo

Root file — global only:

```markdown
# AGENTS.md

pnpm workspace (`pnpm-workspace.yaml`). Install once at the root: `pnpm install`.
The nearest AGENTS.md wins; instructions in the current conversation win over all of them.

## Packages
- `apps/web` — React 19 client (see `apps/web/AGENTS.md`)
- `apps/api` — Fastify + Python workers (see `apps/api/AGENTS.md`)
- `packages/ui` — shared components, published; breaking changes need a major bump
- `packages/db` — Prisma schema and migrations

## Repo-wide
- CI: `pnpm lint && pnpm typecheck && pnpm test`. Run the same three before pushing.
- Commits follow Conventional Commits; one logical change per PR.

## Boundaries
- Ask first: adding a dependency, changing `pnpm-workspace.yaml`, touching `infra/`.
- Never: commit secrets, edit `packages/db/generated/`, force-push `main`.
```

Package file — only what differs:

```markdown
# apps/api

Python 3.12 + uv; the web app lives in `apps/web` and is irrelevant here.
- Dev: `uv run fastapi dev`
- Test: `uv run pytest`; one test: `uv run pytest tests/test_orders.py::test_create`
- Migrations: `uv run alembic revision --autogenerate -m "<msg>"`; review the generated file before committing

Handlers are schema-first: define the Pydantic model in `app/schemas/`, then the route.
Never call the DB from a route — use a repository in `app/repos/`.
```

## 7. Weak vs strong

The right-hand column is not longer because it is more thorough; it is longer because it names a command or a boundary.

| Weak | Strong |
|---|---|
| Write clean code. | TypeScript strict; no `any` in exported signatures. |
| Run the tests. | `pnpm test`; one file: `pnpm test src/foo.test.ts`. |
| Format code properly. | `pnpm format` (Prettier). CI fails on unformatted files. |
| Follow the existing structure. | New endpoint: route in `src/routes/<name>.ts`, schema in `src/schemas/`, test beside it. |
| Be careful with the database. | Never run migrations against staging or prod. Generate locally, open a PR, ask in `#db` before merging. |
| Don't break anything. | `packages/core` is published; a breaking change needs a changeset and a major bump. |
| Use the package manager. | pnpm only — `package-lock.json` is not tracked; a stray npm install rewrites it. |
| A 60-line directory tree. | Three lines, only the non-obvious routing (`handlers → services → repos`). |

Test each line by asking: could an agent follow this without asking a question, and would a reviewer notice if it did not? If both answers are no, the line is decoration.

## 8. Editing an existing file

- Read it whole before touching it, and read the repo enough to know which lines are still true.
- Keep the author's voice and section order unless they are the problem; wholesale replacement throws away knowledge you cannot reconstruct.
- Delete stale lines before adding new ones. A removed command is worth as much as an added one.
- Verify every command you keep, not only the ones you add. Old files are where invented commands hide.
- Propose a diff-sized change, and list separately the things you could not verify.
- If the file is over budget, the fix is usually deletion plus one level of nesting, not shortening every sentence.

## 9. Anti-patterns

- **Pasted README** — two copies that drift; the agent reads both and gets two answers.
- **Template with placeholders** — `<your-test-command>` is shipped as if it were knowledge.
- **Invented commands** — a plausible `pnpm test:e2e` that does not exist; the agent runs it, fails, and loses trust in the file.
- **Task-level instructions** — "for this refactor use the strategy pattern" belongs in the conversation, not in a repository file.
- **Contradictions across levels** — root says npm, package says pnpm; the agent picks one at random.
- **Architecture tour** — prose that belongs in `docs/`, read once by a human; link it instead.
- **Slogans** — "be thorough", "think step by step", "act as a senior engineer".
- **Unenforceable policy** — a "never" that no CI check, hook, or permission backs.
- **Stale** — a script renamed two releases ago is still documented; worse than silence, because it is trusted.
