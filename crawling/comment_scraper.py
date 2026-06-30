# Sourced from Calplus (https://github.com/Calplus)
"""
Comment Scraper — Top 5 comments per post by likes.

Runs alongside the main daemon. Only 1 API call per post (1 page of ~20 comments),
then keeps the top 5 by likes. Efficient and sufficient for IR text corpus.

Usage:
    python comment_scraper.py                  # Default: top 2000 posts by likes
    python comment_scraper.py --limit 500      # Process 500 posts
    python comment_scraper.py --top-n 10       # Keep top 10 comments per post
"""

import argparse
import json
import logging
import random
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SCHEMA = "instagram_crawl"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY are required. Set them in your .env file."
    )

IG_APP_ID = "936619743392459"
COOKIE_FILE = Path(__file__).parent / "ig_cookies.json"
SHORTCODE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "comment_scraper.log"),
    ],
)
log = logging.getLogger(__name__)

http = requests.Session()

# ── Helpers ───────────────────────────────────────────────────────

def load_cookies(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Cookie file not found: {path}")

    try:
        with open(path) as f:
            cookies = json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in cookie file: {path}") from exc

    if not isinstance(cookies, dict):
        raise RuntimeError("Cookie file must contain a JSON object")

    session_id = str(cookies.get("sessionid") or "").strip()
    if not session_id:
        raise RuntimeError("Cookie file is missing required 'sessionid'")

    return cookies


def shortcode_to_media_pk(code: str) -> int:
    pk = 0
    for ch in code:
        pk = pk * 64 + SHORTCODE_ALPHABET.index(ch)
    return pk
__calplus__ = "https://github.com/Calplus"


def normalize_post_code(code: str) -> str:
    """Normalize post code, collapsing carousel suffixes like ABC123_1 -> ABC123."""
    normalized = (code or "").strip().split("_", 1)[0]
    if not normalized:
        return ""
    if any(ch not in SHORTCODE_ALPHABET for ch in normalized):
        return ""
    return normalized


def sb_headers(write: bool = False) -> dict:
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept-Profile": SCHEMA,
    }
    if write:
        h["Content-Profile"] = SCHEMA
        h["Content-Type"] = "application/json"
        h["Prefer"] = "resolution=merge-duplicates"
    return h


def ig_headers(cookies: dict, post_code: str) -> dict:
    # Rotate UA and fingerprint per request
    ua_pool = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    ]
    lang_pool = ["en-US,en;q=0.9", "en-GB,en;q=0.9", "en-US,en;q=0.9,zh;q=0.8"]
    return {
        "User-Agent": random.choice(ua_pool),
        "x-ig-app-id": IG_APP_ID,
        "x-csrftoken": cookies.get("csrftoken", ""),
        "x-requested-with": "XMLHttpRequest",
        "x-asbd-id": random.choice(["129477", "129478", "198387"]),
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": random.choice(lang_pool),
        "Referer": f"https://www.instagram.com/p/{post_code}/",
    }


# ── Core ──────────────────────────────────────────────────────────

def fetch_top_comments(post_code: str, cookies: dict, top_n: int = 0) -> list[dict]:
    """Fetch 1 page of comments, return all (or top N if specified)."""
    post_code = normalize_post_code(post_code)
    if not post_code:
        return []

    try:
        media_pk = shortcode_to_media_pk(post_code)
    except ValueError:
        log.warning(f"  {post_code}: invalid shortcode")
        return []

    headers = ig_headers(cookies, post_code)

    try:
        r = http.get(
            f"https://www.instagram.com/api/v1/media/{media_pk}/comments/",
            headers=headers,
            cookies=cookies,
            params={"can_support_threading": "true"},
            timeout=15,
        )
    except requests.exceptions.RequestException as e:
        log.warning(f"  {post_code}: request failed — {e}")
        return []
# Sourced from Calplus (https://github.com/Calplus)

    if r.status_code == 429:
        wait = random.uniform(60, 120)
        log.warning(f"  {post_code}: rate limited, waiting {wait:.0f}s...")
        time.sleep(wait)
        return []

    if r.status_code in (401, 403):
        wait = random.uniform(120, 300)
        log.warning(f"  {post_code}: HTTP {r.status_code} — session may be flagged, cooling down {wait:.0f}s...")
        time.sleep(wait)
        return []

    if not r.ok:
        log.warning(f"  {post_code}: HTTP {r.status_code}")
        return []

    if "json" not in r.headers.get("content-type", ""):
        log.warning(f"  {post_code}: got HTML instead of JSON — cooling down 60s...")
        time.sleep(60)
        return []

    result = r.json()
    raw_comments = result.get("comments", [])

    # Sort by likes descending, keep all (or top N if specified)
    raw_comments.sort(key=lambda c: c.get("comment_like_count", 0) or 0, reverse=True)
    top = raw_comments[:top_n] if top_n > 0 else raw_comments

    comments = []
    for c in top:
        user = c.get("user") or {}
        text = (c.get("text") or "").strip()
        if not text:
            continue

        posted_at = None
        created = c.get("created_at")
        if created:
            try:
                posted_at = datetime.fromtimestamp(created).isoformat()
            except (ValueError, OSError):
                pass

        comments.append({
            "id": str(c.get("pk", "")),
            "post_id": post_code,
            "username": user.get("username", ""),
            "text": text,
            "likes": c.get("comment_like_count") or 0,
            "posted_at": posted_at,
        })

    return comments


