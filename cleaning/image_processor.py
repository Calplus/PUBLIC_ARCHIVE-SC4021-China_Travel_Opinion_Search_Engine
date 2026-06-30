# Sourced from Calplus (https://github.com/Calplus)
"""VLM image classification + quality scoring.

Supports two backends:
  - NTU cluster: Qwen3-VL-32B via vLLM (FREE, requires NTU VPN)
  - OpenRouter:  Qwen2.5-VL-72B (paid fallback)

Processes ig_posts / pinterest_pins and writes structured metadata to Supabase.

Usage:
    # Default: use NTU cluster, classify IG posts with likes >= 50
    python -m cleaning.image_processor

    # Use OpenRouter instead
    python -m cleaning.image_processor --backend openrouter

    # Re-classify posts that failed (have processed_image_at but no category)
    python -m cleaning.image_processor --retry-failed

    # Pinterest pins
    python -m cleaning.image_processor --table pinterest_pins --likes-threshold 20

    # Custom concurrency
    python -m cleaning.image_processor --concurrency 20
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import base64

import httpx
import requests
from tqdm import tqdm

from config_processing import SUPABASE_URL, sb_headers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("image_processor")
logging.getLogger("httpx").setLevel(logging.WARNING)

API = f"{SUPABASE_URL}/rest/v1"

# ─────────────────────── Backend configs ───────────────────────

BACKENDS = {
    "cluster": {
        "url": "http://10.96.189.13:30000/v1/chat/completions",
        "model": "/tc3home/pa0008ng/models/Qwen3-VL-32B-Instruct",
        "api_key": "none",
        "timeout": 120,
        "base64": True,  # cluster can't fetch URLs, send images inline
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "qwen/qwen2.5-vl-72b-instruct",
        "api_key": None,  # loaded from env
        "timeout": 60,
    },
}

VLM_PROMPT = """You are classifying China travel images for a search engine dataset.
Return ONLY valid JSON (no markdown fences).

{
  "category": "<one of the 15 categories below>",
  "subcategory": "<specific subcategory or null>",
  "quality": <1-10 integer>,
  "description": "<1 sentence, what is shown>",
  "landmark": "<specific landmark/place name, or null>",
  "city": "<Chinese city name if identifiable, or null>",
  "mood": "<vibrant|serene|cozy|dramatic|rustic|modern|festive|mysterious|romantic|adventurous>",
  "is_professional": <true if professionally shot/edited, false if casual/UGC>,
  "has_text_overlay": <true if image contains designed text/graphics>
}

## 15 Categories (pick exactly one):

### Photography categories (the image is primarily a photo):
landscape — Natural scenery: mountains, lakes, rivers, waterfalls, terraces, deserts, grasslands, forests, beaches, aerial nature. Subcategories: mountain, water, karst, rice_terrace, desert, coast, forest, grassland, aerial, seasonal_bloom
heritage — Historic/traditional architecture: temples, pagodas, palaces, ancient towns, water towns, Great Wall, hutongs, tulou, villages. Subcategories: imperial, temple, ancient_town, great_wall, traditional_village, bridge_gate
cityscape — Modern urban scenes: skylines, neon nightscapes, street scenes, shopping streets, aerial city. Subcategories: skyline, night_city, street_scene, aerial_urban
food — All food/drink: street food, restaurant dishes, hot pot, tea, desserts, markets, cooking, regional cuisine. Subcategories: street_food, restaurant, hotpot, tea, dessert, market, cooking
people_kol — Person-centric: influencer portraits, traveler selfies, outfit shots, hanfu/costume fashion. The PERSON is the main subject.
people_group — Group photos: tour groups, family/friend travel, wedding/couple shoots. Multiple people as main subject.
people_local — Local life: ethnic minority portraits, street vendors, performers, monks, candid daily life.
accommodation — Hotels, resorts, rooms, pools, guesthouses, glamping, scenic views from rooms. Subcategories: luxury_hotel, boutique_inn, glamping, room_view
activity — Experiences: cultural workshops, hiking, cycling, cruises, cable cars, trains, festivals, night shows, spa. Subcategories: cultural, adventure, cruise, train, festival, wellness
wildlife — Animals/flora: giant pandas, birds, monkeys, flower close-ups. Subcategories: panda, bird, other_animal, flora
aesthetic — Abstract/artistic: reflections, symmetry, minimalist, atmospheric fog/mist, color-dominant compositions.

