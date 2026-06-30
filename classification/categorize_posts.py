# Sourced from Calplus (https://github.com/Calplus)
"""13-category travel classification for Instagram posts and comments.

Assigns one or more travel categories to each document using keyword matching
on caption/text + hashtags. Categories are stored as a text[] array.

Consolidated from the original 23 categories into 13 user-facing groups.

Run:
    python -m classification.categorize_posts [--table ig_posts|ig_comments|all]
"""
import argparse
import os
import re
import time
from typing import Optional

import requests as http_requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SCHEMA = "instagram_crawl"
PAGE_SIZE = 500
MAX_RETRIES = 4
BASE_BACKOFF = 1.5

# ─── 13 Consolidated Travel Categories ───────────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "heritage_culture": [
        # historical_sites
        "temple", "palace", "ancient", "dynasty", "wall", "pagoda", "shrine",
        "mosque", "ruins", "unesco", "forbidden city", "great wall", "terracotta",
        "tomb", "mausoleum", "hutong", "courtyard", "pavilion", "fortress",
        "imperial", "ming", "qing", "tang", "han dynasty", "old town",
        "ancient town", "ancient city", "city wall", "drum tower", "bell tower",
        "ancestral hall", "stele", "stone carving", "archaeological", "relic",
        "cultural relic", "heritage site", "world heritage",
        # cultural_experiences
        "opera", "calligraphy", "silk", "ceramics", "pottery", "festival",
        "traditional", "ethnic", "minority", "tibetan", "uyghur", "miao",
        "dong", "costume", "folk", "ceremony", "ritual", "heritage",
        "performance", "craft", "artisan", "lantern festival", "dragon boat",
        "mid-autumn", "spring festival", "chinese new year", "lunar new year",
        "paper cutting", "shadow puppet", "embroidery", "batik", "tie-dye",
        "incense", "tea ceremony", "tea culture", "hanfu", "qipao",
        "lion dance", "dragon dance", "firecracker",
    ],
    "museums_art": [
        # museums
        "museum", "gallery", "exhibit", "exhibition", "artifact", "collection",
        "science museum", "history museum", "art museum",
        "antiquity", "national museum", "war museum", "memorial",
        "memorial hall", "art gallery", "contemporary art", "installation art",
        "sculpture", "curator",
        # architecture
        "skyline", "skyscraper", "modern", "futuristic", "architecture",
        "tower", "building", "light show", "neon", "cyberpunk", "urban",
        "design", "landmark", "art district", "street art", "graffiti",
        "mural", "creative", "installation", "bund", "pudong", "cbd",
        "colonial", "art deco", "brutalist", "glass", "steel",
        "observation deck", "bridge", "dam", "concrete", "facade",
    ],
    "food_dining": [
        # street_food
        "street food", "night market", "snack", "hawker", "food stall",
        "cheap eats", "food street", "bbq", "grill", "skewer", "wonton",
        "jianbing", "baozi", "snack street", "da pai dang", "local food",
        "lamb skewer", "chuanr", "stinky tofu", "tanghulu", "roujiamo",
        "xiaolongbao", "fried", "pancake", "bingfen", "malatang",
        "food market", "wet market", "morning market",
        # cuisine
        "restaurant", "cuisine", "dish", "meal", "delicious", "taste",
        "noodle", "dumpling", "hotpot", "sichuan", "cantonese", "dim sum",
        "spicy", "authentic", "local cuisine", "fine dining", "michelin",
        "gourmet", "tea house", "tea", "pu-erh", "peking duck",
        "mapo tofu", "kung pao", "congee", "fried rice",
        "spring roll", "mooncake", "steamed", "braised", "roasted",
        "hot pot", "seafood", "vegetarian", "vegan", "halal",
        "food tour", "cooking class", "recipe", "chef", "flavor",
    ],
    "nature_scenery": [
        # scenic_landscapes
        "landscape", "karst", "limestone", "cave", "river cruise", "scenic",
        "panorama", "viewpoint", "waterfall", "lake", "vista", "national park",
        "geopark", "natural wonder", "desert", "grassland", "steppe", "dune",
        "gobi", "silk road", "terraced fields", "rice terrace", "bamboo forest",
        "rainforest", "plateau", "prairie", "wetland", "glacier", "hot spring",
        "sunrise", "sunset", "golden hour", "mist", "fog", "reflection",
        "jiuzhaigou", "zhangjiajie", "guilin", "yangshuo", "danxia",
        # photography
        "photo", "photography", "instagrammable", "photogenic", "camera",
        "picture", "shot", "selfie", "scenic spot", "insta-worthy",
        "xiaohongshu", "drone", "timelapse", "panoramic", "portrait",
        "landscape photo", "lens", "tripod", "filter", "edit", "lightroom",
        "capture",
    ],
    "beaches_coastal": [
        "beach", "coast", "coastal", "ocean", "sea", "island", "surfing",
        "tropical", "resort", "seaside", "bay", "lagoon", "snorkeling",
        "diving", "marine", "coral", "sand", "wave", "tide", "boardwalk",
        "sanya", "hainan", "beihai", "weihai", "qingdao beach",
        "paradise island", "sunbathing",
    ],
    "hiking_adventure": [
        # hiking
        "hike", "hiking", "trail", "trek", "trekking", "mountain", "climb",
        "summit", "peak", "elevation", "basecamp", "ridge", "valley", "gorge",
        "canyon", "scenic walk", "mountaineering", "backpacking", "altitude",
        "camping", "overlook", "pass", "ascent", "descent", "switchback",
        "huangshan", "taishan", "emeishan", "huashan", "wutaishan",
__calplus__ = "https://github.com/Calplus"
        # winter_sports
        "ski", "skiing", "snowboard", "ice", "snow", "winter", "ice festival",
        "sledding", "frozen", "winter sports", "harbin ice",
        "ice sculpture", "ice world", "snow festival", "ice skating",
        "curling", "ice hockey", "snowfall", "frost", "sub-zero",
    ],
    "wildlife": [
        "panda", "wildlife", "animal", "bird", "birdwatching", "conservation",
        "zoo", "sanctuary", "nature reserve", "monkey", "endangered",
        "botanical", "garden", "flora", "fauna", "safari", "national park",
        "red panda", "golden monkey", "snow leopard", "crane", "dolphin",
        "butterfly", "aquarium", "breeding center", "research base",
    ],
    "nightlife_entertainment": [
        # nightlife
        "nightlife", "bar", "club", "clubbing", "pub", "lounge", "rooftop",
        "live music", "concert", "dj", "party", "entertainment", "karaoke",
        "craft beer", "cocktail", "nightclub", "disco", "happy hour",
        "speakeasy", "wine bar", "jazz", "nightspot", "after dark",
        "neon lights", "night scene", "night view",
        # shopping
        "shopping", "mall", "market", "souvenir", "boutique", "brand",
        "fashion", "luxury", "outlet", "wholesale", "tech", "electronics",
        "antique", "bazaar", "duty-free", "bargain", "silk market",
        "pearl market", "jade", "tea shop", "flea market", "vintage",
        "department store", "haul", "buy", "purchase",
    ],
    "wellness_relaxation": [
        # wellness
        "spa", "wellness", "traditional chinese medicine", "tcm",
        "acupuncture", "massage", "tai chi", "qigong", "meditation", "retreat",
        "relaxation", "health", "thermal", "martial arts", "kung fu",
        "shaolin", "wing chun", "yoga", "mindfulness", "detox", "healing",
        "herbal", "cupping", "moxibustion",
        # accommodation
        "hotel", "hostel", "room", "stay", "bed", "airbnb", "resort", "lodge",
        "guesthouse", "villa", "motel", "amenities", "lobby", "pool", "suite",
        "booking", "check-in", "checkout", "reception", "concierge",
        "dormitory", "bunk", "capsule hotel", "homestay", "boutique hotel",
        "five star", "luxury hotel", "budget hotel",
    ],
    "budget_safety": [
        # budget
        "price", "cost", "expensive", "cheap", "budget", "affordable",
        "worth", "money", "fee", "ticket", "free", "overpriced", "bargain",
        "yuan", "rmb", "discount", "deal", "value", "rip-off", "backpacker",
        "economical", "save money", "splurge", "mid-range",
        "hostel price", "entrance fee", "admission",
        # safety
        "safe", "unsafe", "scam", "theft", "crime", "police", "security",
        "danger", "robbery", "pickpocket", "fraud", "warning", "tourist trap",
        "careful", "caution", "risk", "emergency", "hospital", "insurance",
        "lost", "stolen", "harassment", "solo travel", "travel advisory",
    ],
    "transport_connectivity": [
        # transportation
        "train", "bus", "taxi", "flight", "metro", "subway", "uber", "didi",
        "drive", "airport", "station", "car rental", "ferry", "boat",
        "bicycle", "highway", "transit", "high-speed rail", "bullet train",
        "commute", "transfer", "ticket", "boarding", "luggage", "delay",
        "schedule", "route", "connection", "bike share", "e-bike", "scooter",
        # connectivity
        "wifi", "internet", "vpn", "signal", "4g", "5g", "wechat", "alipay",
        "app", "digital", "firewall", "great firewall",
        "mobile payment", "sim card", "data", "roaming", "esim", "hotspot",
        "qr code", "online", "download", "streaming", "censorship",
        # language_access
        "english", "language", "communication", "translate", "mandarin",
        "understand", "sign", "foreign", "foreigner", "expat", "culture shock",
        "barrier", "tourist-friendly", "bilingual", "signage", "speak",
        "google translate", "language barrier", "gesture", "phrasebook",
        "local language", "dialect", "putonghua",
    ],
    "weather_planning": [
        "weather", "air quality", "pollution", "smog", "aqi", "hot", "cold",
        "rain", "humid", "sunny", "cloudy", "snow", "temperature", "season",
        "haze", "dust", "pm2.5", "clear sky", "fog", "frost", "monsoon",
        "typhoon", "heatwave", "humidity", "climate", "forecast",
        "best time to visit", "rainy season", "dry season",
    ],
    "family_kids": [
        "family", "kids", "children", "theme park", "playground",
        "family-friendly", "disney", "waterpark", "zoo", "aquarium",
        "amusement", "child-friendly", "stroller", "baby", "toddler",
        "family trip", "family vacation", "disneyland", "ocean park",
        "happy valley", "chimelong", "legoland",
    ],
}