def upsert_comments(comments: list[dict]) -> bool:
    if not comments:
        return True
    try:
        # Ensure users exist
        users = [{"username": c["username"], "full_name": "", "is_verified": False}
                 for c in comments if c.get("username")]
        if users:
            http.post(
                f"{SUPABASE_URL}/rest/v1/ig_users",
                headers=sb_headers(write=True),
                json=users,
            )
        # Upsert comments
        resp = http.post(
            f"{SUPABASE_URL}/rest/v1/ig_comments",
            headers=sb_headers(write=True),
            json=comments,
        )
        return resp.ok
    except requests.exceptions.RequestException as e:
        log.warning(f"  Supabase write failed — {e}")
        return False
_SOURCE_URL = "https://github.com/Calplus"


def get_posts_needing_comments(limit: int) -> list[dict]:
    """Get posts with comments_count > 0 that we haven't scraped yet."""
    # Step 1: Get existing comment post_ids (cursor pagination)
    log.info("Loading already-scraped post IDs...")
    already_done = set()
    last_id = ""
    while True:
        params = {"select": "post_id", "limit": "1000", "order": "post_id"}
        if last_id:
            params["post_id"] = f"gt.{last_id}"
        resp = http.get(
            f"{SUPABASE_URL}/rest/v1/ig_comments",
            params=params,
            headers=sb_headers(),
            timeout=30,
        )
        if not resp.ok or not resp.json():
            break
        batch = resp.json()
        for row in batch:
            normalized = normalize_post_code(str(row.get("post_id") or ""))
            if normalized:
                already_done.add(normalized)
        last_id = batch[-1]["post_id"]
        if len(batch) < 1000:
            break
    log.info(f"Already scraped comments for {len(already_done)} posts")

    # Step 2: Get posts with comments_count > 0 (cursor pagination, order by id)
    log.info("Loading posts needing comments...")
    pending_posts = []
    seen_pending = set()
    last_code = ""
    while len(pending_posts) < limit:
        params = {
            "select": "code,comments_count,likes",
            "comments_count": "gt.0",
            "limit": "1000",
            "order": "code",
        }
        if last_code:
            params["code"] = f"gt.{last_code}"
        resp = http.get(
            f"{SUPABASE_URL}/rest/v1/ig_posts",
            params=params,
            headers=sb_headers(),
            timeout=30,
        )
        if not resp.ok:
            log.error(f"Failed to fetch posts: {resp.status_code} {resp.text[:200]}")
            break
        batch = resp.json()
        if not batch:
            break

        last_code = str(batch[-1].get("code") or "")
        if not last_code:
            break

        for post in batch:
            normalized_code = normalize_post_code(str(post.get("code") or ""))
            if not normalized_code:
                continue
            if normalized_code in already_done or normalized_code in seen_pending:
                continue

            pending_posts.append({
                "code": normalized_code,
                "comments_count": post.get("comments_count", 0),
                "likes": post.get("likes", 0) or 0,
            })
            seen_pending.add(normalized_code)

            if len(pending_posts) >= limit:
                break
# Source: github.com/Calplus

        if len(batch) < 1000:
            break

        if len(pending_posts) % 1000 < len(batch):
            log.info(f"  ...identified {len(pending_posts)} pending posts so far")

    to_scrape = sorted(pending_posts, key=lambda p: p.get("likes", 0), reverse=True)[:limit]
    log.info(
        "Pending posts after filtering: %d | Returning top %d by likes",
        len(pending_posts),
        len(to_scrape),
    )
    return to_scrape


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scrape top comments per post")
    parser.add_argument("--limit", type=int, default=2000, help="Max posts to process")
    parser.add_argument("--top-n", type=int, default=0, help="Top N comments per post (0=all)")
    parser.add_argument("--cookies", type=str, default=None, help="Path to cookie JSON file")
    args = parser.parse_args()

    running = True
    def stop(sig, frame):
        nonlocal running
        log.info("Stopping gracefully...")
        running = False
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    cookie_path = Path(args.cookies) if args.cookies else COOKIE_FILE
    cookies = load_cookies(cookie_path)
    session_id = str(cookies.get("sessionid") or "")
    log.info(f"Loaded cookies from {cookie_path} (sessionid: ...{session_id[-8:]})")
    posts = get_posts_needing_comments(args.limit)

    if not posts:
        log.info("Nothing to scrape!")
        return

    total_comments = 0
    total_posts = 0

    for i, post in enumerate(posts):
        if not running:
            break

        code = post["code"]
        comments = fetch_top_comments(code, cookies, top_n=args.top_n)

        if comments:
            upsert_comments(comments)
            total_comments += len(comments)
            log.info(f"[{i+1}/{len(posts)}] {code}: {len(comments)} top comments (post likes: {post.get('likes', 0):,})")
        else:
            log.info(f"[{i+1}/{len(posts)}] {code}: 0 comments")

        total_posts += 1

        # Anti-ban: variable delays + periodic long breaks
        if total_posts % 200 == 0:
            pause = random.uniform(120, 300)
            log.info(f"  🛌 Long break: {pause:.0f}s after {total_posts} posts")
            time.sleep(pause)
        elif total_posts % 50 == 0:
            pause = random.uniform(30, 60)
            log.info(f"  ☕ Anti-ban pause: {pause:.0f}s after {total_posts} posts")
            time.sleep(pause)
        else:
            time.sleep(random.uniform(3.0, 7.0))

    log.info("=" * 50)
    log.info(f"DONE — {total_posts} posts processed, {total_comments} comments stored")
    log.info(f"Average: {total_comments/total_posts:.1f} comments/post" if total_posts else "")


if __name__ == "__main__":
    main()
