import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const user = await login(email, password);
      if (user.role === "citizen") navigate("/complaints");
      else if (user.role === "officer") navigate("/officer");
      else navigate("/admin");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    }
  };

  return (
    <div className="container" style={{ maxWidth: 420 }}>
      <div className="card">
        <h2>Sign in</h2>
        {error && <div className="error-text">{error}</div>}
        <form onSubmit={handleSubmit}>
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <button className="btn" type="submit" style={{ width: "100%" }}>Sign in</button>
        </form>
        <p style={{ marginTop: 14, fontSize: "0.9rem" }}>
          New citizen? <Link to="/register">Register here</Link>
        </p>
        <p style={{ fontSize: "0.75rem", color: "#6b7280" }}>
          Demo accounts (run seed_data.py): admin@grievance.gov / admin123, officer.pwd@grievance.gov / officer123
        </p>
      </div>
    </div>
  );
}
