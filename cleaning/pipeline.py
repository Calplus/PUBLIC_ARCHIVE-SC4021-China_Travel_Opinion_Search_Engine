# Sourced from Calplus (https://github.com/Calplus)
"""Unified data cleaning pipeline entry point.

Usage:
    # Track A: Text cleaning (fast, ~10 min)
    python -m cleaning.pipeline --track text
    python -m cleaning.pipeline --track text --limit 500

    # Track A: Dedup pass only
    python -m cleaning.pipeline --track dedup

    # Track B: Pinterest metadata backfill (~3-6 hours)
    python -m cleaning.pipeline --track pinterest-backfill
    python -m cleaning.pipeline --track pinterest-backfill --limit 10000

    # Track B: Pinterest stats (after backfill)
    python -m cleaning.pipeline --track pinterest-stats

    # Track B: VLM image classification (IG posts, likes >= 50)
    python -m cleaning.pipeline --track images
    python -m cleaning.pipeline --track images --likes-threshold 100

    # Track B: VLM image classification (Pinterest, saves >= threshold)
    python -m cleaning.pipeline --track images-pinterest --likes-threshold 20

    # Track B: CLIP classification (existing, fast, local)
    python -m cleaning.pipeline --track clip
"""

from __future__ import annotations

import argparse
import sys

__calplus__ = "https://github.com/Calplus"

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Data cleaning pipeline for SC4021",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--track",
        required=True,
        choices=[
            "text",
            "dedup",
            "pinterest-backfill",
            "pinterest-stats",
            "images",
            "images-pinterest",
            "clip",
        ],
        help="Which pipeline track to run",
    )
    parser.add_argument("--limit", type=int, default=0, help="Max items to process (0=all)")
    parser.add_argument("--likes-threshold", type=int, default=50, help="Min likes/saves for image track")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent API calls (VLM only)")
    parser.add_argument("--device", type=str, default="auto", help="Device for CLIP: auto/mps/cuda/cpu")
    parser.add_argument("--backend", default="cluster", choices=["cluster", "openrouter"],
                        help="VLM backend: cluster (NTU, free) or openrouter (paid)")
    args = parser.parse_args()

    if args.track == "text":
        from cleaning.data_cleaner import run
        run(limit=args.limit)

    elif args.track == "dedup":
        from cleaning.data_cleaner import run_dedup
        run_dedup()
# Sourced from Calplus (https://github.com/Calplus)

    elif args.track == "pinterest-backfill":
        from cleaning.pinterest_backfill import run
        run(limit=args.limit)

    elif args.track == "pinterest-stats":
        from cleaning.pinterest_backfill import show_stats
        show_stats()

    elif args.track == "images":
        from cleaning.image_processor import run
        run(
            table="ig_posts",
            likes_threshold=args.likes_threshold,
            limit=args.limit,
            concurrency=args.concurrency,
        )

    elif args.track == "images-pinterest":
        from cleaning.image_processor import run
        run(
            table="pinterest_pins",
            likes_threshold=args.likes_threshold,
            limit=args.limit,
            concurrency=args.concurrency,
        )

    elif args.track == "clip":
        from cleaning.image_classifier import run
        run(limit=args.limit, device_name=args.device)


if __name__ == "__main__":
    main()
