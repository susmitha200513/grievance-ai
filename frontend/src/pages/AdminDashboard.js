import React, { useEffect, useState } from "react";
import client from "../api/client";
import { PriorityBadge, StatusBadge } from "../components/Badges";

export default function AdminDashboard() {
  const [overview, setOverview] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [officers, setOfficers] = useState([]);
  const [assignMap, setAssignMap] = useState({});

  const load = async () => {
    const [o, c, off] = await Promise.all([
      client.get("/dashboard/overview"),
      client.get("/complaints"),
      client.get("/officers"),
    ]);
    setOverview(o.data);
    setComplaints(c.data);
    setOfficers(off.data);
  };

  useEffect(() => { load(); }, []);

  const assign = async (complaintId) => {
    const officerId = assignMap[complaintId];
    if (!officerId) return;
    await client.post(`/complaints/${complaintId}/assign`, null, { params: { officer_id: officerId } });
    load();
  };

  return (
    <div className="container">
      {overview && (
        <div className="grid cols-4">
          <div className="card stat-box"><div className="value">{overview.total_complaints}</div><div className="label">Total Complaints</div></div>
          <div className="card stat-box"><div className="value">{overview.resolved_complaints}</div><div className="label">Resolved</div></div>
          <div className="card stat-box"><div className="value">{overview.pending_complaints}</div><div className="label">Pending</div></div>
          <div className="card stat-box"><div className="value">{overview.high_priority_complaints}</div><div className="label">High Priority</div></div>
        </div>
      )}

      <div className="card">
        <h3>All Complaints</h3>
        <table>
          <thead>
            <tr><th>ID</th><th>Title</th><th>Area</th><th>Dept</th><th>Priority</th><th>Status</th><th>Assign Officer</th></tr>
          </thead>
          <tbody>
            {complaints.map((c) => (
              <tr key={c.id}>
                <td>{c.complaint_code}</td>
                <td>{c.title}</td>
                <td>{c.area || "—"}</td>
                <td>{c.ai_department}</td>
                <td><PriorityBadge priority={c.ai_priority} /></td>
                <td><StatusBadge status={c.status} /></td>
                <td>
                  {c.assigned_officer_id ? "Assigned" : (
                    <>
                      <select
                        value={assignMap[c.id] || ""}
                        onChange={(e) => setAssignMap({ ...assignMap, [c.id]: e.target.value })}
                        style={{ marginBottom: 0, width: 140, display: "inline-block" }}
                      >
                        <option value="">Select officer</option>
                        {officers.map((o) => <option key={o.id} value={o.id}>{o.name} ({o.department})</option>)}
                      </select>
                      <button className="btn" style={{ marginLeft: 6, padding: "6px 10px" }} onClick={() => assign(c.id)}>Assign</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
