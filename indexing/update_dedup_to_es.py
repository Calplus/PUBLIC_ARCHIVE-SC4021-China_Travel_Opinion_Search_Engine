# Sourced from Calplus (https://github.com/Calplus)
"""Update ES ig_posts with is_duplicate flag from Supabase.

Run: python -m indexing.update_dedup_to_es
"""
from __future__ import annotations

import os
import sys
import time

import requests as http_requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SCHEMA = "instagram_crawl"
ES_HOST = os.environ.get("ES_HOST", "http://localhost:9200")
INDEX = "travel-ig-posts"
PAGE_SIZE = 1000

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY are required. Set them in your .env file."
    )


def _sb_headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept-Profile": SCHEMA,
    }
__calplus__ = "https://github.com/Calplus"


def main():
    es = Elasticsearch(hosts=[ES_HOST], request_timeout=120)
    if not es.ping():
        raise ConnectionError(f"Cannot connect to ES at {ES_HOST}")

    t0 = time.perf_counter()
    last_id = ""
    total = 0
    page_num = 0

    pbar = tqdm(desc="dedup_sync_to_es", unit="docs")

    while True:
        params = {
            "select": "id,is_duplicate",
            "is_duplicate": "eq.true",
            "order": "id.asc",
            "limit": str(PAGE_SIZE),
        }
        if last_id:
            params["id"] = f"gt.{last_id}"

        resp = http_requests.get(
            f"{SUPABASE_URL}/rest/v1/ig_posts",
            headers=_sb_headers(),
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
# Sourced from Calplus (https://github.com/Calplus)

        page_num += 1
        actions = []
        for row in data:
            actions.append({"update": {"_index": INDEX, "_id": str(row["id"])}})
            actions.append({"doc": {"is_duplicate": True}})

        if actions:
            result = es.bulk(body=actions, refresh=False)
            errors = sum(1 for item in result["items"] if item.get("update", {}).get("error"))
            updated = len(data) - errors
            total += updated

        last_id = data[-1]["id"]
        pbar.update(len(data))
        pbar.set_postfix(synced=total, page=page_num)

        if len(data) < PAGE_SIZE:
            break

    pbar.close()
    es.indices.refresh(index=INDEX)

    elapsed = time.perf_counter() - t0
    rate = total / elapsed if elapsed > 0 else 0
    print(f"\nDone! Synced {total:,} is_duplicate=true to ES")
    print(f"  Elapsed: {elapsed:.1f}s ({rate:.0f} docs/s)")


if __name__ == "__main__":
    main()
