# Thread vs Async Crawler

Benchmarks three Python concurrency models against the same crawl workload and visualizes the results in a Flask dashboard.

| Approach | How it works |
|---|---|
| **Single-threaded** | Sequential requests — one page at a time |
| **ThreadPoolExecutor** | OS threads — multiple requests in parallel, GIL-bound |
| **asyncio + aiohttp** | Event loop — non-blocking I/O, no thread overhead |

## Setup

```bash
git clone <repo>
cd thread-vs-async-crawler
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` to configure the benchmark (seed URL, page count, workers, repeats). MongoDB is optional — leave `MONGODB_URI` blank to skip persistence.

## Run

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) and click **Run Benchmark**.

The dashboard runs all three crawlers, then displays:
- A summary table with min/avg/max times and speedup vs single-threaded
- An interactive Chart.js bar chart
- Raw timing for every individual run

## Project structure

```
├── app.py                  # Flask app and routes
├── crawlers/
│   ├── threaded.py         # Single-threaded and ThreadPoolExecutor crawlers
│   └── async_crawler.py    # asyncio + aiohttp crawler
├── benchmark/
│   └── runner.py           # Background thread, state tracking, result persistence
├── templates/
│   └── index.html          # Dashboard UI
├── static/
│   └── style.css           # Dark theme styles
└── results/
    └── raw_results.json    # Persisted between runs (gitignored)
```

## Key findings

Async consistently outperforms threaded for I/O-bound workloads at scale. Threading adds OS-level thread overhead and GIL contention; asyncio handles the same concurrency with a single thread via cooperative multitasking. Single-threaded is the baseline — purely sequential, no parallelism.

## Tech

Python · Flask · asyncio · aiohttp · ThreadPoolExecutor · BeautifulSoup · MongoDB (optional)
