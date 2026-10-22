from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


@dataclass(slots=True)
class CacheCleanupResult:
    scanned: int
    removed: int
    freed_bytes: int
    kept: int
    kept_bytes: int


def _png_files(cache_dir: Path) -> list[tuple[Path, int, float]]:
    if not cache_dir.is_dir():
        return []
    files: list[tuple[Path, int, float]] = []
    for path in cache_dir.glob("*.png"):
        if not path.is_file():
            continue
        stat = path.stat()
        files.append((path, stat.st_size, stat.st_mtime))
    return files


def cleanup_image_cache(
    cache_dir: Path,
    *,
    max_age_days: int = 30,
    max_bytes: int = 512 * 1024 * 1024,
    dry_run: bool = False,
    now: datetime | None = None,
) -> CacheCleanupResult:
    files = _png_files(cache_dir)
    if not files:
        return CacheCleanupResult(0, 0, 0, 0, 0)

    current = now or datetime.now(UTC)
    cutoff = current - timedelta(days=max(0, max_age_days))
    remove: set[Path] = set()
    removed_bytes = 0

    for path, size, mtime in files:
        modified = datetime.fromtimestamp(mtime, UTC)
        if max_age_days >= 0 and modified < cutoff:
            remove.add(path)
            removed_bytes += size

    remaining = [(path, size, mtime) for path, size, mtime in files if path not in remove]
    total = sum(size for _, size, _ in remaining)
    for path, size, _ in sorted(remaining, key=lambda item: item[2]):
        if total <= max_bytes:
            break
        remove.add(path)
        removed_bytes += size
        total -= size

    if not dry_run:
        for path in remove:
            path.unlink(missing_ok=True)

    kept = len(files) - len(remove)
    return CacheCleanupResult(
        scanned=len(files),
        removed=len(remove),
        freed_bytes=removed_bytes,
        kept=kept,
        kept_bytes=total if not dry_run else sum(
            size for path, size, _ in files if path not in remove
        ),
    )
