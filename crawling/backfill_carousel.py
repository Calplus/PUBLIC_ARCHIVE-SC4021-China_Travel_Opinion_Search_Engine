# Sourced from Calplus (https://github.com/Calplus)
"""Backfill carousel slides for existing ig_posts.

Finds all media_type=8 (carousel) posts that only have the cover image,
fetches full media info from IG API, and inserts each slide as a new row.

Usage:
    python3 backfill_carousel.py --cookies ig_cookies.json [--limit 500] [--skip-images]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SCHEMA = "instagram_crawl"
BUCKET = "ig-images"
IG_APP_ID = "936619743392459"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY are required. Set them in your .env file."
    )

log = logging.getLogger("backfill")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

http = requests.Session()
http.headers["User-Agent"] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


# ── Supabase helpers ──────────────────────────────────────────────

def _sb_headers(write: bool = False) -> dict:
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept-Profile": SCHEMA,
    }
    if write:
        h["Content-Profile"] = SCHEMA
    return h


def _load_cookie_file(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Cookie file not found: {path}")

    try:
        cookies = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in cookie file: {path}") from exc

    if not isinstance(cookies, dict):
        raise RuntimeError("Cookie file must contain a JSON object")

    session_id = str(cookies.get("sessionid") or "").strip()
    if not session_id:
        raise RuntimeError("Cookie file is missing required 'sessionid'")

    return cookies

__calplus__ = "https://github.com/Calplus"

def db_upsert(table: str, data: dict | list[dict]) -> bool:
    headers = _sb_headers(write=True)
    headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
    payload = data if isinstance(data, list) else [data]
    resp = http.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=headers,
        json=payload,
    )
    if resp.status_code not in (200, 201):
        log.warning(f"db_upsert {table}: {resp.status_code} {resp.text[:200]}")
    return resp.ok


def get_carousel_codes() -> list[str]:
    """Get all original shortcodes for carousel posts (media_type=8).

    Uses RPC-free approach: paginate through ALL ig_posts with media_type=8,
    filter slide IDs client-side.
    """
    headers = _sb_headers()
    codes = []
    # Paginate using code as cursor (code is indexed + unique)
    last_code = ""
    while True:
        params = {
            "select": "code",
            "media_type": "eq.8",
            "limit": "500",
            "order": "code",
        }
        if last_code:
            params["code"] = f"gt.{last_code}"
        resp = http.get(
            f"{SUPABASE_URL}/rest/v1/ig_posts",
            params=params,
            headers=headers,
            timeout=60,
        )
        if not resp.ok:
            log.warning(f"get_carousel_codes page: HTTP {resp.status_code} {resp.text[:200]}")
            # On timeout, wait and retry once
            if resp.status_code == 500:
                time.sleep(5)
                resp = http.get(
                    f"{SUPABASE_URL}/rest/v1/ig_posts",
                    params=params,
                    headers=headers,
                    timeout=60,
                )
                if not resp.ok:
                    log.error("Retry also failed, stopping pagination")
                    break
            else:
                break
        batch = resp.json()
        if not batch:
            break
        codes.extend(r["code"] for r in batch if r.get("code"))
        last_code = batch[-1]["code"]
        if len(batch) < 500:
            break
        if len(codes) % 5000 < 500:
            log.info(f"  ...fetched {len(codes)} carousel codes so far")
    # Deduplicate and filter out slide IDs (code_1, code_2 etc)
    seen = set()
    result = []
    for c in codes:
        # Skip slide IDs — they contain _ followed by digits (e.g. DT4yFvsEZKp_1)
        if "_" in c and c.rsplit("_", 1)[-1].isdigit():
            continue
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def get_existing_ids() -> set[str]:
    """Get all existing IDs to avoid duplicates."""
    headers = _sb_headers()
    ids = set()
    last_id = ""
    while True:
        params = {"select": "id", "limit": "1000", "order": "id"}
        if last_id:
            params["id"] = f"gt.{last_id}"
        resp = http.get(
            f"{SUPABASE_URL}/rest/v1/ig_posts",
            params=params,
            headers=headers,
            timeout=30,
        )
        if not resp.ok or not resp.json():
            break
        batch = resp.json()
        ids.update(r["id"] for r in batch if r.get("id"))
        last_id = batch[-1]["id"]
        if len(batch) < 1000:
            break
    return ids
# Sourced from Calplus (https://github.com/Calplus)


# ── IG API ────────────────────────────────────────────────────────

def shortcode_to_media_pk(code: str) -> int:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    pk = 0
    for char in code:
        pk = pk * 64 + alphabet.index(char)
    return pk


def fetch_media_info(code: str, cookies: dict) -> dict | None:
    """Fetch full media info for a post by shortcode."""
    media_pk = shortcode_to_media_pk(code)
    headers = {
        "User-Agent": http.headers["User-Agent"],
        "x-ig-app-id": IG_APP_ID,
        "x-csrftoken": cookies.get("csrftoken", ""),
        "x-requested-with": "XMLHttpRequest",
        "Accept": "*/*",
        "Referer": f"https://www.instagram.com/p/{code}/",
    }

    try:
        r = http.get(
            f"https://www.instagram.com/api/v1/media/{media_pk}/info/",
            headers=headers,
            cookies=cookies,
            timeout=15,
        )
    except requests.RequestException as e:
        log.warning(f"Request failed for {code}: {e}")
        return None

    if r.status_code == 429:
        return "rate_limited"
    if not r.ok:
        log.warning(f"HTTP {r.status_code} for {code}")
        return None

    try:
        data = r.json()
    except json.JSONDecodeError:
        log.warning(f"Invalid JSON for {code}")
        return None

    items = data.get("items", [])
    return items[0] if items else None


def get_best_image(media_item: dict) -> dict:
    images = (media_item.get("image_versions2") or {}).get("candidates", [])
    return max(images, key=lambda x: x.get("width", 0)) if images else {}


# ── Image download ────────────────────────────────────────────────

def upload_image(image_bytes: bytes, filename: str) -> str | None:
    resp = http.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filename}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "image/jpeg",
        },
        data=image_bytes,
    )
    if resp.ok or resp.status_code == 409:
        return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}"
    return None
_SOURCE_URL = "https://github.com/Calplus"


def download_and_store(image_url: str, image_id: str) -> str | None:
    if not image_url:
        return None
    try:
        resp = http.get(image_url, timeout=15)
        if resp.status_code != 200:
            return None
        return upload_image(resp.content, f"{image_id}.jpg")
    except Exception as e:
        log.warning(f"Image error {image_id}: {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Backfill carousel slides")
    parser.add_argument("--cookies", required=True, help="Path to cookies JSON")
    parser.add_argument("--limit", type=int, default=0, help="Max carousels to process (0=all)")
    parser.add_argument("--skip-images", action="store_true", help="Skip image downloads")
    args = parser.parse_args()

    cookie_path = Path(args.cookies)
    cookies = _load_cookie_file(cookie_path)
    session_id = str(cookies.get("sessionid") or "")
    log.info(f"Loaded cookies from {cookie_path} (sessionid: ...{session_id[-8:]})")

    # Step 1: Find carousel post codes
    log.info("Fetching carousel post codes from DB...")
    all_codes = get_carousel_codes()
    log.info(f"Found {len(all_codes)} unique carousel codes (media_type=8)")

    # Step 2: Get existing IDs to skip already-backfilled
    existing_ids = get_existing_ids()
    log.info(f"Existing IDs in DB: {len(existing_ids)}")

    # Filter to only carousels that haven't been expanded yet
    to_backfill = [c for c in all_codes if f"{c}_1" not in existing_ids]
    log.info(f"Need backfill: {len(to_backfill)} / {len(all_codes)} (rest already expanded)")

    if args.limit:
        to_backfill = to_backfill[:args.limit]
        log.info(f"Limited to {args.limit} carousels")

    if not to_backfill:
        log.info("Nothing to backfill!")
        return

    # Step 3: Process each carousel
    total_slides = 0
    errors = 0
    rate_limits = 0

    for i, code in enumerate(to_backfill):
        log.info(f"[{i+1}/{len(to_backfill)}] Fetching carousel {code}...")

        media = fetch_media_info(code, cookies)

        if media == "rate_limited":
            rate_limits += 1
            wait = random.uniform(60, 120)
            log.warning(f"Rate limited! Waiting {wait:.0f}s... (total: {rate_limits})")
            time.sleep(wait)
            media = fetch_media_info(code, cookies)
            if media == "rate_limited":
                log.error("Still rate limited after retry. Stopping.")
                break

        if not media or not isinstance(media, dict):
            errors += 1
            time.sleep(random.uniform(1, 2))
            continue

        carousel_items = media.get("carousel_media") or []
        if not carousel_items:
            log.info(f"  {code}: no carousel_media found (media_type={media.get('media_type')})")
            errors += 1
            time.sleep(random.uniform(1, 2))
            continue
# Source: github.com/Calplus

        # Extract parent post info from API response for slide metadata
        user = media.get("user") or {}
        caption_obj = media.get("caption") or {}
        caption = caption_obj.get("text") or ""
        location = media.get("location") or {}
        taken_at = media.get("taken_at")
        posted_at = None
        if taken_at:
            try:
                from datetime import datetime
                posted_at = datetime.fromtimestamp(taken_at).isoformat()
            except (ValueError, OSError):
                pass

        # Ensure user exists in ig_users (avoid FK constraint errors)
        username = user.get("username")
        if username:
            db_upsert("ig_users", {
                "username": username,
                "full_name": user.get("full_name") or "",
                "is_verified": user.get("is_verified", False),
            })

        slides_added = 0
        for idx, item in enumerate(carousel_items):
            if idx == 0:
                continue  # Cover image already exists as the original row

            slide_id = f"{code}_{idx}"
            if slide_id in existing_ids:
                continue

            best_img = get_best_image(item)
            if not best_img.get("url"):
                continue

            storage_url = None
            if not args.skip_images:
                storage_url = download_and_store(best_img["url"], slide_id)

            db_upsert("ig_posts", {
                "id": slide_id,
                "code": slide_id,  # code must be unique in DB, use slide_id
                "username": user.get("username"),
                "caption": caption,
                "hashtags": [t for t in re.findall(r"#\w+", caption)],
                "image_url": best_img["url"],
                "storage_url": storage_url,
                "media_type": item.get("media_type", 1),
                "likes": media.get("like_count") or 0,
                "comments_count": media.get("comment_count") or 0,
                "views": media.get("play_count") or media.get("view_count"),
                "location_name": location.get("name"),
                "location_lat": location.get("lat"),
                "location_lng": location.get("lng"),
                "posted_at": posted_at,
                "word_count": len(caption.split()),
            })

            existing_ids.add(slide_id)
            slides_added += 1
            total_slides += 1

            time.sleep(random.uniform(0.2, 0.5))

        log.info(f"  {code}: +{slides_added} slides (total in post: {len(carousel_items)})")

        # Rate-limit friendly delay between API calls
        time.sleep(random.uniform(1.5, 3.0))

        if (i + 1) % 50 == 0:
            log.info(f"=== Progress: {i+1}/{len(to_backfill)} carousels, +{total_slides} slides, {errors} errors ===")

    log.info("=" * 60)
    log.info(f"DONE! Processed {len(to_backfill)} carousels")
    log.info(f"New slides added: {total_slides}")
    log.info(f"Errors: {errors}")
    log.info(f"Rate limits hit: {rate_limits}")


if __name__ == "__main__":
    main()
