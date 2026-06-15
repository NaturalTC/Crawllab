# CrawlLab

A fullstack web crawl analytics platform. Users register, submit crawl jobs against any seed URL, and get a live performance comparison across three Python concurrency strategies: single-threaded, ThreadPoolExecutor, and asyncio+aiohttp.

**Stack:** Flask · MongoDB · React · Recharts · JWT auth · SSE (real-time progress)

## Setup

**Prerequisites:** MongoDB running locally on port 27017, Node.js, Python 3.12+

### Backend

```bash
cd backend
cp .env.example .env        # edit JWT_SECRET_KEY if desired
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py               # http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

## API

| Method | Route | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | — | Create account |
| POST | `/api/auth/login` | — | Return JWT |
| GET | `/api/auth/me` | JWT | Current user |
| GET | `/api/jobs` | JWT | List user's jobs |
| POST | `/api/jobs` | JWT | Create + start job |
| GET | `/api/jobs/:id` | JWT | Job + results |
| DELETE | `/api/jobs/:id` | JWT | Delete job |
| GET | `/api/jobs/:id/stream` | JWT | SSE live progress |

## MongoDB collections

- `users` — email, bcrypt password hash, created_at
- `jobs` — seed_url, config, status, user_id, timestamps
- `results` — per-run timings and summary stats for all three strategies
