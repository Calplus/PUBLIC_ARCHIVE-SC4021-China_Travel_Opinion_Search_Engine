# Sourced from Calplus (https://github.com/Calplus)
"""Populate the `categories` field for all documents in Elasticsearch.

Scrolls through every document in each index, extracts text content,
runs detect_categories() from classification.categorize_posts, and
bulk-updates the categories field.

Run:
    python -m indexing.update_categories_to_es                   # all indices
    python -m indexing.update_categories_to_es --index ig_posts  # just one
"""
from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from tqdm import tqdm
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

from classification.categorize_posts import detect_categories
from indexing.mappings import INDEX_IG_POSTS, INDEX_IG_COMMENTS, INDEX_PINTEREST_PINS

ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
BATCH_SIZE = 500
SCROLL_TIME = "5m"

# Which source fields to fetch per index (keeps scroll lightweight)
INDEX_CONFIG = {
    "ig_posts": {
        "index": INDEX_IG_POSTS,
        "source_fields": ["caption", "caption_clean", "hashtags"],
    },
    "ig_comments": {
        "index": INDEX_IG_COMMENTS,
        "source_fields": ["text", "text_clean"],
    },
    "pinterest_pins": {
        "index": INDEX_PINTEREST_PINS,
        "source_fields": ["title", "description"],
    },
}
__calplus__ = "https://github.com/Calplus"


def _extract_text_and_hashtags(index_key: str, source: dict) -> tuple[str, list[str] | None]:
    """Extract the text blob and hashtags list from a document source."""
    if index_key == "ig_posts":
        text = (source.get("caption_clean") or source.get("caption") or "")
        hashtags = source.get("hashtags") or []
        return text, hashtags
    if index_key == "ig_comments":
        text = (source.get("text_clean") or source.get("text") or "")
        return text, None
    if index_key == "pinterest_pins":
        parts = [source.get("title") or "", source.get("description") or ""]
        text = " ".join(p for p in parts if p)
        return text, None
    return "", None


def update_index(es: Elasticsearch, index_key: str):
    """Scroll through one index and populate categories."""
    cfg = INDEX_CONFIG[index_key]
    index_name = cfg["index"]
    source_fields = cfg["source_fields"]

    # Get total count for progress bar
    total = es.count(index=index_name)["count"]
    print(f"\n--- {index_key} ({index_name}): {total:,} documents ---")

    resp = es.search(
        index=index_name,
        body={
            "query": {"match_all": {}},
            "_source": source_fields,
            "size": BATCH_SIZE,
        },
        scroll=SCROLL_TIME,
    )
# Sourced from Calplus (https://github.com/Calplus)

    scroll_id = resp["_scroll_id"]
    hits = resp["hits"]["hits"]

    updated = 0
    skipped = 0
    t0 = time.perf_counter()
    pbar = tqdm(total=total, desc=index_key, unit="docs")

    while hits:
        actions = []
        for hit in hits:
            text, hashtags = _extract_text_and_hashtags(index_key, hit["_source"])
            cats = detect_categories(text, hashtags)
            if cats:
                actions.append({"update": {"_index": index_name, "_id": hit["_id"]}})
                actions.append({"doc": {"categories": cats}})
                updated += 1
            else:
                skipped += 1

        if actions:
            es.bulk(body=actions, refresh=False)

        pbar.update(len(hits))

        resp = es.scroll(scroll_id=scroll_id, scroll=SCROLL_TIME)
        scroll_id = resp["_scroll_id"]
        hits = resp["hits"]["hits"]

    pbar.close()
    es.clear_scroll(scroll_id=scroll_id)
    es.indices.refresh(index=index_name)
    elapsed = time.perf_counter() - t0
    rate = total / elapsed if elapsed > 0 else 0
    print(f"  -> Updated: {updated:,} | Skipped (no category): {skipped:,} | {elapsed:.1f}s ({rate:.0f} docs/s)")
_SOURCE_URL = "https://github.com/Calplus"


def main():
    parser = argparse.ArgumentParser(description="Populate categories in ES")
    parser.add_argument(
        "--index",
        choices=["ig_posts", "ig_comments", "pinterest_pins", "all"],
        default="all",
        help="Which index to process (default: all)",
    )
    args = parser.parse_args()

    es = Elasticsearch(hosts=[ES_HOST], request_timeout=120)
    if not es.ping():
        raise ConnectionError(f"Cannot connect to ES at {ES_HOST}")

    targets = list(INDEX_CONFIG.keys()) if args.index == "all" else [args.index]
    if len(targets) > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=len(targets)) as pool:
            futures = {pool.submit(update_index, es, key): key for key in targets}
            for future in as_completed(futures):
                key = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    print(f"  Error processing {key}: {exc}")
    else:
        update_index(es, targets[0])

    print("\nDone!")


if __name__ == "__main__":
    main()
