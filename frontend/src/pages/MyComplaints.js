import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import { PriorityBadge, StatusBadge } from "../components/Badges";

export default function MyComplaints() {
  const [complaints, setComplaints] = useState([]);
  const [search, setSearch] = useState("");

  const load = async (q = "") => {
    const res = await client.get("/complaints", { params: q ? { search: q } : {} });
    setComplaints(res.data);
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="container">
      <div className="card">
        <h2>My Complaints</h2>
        <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
          <input
            placeholder="Search by ID, title, or keyword"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ marginBottom: 0 }}
          />
          <button className="btn" onClick={() => load(search)}>Search</button>
        </div>

        {complaints.length === 0 && <p style={{ color: "#6b7280" }}>No complaints yet. File your first one!</p>}

        <table>
          <thead>
            <tr><th>ID</th><th>Title</th><th>Priority</th><th>Status</th><th>Score</th><th></th></tr>
          </thead>
          <tbody>
            {complaints.map((c) => (
              <tr key={c.id}>
                <td>{c.complaint_code}</td>
                <td>{c.title}</td>
                <td><PriorityBadge priority={c.ai_priority} /></td>
                <td><StatusBadge status={c.status} /></td>
                <td>{c.ai_score}</td>
                <td><Link to={`/complaints/${c.id}`}>View →</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
