import React, { useEffect, useState } from "react";
import client from "../api/client";

function statusColor(status) {
  switch (status) {
    case "Excellent": return "#16a34a";
    case "Good": return "#65a30d";
    case "Needs Attention": return "#ca8a04";
    default: return "#dc2626";
  }
}

export default function HealthScore() {
  const [data, setData] = useState([]);

  useEffect(() => {
    client.get("/dashboard/constituency-health-score").then((res) => setData(res.data));
  }, []);

  return (
    <div className="container">
      <div className="card">
        <h2>Constituency Health Score</h2>
        <p style={{ color: "#6b7280" }}>
          A 0–100 score per area combining unresolved complaints, safety issues, average resolution
          time, and citizen satisfaction — turning raw complaint data into a decision-support signal
          for constituency planning.
        </p>
        <table>
          <thead>
            <tr><th>Area</th><th>Health Score</th><th>Status</th><th>Total</th><th>Unresolved</th><th>Avg Resolution (days)</th><th>Avg Rating</th></tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.area}>
                <td>{row.area}</td>
                <td style={{ fontWeight: 700, color: statusColor(row.status) }}>{row.health_score}</td>
                <td><span style={{ color: statusColor(row.status), fontWeight: 600 }}>{row.status}</span></td>
                <td>{row.total_complaints}</td>
                <td>{row.unresolved_complaints}</td>
                <td>{row.avg_resolution_days ?? "—"}</td>
                <td>{row.avg_citizen_rating ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {data.length === 0 && <p style={{ color: "#6b7280" }}>No area data yet — file some complaints with an Area/Ward set.</p>}
      </div>
    </div>
  );
}
