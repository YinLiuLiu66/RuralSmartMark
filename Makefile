.PHONY: dev lan test e2e perf

dev:
	@set -e; \
	trap 'kill $$backend $$frontend 2>/dev/null || true' EXIT INT TERM; \
	(cd backend && uv run alembic upgrade head && uv run python -m ruralsmartmark.seed && uv run ruralsmartmark) & backend=$$!; \
	(cd frontend && pnpm dev) & frontend=$$!; \
	wait

lan:
	./scripts/lan-demo.sh

test:
	cd backend && uv run pytest && uv run ruff check .
	cd frontend && pnpm typecheck && pnpm lint && pnpm build

e2e:
	cd frontend && pnpm test:e2e

perf:
	cd frontend && pnpm test:perf
