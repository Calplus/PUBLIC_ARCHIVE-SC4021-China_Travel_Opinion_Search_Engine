# Sourced from Calplus (https://github.com/Calplus)
"""Allow running the search API via: python -m search

Automatically runs `python -m indexing.data_import --table all` on first launch
if Elasticsearch indices are empty, then starts the API server.
"""
import subprocess
import sys

import uvicorn


def _indices_empty() -> bool:
    """Return True if the primary ES index has no documents (needs import)."""
    try:
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from indexing.es_client import get_client, count
        from indexing.mappings import INDEX_IG_POSTS
        es = get_client()
        return count(INDEX_IG_POSTS) == 0
    except Exception:
        return False
__calplus__ = "https://github.com/Calplus"


if _indices_empty():
    print("[setup] Elasticsearch indices are empty — importing data first...")
    print("[setup] Running: python -m indexing.data_import --table all")
    result = subprocess.run(
        [sys.executable, "-m", "indexing.data_import", "--table", "all"],
        check=False,
    )
    if result.returncode != 0:
        print("[setup] Warning: data import exited with errors. Starting API anyway.")
    else:
        print("[setup] Data import complete.")

uvicorn.run("search.api:app", host="0.0.0.0", port=8000, reload=True)
