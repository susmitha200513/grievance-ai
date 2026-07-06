import React, { useEffect, useState } from "react";
import client from "../api/client";
import { PriorityBadge, StatusBadge } from "../components/Badges";

const NEXT_STATUS = {
  assigned: "accepted",
  accepted: "in_progress",
  in_progress: "completed",
};

export default function OfficerDashboard() {
  const [complaints, setComplaints] = useState([]);
  const [remarksMap, setRemarksMap] = useState({});

  const load = async () => {
    const res = await client.get("/complaints");
    setComplaints(res.data);
  };

  useEffect(() => { load(); }, []);

  const advance = async (complaint) => {
    const nextStatus = NEXT_STATUS[complaint.status];
    if (!nextStatus) return;
    await client.post(`/complaints/${complaint.id}/status`, {
      status: nextStatus,
      remarks: remarksMap[complaint.id] || "",
    });
    load();
  };

  return (
    <div className="container">
      <div className="card">
        <h2>Officer Dashboard</h2>
        <p style={{ color: "#6b7280" }}>Complaints assigned to you, sorted by AI priority score.</p>
        <table>
          <thead>
            <tr><th>ID</th><th>Title</th><th>Priority</th><th>Status</th><th>Remarks</th><th>Action</th></tr>
          </thead>
          <tbody>
            {complaints.map((c) => (
              <tr key={c.id}>
                <td>{c.complaint_code}</td>
                <td>{c.title}</td>
                <td><PriorityBadge priority={c.ai_priority} /></td>
                <td><StatusBadge status={c.status} /></td>
                <td>
                  <input
                    placeholder="Add remarks"
                    value={remarksMap[c.id] || ""}
                    onChange={(e) => setRemarksMap({ ...remarksMap, [c.id]: e.target.value })}
                    style={{ marginBottom: 0 }}
                  />
                </td>
                <td>
                  {NEXT_STATUS[c.status]
                    ? <button className="btn" onClick={() => advance(c)}>Mark {NEXT_STATUS[c.status].replace("_", " ")}</button>
                    : <span style={{ color: "#9ca3af" }}>—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
