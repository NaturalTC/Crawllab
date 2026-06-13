import json
import threading
from pathlib import Path
from crawlers.threaded import ThreadedCrawler
from crawlers.async_crawler import AsyncCrawler

RESULTS_PATH = Path("results/raw_results.json")
RESULTS_PATH.parent.mkdir(exist_ok=True)

_lock = threading.Lock()
_state: dict = {
    "running": False,
    "progress": "",
    "error": None,
    "results": None,
}


def get_state() -> dict:
    with _lock:
        return dict(_state)


def _set(key: str, value) -> None:
    with _lock:
        _state[key] = value


def _avg(times: list[float]) -> float:
    return round(sum(times) / len(times), 3) if times else 0.0


def _run(seed: str, max_pages: int, workers: int, repeats: int,
         mongo_uri: str | None, db_name: str) -> None:
    _set("error", None)
    _set("results", None)

    try:
        tc = ThreadedCrawler(seed, max_pages, mongo_uri, db_name)
        ac = AsyncCrawler(seed, max_pages)

        _set("progress", "Running single-threaded crawler…")
        single = [tc.crawl_single() for _ in range(repeats)]

        _set("progress", "Running threaded crawler…")
        threaded = [tc.crawl_threaded(workers) for _ in range(repeats)]

        _set("progress", "Running asyncio crawler…")
        async_times = [ac.crawl(workers) for _ in range(repeats)]

        results = {
            "single_thread": [{"run": i + 1, "seconds": round(t, 3)} for i, t in enumerate(single)],
            "thread_pool":   [{"run": i + 1, "seconds": round(t, 3)} for i, t in enumerate(threaded)],
            "asyncio":       [{"run": i + 1, "seconds": round(t, 3)} for i, t in enumerate(async_times)],
            "summary": {
                "single_thread": {"min": round(min(single), 3), "avg": _avg(single),   "max": round(max(single), 3)},
                "thread_pool":   {"min": round(min(threaded), 3), "avg": _avg(threaded), "max": round(max(threaded), 3)},
                "asyncio":       {"min": round(min(async_times), 3), "avg": _avg(async_times), "max": round(max(async_times), 3)},
            },
            "config": {
                "seed": seed,
                "max_pages": max_pages,
                "workers": workers,
                "repeats": repeats,
            },
        }

        RESULTS_PATH.write_text(json.dumps(results, indent=2))
        _set("results", results)
        _set("progress", "Done")
    except Exception as e:
        _set("error", str(e))
        _set("progress", "Error")
    finally:
        _set("running", False)


def start_benchmark(seed: str, max_pages: int, workers: int, repeats: int,
                    mongo_uri: str | None, db_name: str) -> bool:
    with _lock:
        if _state["running"]:
            return False
        _state["running"] = True
        _state["progress"] = "Starting…"

    t = threading.Thread(
        target=_run,
        args=(seed, max_pages, workers, repeats, mongo_uri, db_name),
        daemon=True,
    )
    t.start()
    return True


def load_saved_results() -> dict | None:
    if RESULTS_PATH.exists():
        try:
            return json.loads(RESULTS_PATH.read_text())
        except Exception:
            return None
    return None