# Mapping from old 23 category keys → new 13 keys (for data migration)
OLD_TO_NEW_CATEGORY: dict[str, str] = {
    "historical_sites": "heritage_culture",
    "cultural_experiences": "heritage_culture",
    "museums": "museums_art",
    "architecture": "museums_art",
    "street_food": "food_dining",
    "cuisine": "food_dining",
    "scenic_landscapes": "nature_scenery",
    "photography": "nature_scenery",
    "beaches": "beaches_coastal",
    "hiking": "hiking_adventure",
    "winter_sports": "hiking_adventure",
    "wildlife": "wildlife",
    "nightlife": "nightlife_entertainment",
    "shopping": "nightlife_entertainment",
    "wellness": "wellness_relaxation",
    "accommodation": "wellness_relaxation",
    "budget": "budget_safety",
    "safety": "budget_safety",
    "transportation": "transport_connectivity",
    "connectivity": "transport_connectivity",
    "language_access": "transport_connectivity",
    "weather": "weather_planning",
    "family": "family_kids",
}
# Sourced from Calplus (https://github.com/Calplus)


def migrate_categories(old_cats: list[str]) -> list[str]:
    """Map a list of old 23-category keys to deduplicated new 13-category keys."""
    new = set()
    for c in old_cats:
        mapped = OLD_TO_NEW_CATEGORY.get(c, c)
        if mapped in CATEGORY_KEYWORDS:
            new.add(mapped)
    return sorted(new)

