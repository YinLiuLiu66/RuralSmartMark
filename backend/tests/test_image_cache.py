import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ruralsmartmark.services.image_cache import cleanup_image_cache


def _png(path: Path, size: int = 16) -> None:
    path.write_bytes(b"x" * size)


def _age(path: Path, days: int) -> None:
    stamp = (datetime.now(UTC) - timedelta(days=days)).timestamp()
    os.utime(path, (stamp, stamp))


def test_cleanup_removes_expired_png(tmp_path: Path):
    old = tmp_path / "old.png"
    fresh = tmp_path / "fresh.png"
    note = tmp_path / "note.txt"
    _png(old)
    _png(fresh)
    note.write_text("keep")
    _age(old, 40)

    result = cleanup_image_cache(tmp_path, max_age_days=30)

    assert result.scanned == 2
    assert result.removed == 1
    assert not old.exists()
    assert fresh.exists()
    assert note.exists()


def test_cleanup_enforces_size_limit_oldest_first(tmp_path: Path):
    oldest = tmp_path / "oldest.png"
    middle = tmp_path / "middle.png"
    newest = tmp_path / "newest.png"
    for path in (oldest, middle, newest):
        _png(path, size=100)
    _age(oldest, 3)
    _age(middle, 2)
    _age(newest, 1)

    result = cleanup_image_cache(tmp_path, max_age_days=30, max_bytes=150)

    assert result.removed == 2
    assert result.kept == 1
    assert newest.exists()
    assert not oldest.exists()
    assert not middle.exists()


def test_dry_run_keeps_files(tmp_path: Path):
    old = tmp_path / "old.png"
    _png(old)
    _age(old, 40)

    result = cleanup_image_cache(tmp_path, max_age_days=30, dry_run=True)

    assert result.removed == 1
    assert old.exists()
