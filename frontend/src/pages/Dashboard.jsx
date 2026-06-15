import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";
import "./Dashboard.css";

function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/jobs")
      .then((r) => setJobs(r.data))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id, e) {
    e.stopPropagation();
    if (!confirm("Delete this job and its results?")) return;
    await api.delete(`/jobs/${id}`);
    setJobs((prev) => prev.filter((j) => j._id !== id));
  }

  const doneJobs = jobs.filter((j) => j.status === "done");
  const fastestJob = doneJobs.length
    ? null
    : null;

  return (
    <div className="dashboard">
      <nav className="navbar">
        <span className="nav-logo">CrawlLab</span>
        <div className="nav-right">
          <span className="nav-email">{user?.email}</span>
          <button className="btn-ghost" onClick={logout}>Sign out</button>
        </div>
      </nav>

      <main className="main">
        <div className="page-header">
          <div>
            <h1>My Crawl Jobs</h1>
            <p className="page-sub">{jobs.length} total · {doneJobs.length} completed</p>
          </div>
          <button className="btn-primary" onClick={() => navigate("/jobs/new")}>
            + New Job
          </button>
        </div>

        {loading && <p className="muted-text">Loading…</p>}

        {!loading && jobs.length === 0 && (
          <div className="empty-state card">
            <p>No crawl jobs yet.</p>
            <Link to="/jobs/new">
              <button className="btn-primary" style={{ marginTop: 16 }}>Run your first crawl</button>
            </Link>
          </div>
        )}

        {jobs.length > 0 && (
          <div className="jobs-table card">
            <table>
              <thead>
                <tr>
                  <th>Seed URL</th>
                  <th>Pages</th>
                  <th>Workers</th>
                  <th>Repeats</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job._id} className="job-row" onClick={() => navigate(`/jobs/${job._id}`)}>
                    <td className="url-cell" title={job.seed_url}>{job.seed_url}</td>
                    <td>{job.max_pages}</td>
                    <td>{job.workers}</td>
                    <td>{job.repeats}</td>
                    <td><StatusBadge status={job.status} /></td>
                    <td>{new Date(job.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn-danger"
                        style={{ padding: "4px 10px", fontSize: 12 }}
                        onClick={(e) => handleDelete(job._id, e)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
