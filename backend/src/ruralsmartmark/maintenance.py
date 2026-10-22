from __future__ import annotations

import argparse

from .config import get_settings
from .services.image_cache import cleanup_image_cache


def main() -> None:
    parser = argparse.ArgumentParser(description="智农云链本地维护命令")
    parser.add_argument("command", choices=["image-cache"])
    parser.add_argument("--max-age-days", type=int, default=30)
    parser.add_argument("--max-mb", type=int, default=512)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache_dir = get_settings().image_cache_path
    result = cleanup_image_cache(
        cache_dir,
        max_age_days=args.max_age_days,
        max_bytes=args.max_mb * 1024 * 1024,
        dry_run=args.dry_run,
    )
    action = "将删除" if args.dry_run else "已删除"
    print(f"缓存目录：{cache_dir}")
    print(
        f"扫描 {result.scanned} 个 PNG；{action} {result.removed} 个"
        f"（{result.freed_bytes / 1024 / 1024:.2f} MB）；保留 {result.kept} 个"
        f"（{result.kept_bytes / 1024 / 1024:.2f} MB）"
    )


if __name__ == "__main__":
    main()
