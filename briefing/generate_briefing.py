# Sourced from Calplus (https://github.com/Calplus)
"""Generate weekly Destination Radar briefing from Elasticsearch data.

Computes destination scores, identifies hidden gems vs oversaturated markets,
and outputs a markdown briefing ready to send to travel agencies.

Usage:
    python -m briefing.generate_briefing
    python -m briefing.generate_briefing --output briefing.md
"""
import argparse
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from indexing.es_client import get_client

DESTINATIONS = [
    "beijing", "shanghai", "guilin", "chengdu", "xian", "yunnan",
    "hangzhou", "guangzhou", "shenzhen", "hong kong", "zhangjiajie",
    "tibet", "great wall", "terracotta", "harbin", "suzhou",
    "lijiang", "sanya", "nanjing", "chongqing", "xiamen",
    "kunming", "dali", "huangshan", "jiuzhaigou", "lhasa",
]

EFFICIENCY_THRESHOLDS = {
    "hidden_gem": 3000,
    "growing": 1000,
    "established": 300,
}


def compute_destination_scores(es) -> list[dict]:
    """Query ES for each destination and compute scores."""
    results = []

    for dest in DESTINATIONS:
        resp = es.search(
            index="travel-ig-posts,travel-ig-comments,travel-pinterest-pins",
            query={"multi_match": {
                "query": dest,
                "fields": ["caption^2", "title^2", "text", "description", "hashtags^2"],
            }},
            size=0,
            aggs={
                "avg_likes": {"avg": {"field": "likes"}},
                "avg_sent": {"avg": {"field": "sentiment_score"}},
                "sentiment_breakdown": {"terms": {"field": "sentiment", "size": 5}},
                "top_cities": {"terms": {"field": "city", "size": 3}},
                "sources": {"terms": {"field": "_index", "size": 5}},
            },
            track_total_hits=True,
        )

        total = resp["hits"]["total"]["value"]
        if total == 0:
            continue

        avg_likes = resp["aggregations"]["avg_likes"]["value"] or 0
        avg_sent = resp["aggregations"]["avg_sent"]["value"] or 0.5
        efficiency = avg_likes / max(total, 1) * 1000

        # Sentiment breakdown
        sent_buckets = {
            b["key"]: b["doc_count"]
            for b in resp["aggregations"]["sentiment_breakdown"]["buckets"]
        }
        total_sent = sum(sent_buckets.values()) or 1
        pos_pct = sent_buckets.get("positive", 0) / total_sent * 100
        neg_pct = sent_buckets.get("negative", 0) / total_sent * 100
__calplus__ = "https://github.com/Calplus"

        # Classify
        if efficiency >= EFFICIENCY_THRESHOLDS["hidden_gem"]:
            signal = "HIDDEN GEM"
            emoji = "🔥"
        elif efficiency >= EFFICIENCY_THRESHOLDS["growing"]:
            signal = "GROWING"
            emoji = "📈"
        elif efficiency >= EFFICIENCY_THRESHOLDS["established"]:
            signal = "ESTABLISHED"
            emoji = "📊"
        else:
            signal = "SATURATED"
            emoji = "⚠️"

        # Sentiment health
        if avg_sent < 0.48:
            health = "🔴 LOW"
        elif avg_sent < 0.52:
            health = "🟡 MIXED"
        elif avg_sent < 0.56:
            health = "🟢 GOOD"
        else:
            health = "🟢 GREAT"

        results.append({
            "destination": dest.title(),
            "posts": total,
            "avg_likes": avg_likes,
            "avg_sentiment": avg_sent,
            "efficiency": efficiency,
            "signal": signal,
            "emoji": emoji,
            "health": health,
            "pos_pct": pos_pct,
            "neg_pct": neg_pct,
        })

    results.sort(key=lambda x: -x["efficiency"])
    return results


def generate_markdown(results: list[dict]) -> str:
    """Generate the weekly briefing as markdown."""
    now = datetime.now()
    week_num = now.isocalendar()[1]

    if not results:
        return "\n".join([
            f"# Destination Radar — Week {week_num}, {now.year}",
            f"*Generated {now.strftime('%Y-%m-%d %H:%M')} from 1.3M+ social media posts*",
            "",
            "---",
            "",
            "No destination data was returned from Elasticsearch for this run.",
            "",
            "Try again after indexing data or broadening destination keywords.",
            "",
            "---",
            "",
            "*Powered by SC4021 China Travel Opinion Search Engine*",
        ])