# Pre-compile regex patterns for each category (word boundary matching)
_CATEGORY_PATTERNS: dict[str, re.Pattern] = {}
for _cat, _keywords in CATEGORY_KEYWORDS.items():
    # Sort by length descending so longer phrases match first
    _sorted = sorted(_keywords, key=len, reverse=True)
    _escaped = [re.escape(kw) for kw in _sorted]
    _CATEGORY_PATTERNS[_cat] = re.compile(
        r"\b(?:" + "|".join(_escaped) + r")\b",
        re.IGNORECASE,
    )

# Category display labels
CATEGORY_LABELS: dict[str, str] = {
    "heritage_culture": "Heritage & Culture",
    "museums_art": "Museums & Art",
    "food_dining": "Food & Dining",
    "nature_scenery": "Nature & Scenery",
    "beaches_coastal": "Beaches & Coastal",
    "hiking_adventure": "Hiking & Adventure",
    "wildlife": "Wildlife",
    "nightlife_entertainment": "Nightlife & Entertainment",
    "wellness_relaxation": "Wellness & Relaxation",
    "budget_safety": "Budget & Safety",
    "transport_connectivity": "Getting Around",
    "weather_planning": "Weather & Planning",
    "family_kids": "Family & Kids",
}

# Category groups for frontend display
CATEGORY_GROUPS: dict[str, list[str]] = {
    "Explore": ["heritage_culture", "museums_art", "nature_scenery", "hiking_adventure"],
    "Lifestyle": ["food_dining", "nightlife_entertainment", "wildlife", "wellness_relaxation", "family_kids"],
    "Practical": ["budget_safety", "transport_connectivity", "beaches_coastal", "weather_planning"],
}


