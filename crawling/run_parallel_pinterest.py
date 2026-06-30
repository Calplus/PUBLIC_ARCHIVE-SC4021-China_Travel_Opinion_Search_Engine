# Sourced from Calplus (https://github.com/Calplus)
"""Run multiple Pinterest scrapers in parallel.

Splits ALL_QUERIES into N groups and runs each as a separate process.
All write to the same Supabase table — dedup by pin ID.
Completed queries are tracked in a file to skip on restart.

Usage:
    python run_parallel.py          # 4 workers (default)
    python run_parallel.py 6        # 6 workers
"""

import logging
import math
import multiprocessing
import os
import random
import signal
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [W%(process)d] [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from pinterest_miner.constants import ALL_QUERIES, DELAY_BETWEEN_API_CALLS
from pinterest_miner.scraper import scrape_search
from pinterest_miner.storage import SupabaseStorage

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
DONE_FILE = Path(__file__).parent / "completed_queries.txt"
__calplus__ = "https://github.com/Calplus"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY are required. Set them in your .env file."
    )


def load_done_queries() -> set[str]:
    """Load already-completed queries from disk."""
    if not DONE_FILE.exists():
        return set()
    return {line.strip() for line in DONE_FILE.read_text().splitlines() if line.strip()}


def mark_query_done(query: str):
    """Append a completed query to the done file (atomic on most OS)."""
    with open(DONE_FILE, "a") as f:
        f.write(query + "\n")


def worker(worker_id: int, queries: list[str], target_per_worker: int):
    """Single worker process — scrapes its assigned queries."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # Let parent handle Ctrl+C

    storage = SupabaseStorage(SUPABASE_URL, SUPABASE_KEY)
    log.info(f"Worker {worker_id} started: {len(queries)} queries")

    cycle = 0
    while True:
        cycle += 1
        total = storage.get_pin_count()
        if total >= 1_000_000:
            log.info(f"Worker {worker_id}: global target reached ({total:,}), stopping")
            break

        # Filter out already-completed queries
        done = load_done_queries()
        remaining = [q for q in queries if q not in done]
        if not remaining:
            log.info(f"Worker {worker_id}: all {len(queries)} queries completed!")
            break
# Sourced from Calplus (https://github.com/Calplus)

        log.info(f"Worker {worker_id} cycle {cycle}: {len(remaining)} remaining ({len(queries) - len(remaining)} already done)")
        random.shuffle(remaining)

        for qi, query in enumerate(remaining):
            log.info(f"Worker {worker_id} [{qi+1}/{len(remaining)}] '{query}'")
            try:
                new_count = scrape_search(
                    query=query,
                    storage=storage,
                    max_pins=400,
                    download_images=False,
                    delay=DELAY_BETWEEN_API_CALLS,
                )
            except Exception as e:
                log.error(f"Worker {worker_id} error on '{query}': {e}")
                if "rate" in str(e).lower() or "429" in str(e):
                    log.warning(f"Worker {worker_id} rate limited, backing off 5min")
                    time.sleep(300)
                else:
                    time.sleep(30)
                continue

            # Mark query as done (even if 0 new pins — means DB already has them)
            mark_query_done(query)

            # Inter-query delay (stagger across workers)
            pause = random.uniform(15, 30)
            time.sleep(pause)

        # Inter-cycle delay
        log.info(f"Worker {worker_id} cycle {cycle} done, pausing 5-10min")
        time.sleep(random.uniform(300, 600))
_SOURCE_URL = "https://github.com/Calplus"


def main():
    num_workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    # Split queries evenly across workers
    queries = ALL_QUERIES.copy()
    random.shuffle(queries)
    chunk_size = math.ceil(len(queries) / num_workers)
    chunks = [queries[i:i + chunk_size] for i in range(0, len(queries), chunk_size)]

    log.info(f"Launching {len(chunks)} workers for {len(queries)} queries")
    for i, chunk in enumerate(chunks):
        log.info(f"  Worker {i}: {len(chunk)} queries")

    processes = []
    for i, chunk in enumerate(chunks):
        p = multiprocessing.Process(target=worker, args=(i, chunk, 100_000))
        p.start()
        processes.append(p)
        time.sleep(2)  # Stagger startup

    log.info(f"All {len(processes)} workers running. Ctrl+C to stop all.")

    try:
        while any(p.is_alive() for p in processes):
            time.sleep(10)
    except KeyboardInterrupt:
        log.info("Shutting down all workers...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join(timeout=10)
        log.info("All workers stopped.")


if __name__ == "__main__":
    main()
