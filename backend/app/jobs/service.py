from __future__ import annotations

import threading
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.collection import Collection
from ..crawlers.threaded import ThreadedCrawler
from ..crawlers.async_crawler import AsyncCrawler

_progress: dict[str, str] = {}
_lock = threading.Lock()


def set_progress(job_id: str, message: str):
    with _lock:
        _progress[job_id] = message


def get_progress(job_id: str) -> str:
    with _lock:
        return _progress.get(job_id, "")


def clear_progress(job_id: str):
    with _lock:
        _progress.pop(job_id, None)


def _avg(times: list[float]) -> float:
    return round(sum(times) / len(times), 3) if times else 0.0


def _run_job(job_id: str, seed: str, max_pages: int, workers: int,
             repeats: int, jobs_col: Collection, results_col: Collection):
    jid = ObjectId(job_id)
    try:
        jobs_col.update_one({"_id": jid}, {"$set": {"status": "running"}})

        tc = ThreadedCrawler(seed, max_pages)
        ac = AsyncCrawler(seed, max_pages)

        set_progress(job_id, "Running single-threaded crawler…")
        single = [tc.crawl_single() for _ in range(repeats)]

        set_progress(job_id, "Running threaded crawler…")
        threaded = [tc.crawl_threaded(workers) for _ in range(repeats)]

        set_progress(job_id, "Running asyncio crawler…")
        async_times = [ac.crawl(workers) for _ in range(repeats)]

        single_r = [{"run": i + 1, "seconds": round(t, 3)} for i, t in enumerate(single)]
        thread_r = [{"run": i + 1, "seconds": round(t, 3)} for i, t in enumerate(threaded)]
        async_r  = [{"run": i + 1, "seconds": round(t, 3)} for i, t in enumerate(async_times)]

        avg_single = _avg(single)
        summary = {
            "single_thread": {"min": round(min(single), 3), "avg": avg_single, "max": round(max(single), 3)},
            "thread_pool":   {"min": round(min(threaded), 3), "avg": _avg(threaded), "max": round(max(threaded), 3), "speedup": round(avg_single / _avg(threaded), 2) if _avg(threaded) else 0},
            "asyncio":       {"min": round(min(async_times), 3), "avg": _avg(async_times), "max": round(max(async_times), 3), "speedup": round(avg_single / _avg(async_times), 2) if _avg(async_times) else 0},
        }

        results_col.insert_one({
            "job_id": jid,
            "single_thread": single_r,
            "thread_pool": thread_r,
            "asyncio": async_r,
            "summary": summary,
        })

        jobs_col.update_one({"_id": jid}, {"$set": {
            "status": "done",
            "completed_at": datetime.now(timezone.utc),
        }})
        set_progress(job_id, "done")

    except Exception as e:
        jobs_col.update_one({"_id": jid}, {"$set": {"status": "error", "error": str(e)}})
        set_progress(job_id, f"error:{e}")


def start_job(job_id: str, seed: str, max_pages: int, workers: int,
              repeats: int, jobs_col: Collection, results_col: Collection):
    set_progress(job_id, "Starting…")
    t = threading.Thread(
        target=_run_job,
        args=(job_id, seed, max_pages, workers, repeats, jobs_col, results_col),
        daemon=True,
    )
    t.start()