def detect_categories(
    text: Optional[str] = None,
    hashtags: Optional[list[str]] = None,
) -> list[str]:
    """Detect travel categories from text and/or hashtags.

    Args:
        text: Caption, comment text, or description.
        hashtags: List of hashtag strings (with or without #).

    Returns:
        Sorted list of matched category keys (e.g. ["cuisine", "street_food"]).
        Empty list if no match.
    """
    combined = ""
    if text:
        combined += text.lower() + " "
    if hashtags:
        combined += " ".join(h.lstrip("#").lower() for h in hashtags)

    if not combined.strip():
        return []

    matched = []
    for cat, pattern in _CATEGORY_PATTERNS.items():
        if pattern.search(combined):
            matched.append(cat)

    return sorted(matched)


# ─── Batch Processing ────────────────────────────────────────────────────────

def _supabase_headers(write: bool = False) -> dict:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept-Profile": SCHEMA,
        "Content-Type": "application/json",
    }
    if write:
        headers["Content-Profile"] = SCHEMA
        headers["Prefer"] = "return=minimal"
    return headers


def _patch_with_retry(url: str, headers: dict, json_data: dict, timeout: int = 30) -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = http_requests.patch(url, headers=headers, json=json_data, timeout=timeout)
            if resp.status_code in {429, 500, 502, 503, 504}:
                if attempt == MAX_RETRIES:
                    return False
                time.sleep(BASE_BACKOFF * (2 ** (attempt - 1)))
                continue
            return resp.status_code < 400
        except http_requests.RequestException:
            if attempt == MAX_RETRIES:
                return False
            time.sleep(BASE_BACKOFF * (2 ** (attempt - 1)))
    return False


def _upsert_batch(base_url: str, headers: dict, batch: list[dict], timeout: int = 60) -> int:
    """Bulk-upsert a list of row dicts (must include 'id') via Supabase merge.

    Sends one POST request for the whole batch instead of one PATCH per row.
    Returns number of rows written. Falls back to individual patches on error.
    """
    if not batch:
        return 0
    upsert_headers = {**headers, "Prefer": "resolution=merge-duplicates,return=minimal"}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = http_requests.post(base_url, headers=upsert_headers, json=batch, timeout=timeout)
            if resp.status_code in {429, 500, 502, 503, 504}:
                if attempt == MAX_RETRIES:
                    break
                time.sleep(BASE_BACKOFF * (2 ** (attempt - 1)))
                continue
            if resp.status_code < 400:
                return len(batch)
            break  # non-retryable client error — fall through to per-row fallback
        except http_requests.RequestException:
            if attempt == MAX_RETRIES:
                break
            time.sleep(BASE_BACKOFF * (2 ** (attempt - 1)))
    # Fallback: individual patches
    ok = 0
    for item in batch:
        row_id = item["id"]
        payload = {k: v for k, v in item.items() if k != "id"}
        if _patch_with_retry(f"{base_url}?id=eq.{row_id}", headers, payload):
            ok += 1
    return ok
