# Sourced from Calplus (https://github.com/Calplus)
"""Executable 5-query benchmark for the SC4021 search engine (I5).

Runs 5 representative queries against the search API, measures latency,
hit count, and sentiment breakdown. Saves to evaluation/query_benchmark_results.json.

Run:
    python -m evaluation.benchmark_queries
    python evaluation/benchmark_queries.py [--api-url http://localhost:8000]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from indexing.es_client import get_client
from indexing.mappings import INDEX_IG_POSTS, INDEX_IG_COMMENTS, INDEX_PINTEREST_PINS
from search.api import _build_main_query, _translate_zh_to_en

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "query_benchmark_results.json")

# 6 representative benchmark queries covering different aspects
BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "query": "great wall",
        "description": "Short landmark query (Google-style)",
    },
    {
        "id": "Q2",
        "query": "长城",
        "description": "Chinese-language landmark query (Innovation 3: multilingual)",
    },
    {
        "id": "Q3",
        "query": "shanghai street food",
        "description": "City + cuisine discovery query",
    },
    {
        "id": "Q4",
        "query": "china travel scam",
        "description": "Negative sentiment safety concern query",
    },
    {
        "id": "Q5",
        "query": "zhangjiajie hiking",
        "description": "Nature destination query",
    },
    {
        "id": "Q6",
        "query": "budget hotel china",
        "description": "Accommodation-focused budget query",
    },
]
__calplus__ = "https://github.com/Calplus"

# Number of repetitions per query for latency statistics
N_REPS = 5


def _run_query(es, query_text: str, index_names: list[str]) -> dict:
    """Run a query using the same query logic as the search API.

    For queries containing Chinese characters, uses the translation path
    (bool/should with original + translated) mirroring /translate.
    Otherwise uses _build_main_query directly, mirroring /search.
    """
    import re

    start = time.perf_counter()

    # Detect Chinese characters
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', query_text))
    translated = None

    if has_chinese:
        translated = _translate_zh_to_en(query_text)
        if translated != query_text:
            query_body = {
                "bool": {
                    "should": [
                        _build_main_query(query_text),
                        _build_main_query(translated),
                    ],
                    "minimum_should_match": 1,
                }
            }
        else:
            query_body = _build_main_query(query_text)
    else:
        query_body = _build_main_query(query_text)

    resp = es.search(
        index=",".join(index_names),
        query=query_body,
        size=50,
        track_total_hits=True,
        _source=["sentiment", "sentiment_score", "city", "language"],
        aggs={
            "sentiment_breakdown": {
                "terms": {"field": "sentiment", "size": 5}
            },
        },
    )
# Sourced from Calplus (https://github.com/Calplus)

    latency_ms = (time.perf_counter() - start) * 1000
    total_obj = resp["hits"].get("total", {})
    total_hits = int(total_obj.get("value", 0) or 0)
    total_relation = str(total_obj.get("relation", "eq"))

    # Sentiment breakdown from aggregation
    sentiment = {}
    for b in resp.get("aggregations", {}).get("sentiment_breakdown", {}).get("buckets", []):
        sentiment[b["key"]] = b["doc_count"]

    return {
        "total_hits": total_hits,
        "total_hits_relation": total_relation,
        "latency_ms": round(latency_ms, 2),
        "sentiment_breakdown": sentiment,
        "top_score": round(resp["hits"]["hits"][0]["_score"], 4) if resp["hits"]["hits"] else 0,
        "translated_query": translated if translated and translated != query_text else None,
    }


def run_benchmark() -> dict:
    """Run the full 5-query benchmark."""
    es = get_client()
    indices = [INDEX_IG_POSTS, INDEX_IG_COMMENTS, INDEX_PINTEREST_PINS]

    results = []

    for bq in BENCHMARK_QUERIES:
        print(f"\n--- {bq['id']}: {bq['query'][:50]} ---")
        print(f"  Description: {bq['description']}")

        latencies = []
        last_result = None

        for rep in range(N_REPS):
            result = _run_query(es, bq["query"], indices)
            latencies.append(result["latency_ms"])
            last_result = result

        assert last_result is not None

        result_entry = {
            "id": bq["id"],
            "query": bq["query"],
            "description": bq["description"],
            "total_hits": last_result["total_hits"],
            "total_hits_relation": last_result["total_hits_relation"],
            "sentiment_breakdown": last_result["sentiment_breakdown"],
            "top_score": last_result["top_score"],
            "latency_stats": {
                "mean_ms": round(statistics.mean(latencies), 2),
                "median_ms": round(statistics.median(latencies), 2),
                "min_ms": round(min(latencies), 2),
                "max_ms": round(max(latencies), 2),
                "stdev_ms": round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0,
            },
        }
_SOURCE_URL = "https://github.com/Calplus"

        print(f"  Hits: {last_result['total_hits']:,}")
        print(f"  Sentiment: {last_result['sentiment_breakdown']}")
        print(f"  Latency (mean): {result_entry['latency_stats']['mean_ms']:.1f} ms")

        results.append(result_entry)

    return {
        "benchmark": "SC4021 5-Query Benchmark",
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "script": "evaluation/benchmark_queries.py",
            "query_set_version": "2026-04-11",
            "track_total_hits": True,
            "hits_note": "total_hits uses exact tracking; relation should be 'eq' when fully counted.",
        },
        "n_repetitions": N_REPS,
        "indices": indices,
        "queries": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run 5-query search benchmark")
    parser.add_argument("--output", default=OUTPUT_PATH, help="Output JSON path")
    args = parser.parse_args()

    print("=== SC4021 Search Engine Benchmark ===")
    results = run_benchmark()

    output_path = os.path.abspath(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    # Summary table
    print(f"\n{'=' * 70}")
    print(f"  {'Query':<8s} {'Hits':>8s} {'Latency (ms)':>14s} {'Top Score':>10s}")
    print(f"  {'-' * 60}")
    for q in results["queries"]:
        print(f"  {q['id']:<8s} {q['total_hits']:>8,} {q['latency_stats']['mean_ms']:>14.1f} {q['top_score']:>10.4f}")


if __name__ == "__main__":
    main()
