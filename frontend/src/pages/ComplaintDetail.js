import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client, { API_BASE } from "../api/client";
import { PriorityBadge, StatusBadge } from "../components/Badges";

const STAGES = ["registered", "assigned", "accepted", "in_progress", "completed"];

export default function ComplaintDetail() {
  const { id } = useParams();
  const [complaint, setComplaint] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);

  const load = async () => {
    const [c, t] = await Promise.all([
      client.get(`/complaints/${id}`),
      client.get(`/complaints/${id}/timeline`),
    ]);
    setComplaint(c.data);
    setTimeline(t.data);
  };

  useEffect(() => { load(); }, [id]);

  const submitFeedback = async () => {
    await client.post(`/complaints/${id}/feedback`, { rating, comment });
    setFeedbackSent(true);
  };

  if (!complaint) return <div className="container">Loading...</div>;

  return (
    <div className="container">
      <div className="card">
        <h2>{complaint.title} <span style={{ fontSize: "0.9rem", color: "#6b7280" }}>({complaint.complaint_code})</span></h2>
        <p>{complaint.description}</p>
        {complaint.image_path && (
          <img src={`${API_BASE}${complaint.image_path}`} alt="complaint" style={{ maxWidth: "100%", borderRadius: 8, marginBottom: 12 }} />
        )}
        <div className="grid cols-4">
          <div><label>Priority</label><PriorityBadge priority={complaint.ai_priority} /></div>
          <div><label>Status</label><StatusBadge status={complaint.status} /></div>
          <div><label>AI Department</label>{complaint.ai_department}</div>
          <div><label>Smart Score</label>{complaint.ai_score}</div>
        </div>
        <p style={{ marginTop: 10 }}><strong>AI Summary:</strong> {complaint.ai_summary}</p>
      </div>

      <div className="card">
        <h3>Progress Timeline</h3>
        <ul className="timeline">
          {STAGES.map((stage) => {
            const entry = timeline.find((t) => t.status === stage);
            const reached = !!entry;
            return (
              <li key={stage} style={{ opacity: reached ? 1 : 0.35 }}>
                <strong>{stage.replace("_", " ")}</strong>
                {entry?.remarks && <div style={{ fontSize: "0.85rem", color: "#6b7280" }}>{entry.remarks}</div>}
                {entry && <div style={{ fontSize: "0.75rem", color: "#9ca3af" }}>{new Date(entry.created_at).toLocaleString()}</div>}
              </li>
            );
          })}
        </ul>
      </div>

      {complaint.status === "completed" && !feedbackSent && (
        <div className="card">
          <h3>Rate the Resolution</h3>
          <label>Rating</label>
          <select value={rating} onChange={(e) => setRating(Number(e.target.value))}>
            {[5, 4, 3, 2, 1].map((r) => <option key={r} value={r}>{"⭐".repeat(r)}</option>)}
          </select>
          <label>Comment</label>
          <textarea rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
          <button className="btn" onClick={submitFeedback}>Submit Feedback</button>
        </div>
      )}
      {feedbackSent && <div className="success-text">Thank you for your feedback!</div>}
    </div>
  );
}