# Sourced from Calplus (https://github.com/Calplus)

    lines = [
        f"# Destination Radar — Week {week_num}, {now.year}",
        f"*Generated {now.strftime('%Y-%m-%d %H:%M')} from 1.3M+ social media posts*",
        "",
        "---",
        "",
        "## Top Opportunities (Hidden Gems)",
        "",
        "High engagement, low competition — **post about these NOW.**",
        "",
        "| Rank | Destination | Posts | Avg Likes | Efficiency | Sentiment | Signal |",
        "|------|-------------|-------|-----------|------------|-----------|--------|",
    ]

    gems = [r for r in results if r["signal"] == "HIDDEN GEM"]
    for i, r in enumerate(gems[:8], 1):
        lines.append(
            f"| {i} | **{r['destination']}** | {r['posts']:,} | {r['avg_likes']:,.0f} | "
            f"{r['efficiency']:,.0f} | {r['health']} | {r['emoji']} {r['signal']} |"
        )

    lines.extend([
        "",
        "**What this means:** These destinations get massive engagement relative to how",
        "few people are posting about them. Your content faces less competition here.",
        "",
        "---",
        "",
        "## Growing Opportunities",
        "",
        "| Destination | Posts | Avg Likes | Efficiency | Sentiment |",
        "|-------------|-------|-----------|------------|-----------|",
    ])

    growing = [r for r in results if r["signal"] == "GROWING"]
    for r in growing[:8]:
        lines.append(
            f"| {r['destination']} | {r['posts']:,} | {r['avg_likes']:,.0f} | "
            f"{r['efficiency']:,.0f} | {r['health']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Oversaturated (High Competition)",
        "",
        "Everyone is posting here. Hard to stand out unless your content is exceptional.",
        "",
        "| Destination | Posts | Avg Likes | Efficiency | Sentiment |",
        "|-------------|-------|-----------|------------|-----------|",
    ])

    saturated = [r for r in results if r["signal"] in ("ESTABLISHED", "SATURATED")]
    for r in saturated[:8]:
        lines.append(
            f"| {r['destination']} | {r['posts']:,} | {r['avg_likes']:,.0f} | "
            f"{r['efficiency']:,.0f} | {r['health']} |"
        )

    # Sentiment alerts
    low_sent = [r for r in results if r["avg_sentiment"] < 0.50]
    if low_sent:
        lines.extend([
            "",
            "---",
            "",
            "## Sentiment Alerts",
            "",
            "These destinations have below-average sentiment. Investigate before promoting.",
            "",
        ])
        for r in low_sent:
            lines.append(
                f"- **{r['destination']}** — sentiment {r['avg_sentiment']:.3f} "
                f"({r['neg_pct']:.0f}% negative). {r['health']}"
            )
_SOURCE_URL = "https://github.com/Calplus"

    # Action items
    top = gems[0] if gems else results[0]
    lines.extend([
        "",
        "---",
        "",
        "## This Week's Action Items",
        "",
        f"1. **Post about {top['destination']}** — highest efficiency score "
        f"({top['efficiency']:,.0f}). {top['posts']:,} posts but {top['avg_likes']:,.0f} avg likes.",
        f"2. **Avoid oversaturating** — Beijing/Shanghai/Chengdu are crowded. "
        f"Save your budget for hidden gems.",
        f"3. **Check alerts** — any destination with sentiment < 0.50 needs review "
        f"before you sell packages there.",
        "",
        "---",
        "",
        "*Powered by SC4021 China Travel Opinion Search Engine*",
        f"*Data: {sum(r['posts'] for r in results):,} analyzed posts across "
        f"{len(results)} destinations*",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate weekly destination briefing")
    parser.add_argument("--output", "-o", help="Output markdown file path")
    args = parser.parse_args()

    es = get_client()
    print("Computing destination scores...")
    results = compute_destination_scores(es)
    print(f"Analyzed {len(results)} destinations")

    md = generate_markdown(results)

    if args.output:
        with open(args.output, "w") as f:
            f.write(md)
        print(f"Briefing saved to {args.output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
