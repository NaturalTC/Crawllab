import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";
import "./NewJob.css";

export default function NewJob() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    seed_url: "",
    max_pages: 30,
    workers: 10,
    repeats: 3,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function set(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post("/jobs", {
        ...form,
        max_pages: Number(form.max_pages),
        workers: Number(form.workers),
        repeats: Number(form.repeats),
      });
      navigate(`/jobs/${data._id}`);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to start job");
      setLoading(false);
    }
  }

  return (
    <div className="newjob-page">
      <div className="newjob-header">
        <Link to="/dashboard" className="back-link">← Dashboard</Link>
      </div>

      <div className="newjob-card card">
        <h1>New Crawl Job</h1>
        <p className="newjob-sub">
          CrawlLab will benchmark three concurrency strategies against your seed URL.
        </p>

        <form onSubmit={handleSubmit} className="newjob-form">
          <div className="field">
            <label>Seed URL</label>
            <input
              type="url" required autoFocus placeholder="https://en.wikipedia.org/wiki/Main_Page"
              value={form.seed_url}
              onChange={(e) => set("seed_url", e.target.value)}
            />
          </div>

          <div className="fields-row">
            <div className="field">
              <label>Max pages <span className="hint">5 – 100</span></label>
              <input
                type="number" min={5} max={100}
                value={form.max_pages}
                onChange={(e) => set("max_pages", e.target.value)}
              />
            </div>
            <div className="field">
              <label>Workers <span className="hint">1 – 20</span></label>
              <input
                type="number" min={1} max={20}
                value={form.workers}
                onChange={(e) => set("workers", e.target.value)}
              />
            </div>
            <div className="field">
              <label>Repeats <span className="hint">1 – 5</span></label>
              <input
                type="number" min={1} max={5}
                value={form.repeats}
                onChange={(e) => set("repeats", e.target.value)}
              />
            </div>
          </div>

          <div className="strategy-info">
            <div className="strategy">
              <span className="strategy-name">Single-threaded</span>
              <span className="strategy-desc">Sequential — baseline</span>
            </div>
            <div className="strategy">
              <span className="strategy-name">ThreadPoolExecutor</span>
              <span className="strategy-desc">OS threads, {form.workers} workers</span>
            </div>
            <div className="strategy">
              <span className="strategy-name">asyncio + aiohttp</span>
              <span className="strategy-desc">Event loop, non-blocking I/O</span>
            </div>
          </div>

          {error && <p className="error-msg">{error}</p>}

          <div className="form-actions">
            <button type="button" className="btn-ghost" onClick={() => navigate("/dashboard")}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Starting…" : "Run Benchmark"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