_SOURCE_URL = "https://github.com/Calplus"


def run_categorization(table: str = "ig_posts", batch_size: int = PAGE_SIZE) -> int:
    """Categorize all rows in the given table where categories IS NULL.

    Args:
        table: "ig_posts", "ig_comments", or "pinterest_pins"
        batch_size: Number of rows to fetch per page.

    Returns:
        Number of rows updated.
    """
    # Per-table column config
    TABLE_CONFIG: dict[str, dict] = {
        "ig_posts":       {"text": "caption",      "extra": ",hashtags", "hashtags": True},
        "ig_comments":    {"text": "text",          "extra": "",         "hashtags": False},
        "pinterest_pins": {"text": "search_query",  "extra": ",title,description", "hashtags": False},
    }
    if table not in TABLE_CONFIG:
        raise ValueError(f"Unsupported table: {table}. Choose from {list(TABLE_CONFIG)}.")

    cfg = TABLE_CONFIG[table]
    text_field   = cfg["text"]
    use_hashtags = cfg["hashtags"]
    extra_cols   = cfg["extra"]

    base_url     = f"{SUPABASE_URL}/rest/v1/{table}"
    headers_read  = _supabase_headers(write=False)
    headers_write = _supabase_headers(write=True)

    total_updated = 0
    last_id = ""

    print(f"\n--- Categorizing {table} (categories IS NULL) ---")

    while True:
        params = {
            "select": f"id,{text_field}{extra_cols}",
            "categories": "is.null",
            "order": "id.asc",
            "limit": str(batch_size),
        }
        if last_id:
            params["id"] = f"gt.{last_id}"

        resp = http_requests.get(base_url, headers=headers_read, params=params, timeout=60)
        if resp.status_code != 200:
            print(f"  Fetch error {resp.status_code}: {resp.text[:200]}")
            break

        rows = resp.json()
        if not rows:
            break

        upsert_batch: list[dict] = []
        for row in rows:
            # Build text for category detection
            if table == "pinterest_pins":
                # Combine all text fields for richer signal
                text_val = " ".join(filter(None, [
                    row.get("search_query") or "",
                    row.get("title") or "",
                    row.get("description") or "",
                ]))
                hashtags_val: list[str] = []
            else:
                text_val = row.get(text_field, "") or ""
                hashtags_val = row.get("hashtags") or [] if use_hashtags else []
                if isinstance(hashtags_val, str):
                    hashtags_val = [h.strip() for h in hashtags_val.split(",") if h.strip()]

            categories = detect_categories(text=text_val, hashtags=hashtags_val)
            upsert_batch.append({"id": row["id"], "categories": categories or []})

        total_updated += _upsert_batch(base_url, headers_write, upsert_batch)
        last_id = rows[-1]["id"]
        print(f"  Processed {total_updated} rows (last_id={last_id})")

        if len(rows) < batch_size:
            break

    print(f"  Done: {total_updated} rows categorized in {table}")
    return total_updated


# ─── Server-Side SQL Generator ───────────────────────────────────────────────
# Source: github.com/Calplus

