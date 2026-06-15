import { useState, useEffect, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import api from "../api/client";
import "./JobDetail.css";

const COLORS = { single_thread: "#94a3b8", thread_pool: "#60a5fa", asyncio: "#34d399" };
const LABELS = { single_thread: "Single-threaded", thread_pool: "ThreadPool", asyncio: "asyncio" };

function SpeedupBadge({ value }) {
  if (!value || value <= 1) return null;
  return <span className="speedup">{value}x faster</span>;
}

function SummaryCard({ label, color, data }) {
  return (
    <div className="summary-card card">
      <div className="summary-header">
        <span className="summary-dot" style={{ background: color }} />
        <span className="summary-label">{label}</span>
        <SpeedupBadge value={data?.speedup} />
      </div>
      <div className="summary-stats">
        <div><span className="stat-label">min</span><span className="stat-val">{data?.min}s</span></div>
        <div><span className="stat-label">avg</span><span className="stat-val">{data?.avg}s</span></div>
        <div><span className="stat-label">max</span><span className="stat-val">{data?.max}s</span></div>
      </div>
    </div>
  );
}

export default function JobDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [progress, setProgress] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const esRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const { data } = await api.get(`/jobs/${id}`);
        if (cancelled) return;
        setJob(data);
        setLoading(false);

        if (data.status === "running" || data.status === "pending") {
          startStream();
        }
      } catch {
        setError("Job not found");
        setLoading(false);
      }
    }

    function startStream() {
      const token = localStorage.getItem("token");
      const es = new EventSource(`/api/jobs/${id}/stream?token=${token}`);
      esRef.current = es;

      es.onmessage = (e) => {
        const { progress: msg } = JSON.parse(e.data);
        setProgress(msg);

        if (msg === "done" || msg.startsWith("error:")) {
          es.close();
          api.get(`/jobs/${id}`).then((r) => setJob(r.data));
        }
      };

      es.onerror = () => es.close();
    }

    load();
    return () => {
      cancelled = true;
      esRef.current?.close();
    };
  }, [id]);

  async function handleDelete() {
    if (!confirm("Delete this job and its results?")) return;
    await api.delete(`/jobs/${id}`);
    navigate("/dashboard");
  }

  if (loading) return <div className="detail-page"><p className="muted-text">Loading…</p></div>;
  if (error)   return <div className="detail-page"><p className="error-msg">{error}</p></div>;

  const isRunning = job.status === "pending" || job.status === "running";
  const results = job.results;
  const summary = results?.summary;

  const chartData = summary
    ? Object.entries(LABELS).map(([key, label]) => ({
        name: label,
        avg: summary[key]?.avg,
        key,
      }))
    : [];

  return (
    <div className="detail-page">
      <div className="detail-header">
        <Link to="/dashboard" className="back-link">← Dashboard</Link>
        <button className="btn-danger" style={{ fontSize: 13 }} onClick={handleDelete}>Delete</button>
      </div>

      <div className="job-meta card">
        <div className="meta-row">
          <span className="meta-url">{job.seed_url}</span>
          <span className={`badge badge-${job.status}`}>{job.status}</span>
        </div>
        <div className="meta-details">
          <span>{job.max_pages} pages</span>
          <span>{job.workers} workers</span>
          <span>{job.repeats} repeats</span>
          <span>{new Date(job.created_at).toLocaleString()}</span>
        </div>
      </div>

      {isRunning && (
        <div className="running-card card">
          <div className="running-indicator" />
          <p>{progress || "Starting crawlers…"}</p>
        </div>
      )}

      {job.status === "error" && (
        <div className="card" style={{ borderColor: "var(--error)" }}>
          <p className="error-msg">Error: {job.error}</p>
        </div>
      )}

      {summary && (
        <>
          <div className="summary-grid">
            {Object.entries(LABELS).map(([key, label]) => (
              <SummaryCard key={key} label={label} color={COLORS[key]} data={summary[key]} />
            ))}
          </div>

          <div className="chart-card card">
            <h2>Average crawl time (seconds)</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 13 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} unit="s" />
                <Tooltip
                  contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a", borderRadius: 6 }}
                  labelStyle={{ color: "#e2e8f0" }}
                  formatter={(v) => [`${v}s`, "avg"]}
                />
                <Bar dataKey="avg" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry) => (
                    <Cell key={entry.key} fill={COLORS[entry.key]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="runs-card card">
            <h2>Raw run times</h2>
            <table className="runs-table">
              <thead>
                <tr>
                  <th>Run</th>
                  {Object.entries(LABELS).map(([key, label]) => (
                    <th key={key}>{label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.single_thread.map((_, i) => (
                  <tr key={i}>
                    <td>#{i + 1}</td>
                    <td>{results.single_thread[i]?.seconds}s</td>
                    <td>{results.thread_pool[i]?.seconds}s</td>
                    <td>{results.asyncio[i]?.seconds}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
