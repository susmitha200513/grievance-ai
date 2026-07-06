import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

const TYPES = [
  { value: "road", label: "Road Damage" },
  { value: "street_light", label: "Street Light" },
  { value: "illegal_dumping", label: "Illegal Dumping" },
  { value: "corruption", label: "Corruption" },
  { value: "water_leakage", label: "Water Leakage" },
];

export default function FileComplaint() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: "", description: "", complaint_type: "road", area: "", latitude: "", longitude: "",
  });
  const [image, setImage] = useState(null);
  const [error, setError] = useState("");
  const [duplicateWarning, setDuplicateWarning] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const useMyLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => {
      setForm((f) => ({ ...f, latitude: pos.coords.latitude, longitude: pos.coords.longitude }));
    });
  };

  const submit = async (forceNew = false) => {
    setError("");
    setSubmitting(true);
    try {
      const data = new FormData();
      Object.entries(form).forEach(([k, v]) => data.append(k, v));
      data.append("force_new", forceNew);
      if (image) data.append("image", image);

      const res = await client.post("/complaints", data, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
      setDuplicateWarning(null);
    } catch (err) {
      if (err.response?.status === 409) {
        setDuplicateWarning(err.response.data.detail);
      } else {
        setError(err.response?.data?.detail || "Something went wrong");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    submit(false);
  };

  if (result) {
    return (
      <div className="container" style={{ maxWidth: 600 }}>
        <div className="card">
          <h2>✅ Complaint Registered</h2>
          <p><strong>Complaint ID:</strong> {result.complaint_code}</p>
          <h3>AI Analysis</h3>
          <p><strong>Category:</strong> {result.ai_category}</p>
          <p><strong>Department:</strong> {result.ai_department}</p>
          <p><strong>Priority:</strong> {result.ai_priority}</p>
          <p><strong>AI Summary:</strong> {result.ai_summary}</p>
          <p><strong>Smart Score:</strong> {result.ai_score} / 100</p>
          <button className="btn" onClick={() => navigate("/complaints")}>View My Complaints</button>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ maxWidth: 600 }}>
      <div className="card">
        <h2>File a Complaint</h2>
        <p style={{ color: "#6b7280", fontSize: "0.9rem" }}>
          Our AI will automatically classify your complaint, assign a department, priority, and check for duplicates.
        </p>
        {error && <div className="error-text">{error}</div>}

        {duplicateWarning && (
          <div className="card" style={{ borderColor: "#ca8a04", background: "#fffbeb" }}>
            <strong>⚠️ Possible duplicate detected</strong>
            <p>{duplicateWarning.message}</p>
            <p style={{ fontSize: "0.85rem" }}>
              Matched complaint: {duplicateWarning.existing_complaint_code} (similarity: {Math.round(duplicateWarning.similarity * 100)}%)
            </p>
            <button className="btn secondary" onClick={() => setDuplicateWarning(null)}>OK, I'll check my complaints</button>
            {" "}
            <button className="btn" onClick={() => submit(true)}>File anyway (it's a different issue)</button>
          </div>
        )}

        {!duplicateWarning && (
          <form onSubmit={handleSubmit}>
            <label>Complaint Title</label>
            <input value={form.title} onChange={update("title")} required />

            <label>Complaint Type</label>
            <select value={form.complaint_type} onChange={update("complaint_type")}>
              {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>

            <label>Description</label>
            <textarea rows={5} value={form.description} onChange={update("description")} required
              placeholder="Describe the issue in detail — the AI reads this to classify and prioritize it." />

            <label>Area / Ward</label>
            <input value={form.area} onChange={update("area")} placeholder="e.g. Ward 3" />

            <label>Photo (optional)</label>
            <input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])} />

            <div style={{ marginBottom: 12 }}>
              <button type="button" className="btn secondary" onClick={useMyLocation}>📍 Use my current location</button>
              {form.latitude && <span style={{ marginLeft: 10, fontSize: "0.8rem", color: "#6b7280" }}>
                Lat {Number(form.latitude).toFixed(4)}, Lng {Number(form.longitude).toFixed(4)}
              </span>}
            </div>

            <button className="btn" type="submit" disabled={submitting}>
              {submitting ? "Analyzing with AI..." : "Submit Complaint"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