### Design/graphic categories (the image is primarily designed content with text/graphics):
poster — Promotional posters, flash sale banners, destination marketing visuals, branded tour advertisements, seasonal campaign graphics. Designed to attract/sell.
pricing — Price lists, tour package cards, cost breakdowns, comparison tables, "¥X,XXX per person" cards, booking info. Shows specific prices or package details.
itinerary — Route maps, day-by-day schedules, travel timelines, destination maps with pins, "Day 1→Day 2→..." flow charts, packing checklists, visa guides, how-to infographics.
infographic — General travel tips, top-N lists, fun facts, testimonial/review graphics, FAQ cards, destination overviews. Informational designed content that is NOT pricing or itinerary.
__calplus__ = "https://github.com/Calplus"

## Quality scoring guide:
1-3: blurry, bad lighting, random snapshot, low effort
4-5: decent phone photo, acceptable composition
6-7: good composition, nice lighting, intentional framing
8-9: professional quality, magazine-worthy, stunning
10: exceptional, award-level photography
For design/graphic categories: score based on design quality (layout, typography, visual hierarchy)."""

FETCH_BATCH = 50
DEFAULT_CONCURRENCY = 10


# ─────────────────────── API key helper ───────────────────────


def _get_api_key(backend: str) -> str:
    """Get API key for the selected backend."""
    if backend == "cluster":
        return "none"

    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    raise RuntimeError(
        "OPENROUTER_API_KEY not found. Set it in .env or use --backend cluster."
    )


# ─────────────────────── Supabase fetch/patch ───────────────────────


def _fetch_with_retry(url: str, max_retries: int = 5) -> list[dict]:
    """Fetch from Supabase with retry on 500 errors."""
    for attempt in range(max_retries):
        resp = requests.get(url, headers=sb_headers(), timeout=30)
        if resp.status_code >= 500 and attempt < max_retries - 1:
            wait = 3 * (attempt + 1)
            log.warning("Supabase %d, retrying in %ds...", resp.status_code, wait)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    return []


def fetch_unprocessed_ig(
    limit: int,
    likes_threshold: int,
    cursor: str | None = None,
    retry_failed: bool = False,
) -> list[dict]:
    """Fetch ig_posts needing VLM classification."""
    if retry_failed:
        url = (
            f"{API}/ig_posts"
            f"?processed_image_at=not.is.null"
            f"&image_category=is.null"
            f"&storage_url=not.is.null"
            f"&likes=gte.{likes_threshold}"
            f"&select=id,storage_url,caption,likes"
            f"&order=id.asc"
            f"&limit={limit}"
        )
    else:
        url = (
            f"{API}/ig_posts"
            f"?processed_image_at=is.null"
            f"&storage_url=not.is.null"
            f"&likes=gte.{likes_threshold}"
            f"&select=id,storage_url,caption,likes"
            f"&order=id.asc"
            f"&limit={limit}"
        )
    if cursor:
        url += f"&id=gt.{cursor}"
    return _fetch_with_retry(url)


def fetch_unprocessed_pinterest(
    limit: int,
    saves_threshold: int,
    cursor: str | None = None,
    retry_failed: bool = False,
) -> list[dict]:
    """Fetch pinterest_pins needing VLM classification."""
    if retry_failed:
        url = (
            f"{API}/pinterest_pins"
            f"?processed_image_at=not.is.null"
            f"&image_category=is.null"
            f"&image_url=not.is.null"
            f"&saves=gte.{saves_threshold}"
            f"&select=id,image_url,title"
            f"&order=id.asc"
            f"&limit={limit}"
        )
    else:
        url = (
            f"{API}/pinterest_pins"
            f"?processed_image_at=is.null"
            f"&image_url=not.is.null"
            f"&saves=gte.{saves_threshold}"
            f"&select=id,image_url,title"
            f"&order=id.asc"
            f"&limit={limit}"
        )
    if cursor:
        url += f"&id=gt.{cursor}"
    return _fetch_with_retry(url)
# Sourced from Calplus (https://github.com/Calplus)


def patch_batch(table: str, updates: list[dict]) -> int:
    """PATCH each row individually by id — reliable update."""
    if not updates:
        return 0
    ok = 0
    for row in updates:
        row_id = row.pop("id", None)
        if not row_id:
            continue
        for attempt in range(3):
            try:
                resp = requests.patch(
                    f"{API}/{table}?id=eq.{row_id}",
                    json=row,
                    headers=sb_headers(write=True),
                    timeout=15,
                )
                if resp.status_code >= 500 and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                resp.raise_for_status()
                ok += 1
                break
            except requests.RequestException as e:
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                else:
                    log.warning("PATCH %s failed: %s", row_id, e)
    return ok


# ─────────────────────── VLM classification ───────────────────────


async def _download_as_base64(
    image_url: str, client: httpx.AsyncClient,
) -> str | None:
    """Download image and return as data URI (base64)."""
    try:
        resp = await client.get(image_url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "image/jpeg")
        if ";" in ct:
            ct = ct.split(";")[0].strip()
        b64 = base64.b64encode(resp.content).decode()
        return f"data:{ct};base64,{b64}"
    except (httpx.HTTPError, Exception):
        return None


async def classify_image(
    image_url: str,
    client: httpx.AsyncClient,
    backend_cfg: dict,
    api_key: str,
    semaphore: asyncio.Semaphore,
) -> dict | None:
    """Send image to VLM, return parsed JSON.

    For cluster backend: downloads image → base64 → inline in request.
    For OpenRouter: passes URL directly (OpenRouter fetches it).
    """
    async with semaphore:
        # For cluster: download image and encode as base64
        use_base64 = backend_cfg.get("base64", False)
        if use_base64:
            img_data = await _download_as_base64(image_url, client)
            if not img_data:
                return None
            image_content = {"type": "image_url", "image_url": {"url": img_data}}
        else:
            image_content = {"type": "image_url", "image_url": {"url": image_url}}

        for attempt in range(3):
            try:
                resp = await client.post(
                    backend_cfg["url"],
                    json={
                        "model": backend_cfg["model"],
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    image_content,
                                    {"type": "text", "text": VLM_PROMPT},
                                ],
                            }
                        ],
                        "max_tokens": 300,
                        "temperature": 0,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=backend_cfg["timeout"],
                )
                if resp.status_code >= 500 and attempt < 2:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                resp.raise_for_status()
                data = resp.json()
_SOURCE_URL = "https://github.com/Calplus"

                content = data["choices"][0]["message"]["content"]
                # Strip markdown code fences if present
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]
                content = content.strip()

                return json.loads(content)

            except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
                if attempt < 2:
                    await asyncio.sleep(2)
                    continue
                log.debug("VLM call failed for %s: %s", image_url[:60], e)
                return None


async def process_batch_async(
    posts: list[dict],
    table: str,
    backend_cfg: dict,
    api_key: str,
    concurrency: int,
) -> list[dict]:
    """Process a batch of posts with async VLM calls."""
    now = datetime.now(timezone.utc).isoformat()
    semaphore = asyncio.Semaphore(concurrency)

    url_field = "storage_url" if table == "ig_posts" else "image_url"

    async with httpx.AsyncClient() as client:
        post_ids = []
        coros = []
        for post in posts:
            img_url = post.get(url_field)
            if not img_url:
                continue
            post_ids.append(post["id"])
            coros.append(classify_image(img_url, client, backend_cfg, api_key, semaphore))

        vlm_results = await asyncio.gather(*coros, return_exceptions=True)

        results = []
        for post_id, result in zip(post_ids, vlm_results):
            if isinstance(result, Exception):
                result = None
            update = {"id": post_id, "processed_image_at": now}

            if result:
                update["image_category"] = result.get("category")
                update["image_subcategory"] = result.get("subcategory")
                update["quality_score"] = result.get("quality")
                update["image_description"] = result.get("description")
                update["landmark"] = result.get("landmark")
                update["mood"] = result.get("mood")
                update["vlm_city"] = result.get("city")
                update["is_professional"] = result.get("is_professional")
                update["has_text_overlay"] = result.get("has_text_overlay")
            else:
                update["image_category"] = None
                update["image_subcategory"] = None
                update["quality_score"] = None
                update["image_description"] = None
                update["landmark"] = None
                update["mood"] = None
                update["vlm_city"] = None
                update["is_professional"] = None
                update["has_text_overlay"] = None

            results.append(update)

    return results


# ─────────────────────── main pipeline ───────────────────────


def count_target(table: str, likes_threshold: int, retry_failed: bool = False) -> int:
    """Count how many posts match the filter."""
    if retry_failed:
        if table == "ig_posts":
            filter_str = f"?processed_image_at=not.is.null&image_category=is.null&storage_url=not.is.null&likes=gte.{likes_threshold}"
        else:
            filter_str = f"?processed_image_at=not.is.null&image_category=is.null&image_url=not.is.null&saves=gte.{likes_threshold}"
    else:
        if table == "ig_posts":
            filter_str = f"?processed_image_at=is.null&storage_url=not.is.null&likes=gte.{likes_threshold}"
        else:
            filter_str = f"?processed_image_at=is.null&image_url=not.is.null&saves=gte.{likes_threshold}"

    try:
        resp = requests.get(
            f"{API}/{table}{filter_str}&select=id",
            headers={**sb_headers(), "Prefer": "count=exact"},
            params={"limit": "0"},
            timeout=30,
        )
        resp.raise_for_status()
        content_range = resp.headers.get("content-range", "")
        return int(content_range.split("/")[-1]) if "/" in content_range else 0
    except requests.RequestException:
        # Supabase count can fail on complex filters — estimate from a fetch
        log.warning("Count query failed, estimating from fetch...")
        resp = requests.get(
            f"{API}/{table}{filter_str}&select=id&limit=1000",
            headers=sb_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        rows = resp.json()
        # If we got 1000, there are probably more
        return len(rows) * 25 if len(rows) == 1000 else len(rows)
# Source: github.com/Calplus


def run(
    table: str = "ig_posts",
    likes_threshold: int = 50,
    limit: int = 0,
    concurrency: int = DEFAULT_CONCURRENCY,
    backend: str = "cluster",
    retry_failed: bool = False,
) -> None:
    """Main VLM classification loop."""
    backend_cfg = BACKENDS[backend]
    api_key = _get_api_key(backend)

    total_target = count_target(table, likes_threshold, retry_failed)
    mode = "RETRY failed" if retry_failed else "NEW"
    log.info(
        "[%s] %s | Target: %d %s (threshold=%d, concurrency=%d, backend=%s)",
        mode, backend_cfg["model"], total_target, table,
        likes_threshold, concurrency, backend,
    )

    target = min(limit, total_target) if limit else total_target
    processed = 0
    errors = 0
    cursor: str | None = None
    pbar = tqdm(total=target, desc="VLM classify", unit="imgs")

    while processed < target:
        fetch_size = min(FETCH_BATCH, target - processed)

        if table == "ig_posts":
            posts = fetch_unprocessed_ig(fetch_size, likes_threshold, cursor, retry_failed)
        else:
            posts = fetch_unprocessed_pinterest(fetch_size, likes_threshold, cursor, retry_failed)

        if not posts:
            log.info("No more unprocessed posts.")
            break

        cursor = posts[-1]["id"]

        updates = asyncio.run(
            process_batch_async(posts, table, backend_cfg, api_key, concurrency)
        )

        try:
            patch_batch(table, updates)
        except requests.RequestException as e:
            log.warning("Supabase upsert failed: %s", e)
            errors += 1

        ok = sum(1 for u in updates if u.get("image_category"))
        processed += len(updates)
        pbar.update(len(updates))
        log.info(
            "  classified %d/%d (total: %d, errors: %d)",
            ok, len(updates), processed, errors,
        )

        time.sleep(0.5)

    pbar.close()
    log.info("=== Done. Processed %d images (%d errors) ===", processed, errors)


# ─────────────────────── CLI ───────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="VLM image classifier")
    parser.add_argument("--table", default="ig_posts", choices=["ig_posts", "pinterest_pins"])
    parser.add_argument("--likes-threshold", type=int, default=50, help="Min likes/saves (default 50)")
    parser.add_argument("--limit", type=int, default=0, help="Max images to process (0=all)")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY, help="Concurrent API calls")
    parser.add_argument("--backend", default="cluster", choices=["cluster", "openrouter"],
                        help="VLM backend: cluster (NTU, free) or openrouter (paid)")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Re-classify posts that have processed_image_at but no image_category")
    args = parser.parse_args()

    run(
        table=args.table,
        likes_threshold=args.likes_threshold,
        limit=args.limit,
        concurrency=args.concurrency,
        backend=args.backend,
        retry_failed=args.retry_failed,
    )


if __name__ == "__main__":
    main()