def generate_sql(table: str) -> str:
    """Generate a server-side SQL UPDATE for bulk category assignment.

    Outputs a single UPDATE that runs entirely inside PostgreSQL with no
    per-row network overhead. Run the output in the Supabase SQL Editor.
    Estimated time: ig_posts/ig_comments ~30s, pinterest_pins ~5-15min.
    """
    TABLE_TEXT_EXPR: dict[str, str] = {
        "ig_posts": (
            "lower(COALESCE(caption,'') || ' '"
            " || array_to_string(COALESCE(hashtags, '{}'), ' '))"
        ),
        "ig_comments": "lower(COALESCE(text,''))",
        "pinterest_pins": (
            "lower(COALESCE(search_query,'') || ' '"
            " || COALESCE(title,'') || ' ' || COALESCE(description,''))"
        ),
    }
    if table not in TABLE_TEXT_EXPR:
        raise ValueError(f"Unsupported table: {table}")

    text_expr = TABLE_TEXT_EXPR[table]

    # Escape PostgreSQL POSIX regex metacharacters inside dollar-quoted strings
    _pg_re_special = re.compile(r'([.+*?[\]{}()|^$\\])')

    cases: list[str] = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        conditions: list[str] = []
        for kw in keywords:
            if ' ' in kw:
                # Multi-word phrase: LIKE is precise (both words must be adjacent)
                esc = kw.replace("'", "''").replace("%", r"\%").replace("_", r"\_")
                conditions.append(f"t LIKE '%{esc}%'")
            else:
                # Single word: word-boundary regex prevents substring false-positives
                # e.g. \yice\y won't match "office", \ybar\y won't match "barber"
                # Dollar-quoting ($wb$...$wb$) avoids SQL backslash-escaping issues
                pg_esc = _pg_re_special.sub(r'\\\1', kw)
                conditions.append(f"t ~ $wb$\\y{pg_esc}\\y$wb$")
        condition = "\n                OR ".join(conditions)
        cases.append(
            f"            CASE WHEN ({condition})\n"
            f"                THEN '{cat}'::text END"
        )

    cases_block = ",\n".join(cases)
    return (
        f"-- Server-side category assignment for {table}\n"
        f"-- Run in Supabase SQL Editor (no Python / no network overhead)\n"
        f"-- Estimated time: ig_posts/ig_comments ~30s, pinterest_pins ~5-15min\n\n"
        f"UPDATE instagram_crawl.{table} AS tbl\n"
        f"SET categories = computed.cats\n"
        f"FROM (\n"
        f"    SELECT id,\n"
        f"        ARRAY_REMOVE(ARRAY[\n"
        f"{cases_block}\n"
        f"        ], NULL) AS cats\n"
        f"    FROM (\n"
        f"        SELECT id,\n"
        f"            {text_expr} AS t\n"
        f"        FROM instagram_crawl.{table}\n"
        f"        WHERE categories IS NULL\n"
        f"    ) src\n"
        f") computed\n"
        f"WHERE tbl.id = computed.id;\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Categorize posts/comments with 13 travel categories")
    parser.add_argument(
        "--table",
        choices=["ig_posts", "ig_comments", "pinterest_pins", "all"],
        default="all",
        help="Which table to categorize (default: all — ig_posts + ig_comments; pinterest_pins is separate)",
    )
    parser.add_argument(
        "--generate-sql",
        action="store_true",
        help="Generate server-side SQL UPDATE file(s) and write to cleaning/sql/ instead of running Python",
    )
    args = parser.parse_args()

    if args.generate_sql:
        tables_to_gen = (
            ["ig_posts", "ig_comments", "pinterest_pins"]
            if args.table == "all"
            else [args.table]
        )
        sql_dir = os.path.join(os.path.dirname(__file__), "..", "cleaning", "sql")
        for t in tables_to_gen:
            sql_path = os.path.join(sql_dir, f"categorize_{t}.sql")
            with open(sql_path, "w", encoding="utf-8") as f:
                f.write(generate_sql(t))
            print(f"Wrote: {sql_path}")
        return

    if args.table == "all":
        total = 0
        for t in ["ig_posts", "ig_comments"]:
            total += run_categorization(t)
        print(f"\nTotal categorized (ig tables): {total}")
        print(
            "\nNOTE: pinterest_pins requires the `categories` column to be added to Supabase first.\n"
            "      Run cleaning/sql/add_categories_column.sql in the Supabase SQL Editor, then:\n"
            "      python -m classification.categorize_posts --table pinterest_pins"
        )
    else:
        run_categorization(args.table)


if __name__ == "__main__":
    main()
