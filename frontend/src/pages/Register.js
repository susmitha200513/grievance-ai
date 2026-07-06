import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "citizen", department: "" });
  const [error, setError] = useState("");

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const user = await register(form.name, form.email, form.password, form.role, form.department);
      navigate(user.role === "officer" ? "/officer" : "/complaints");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <div className="container" style={{ maxWidth: 420 }}>
      <div className="card">
        <h2>Create account</h2>
        {error && <div className="error-text">{error}</div>}
        <form onSubmit={handleSubmit}>
          <label>Full name</label>
          <input value={form.name} onChange={update("name")} required />
          <label>Email</label>
          <input type="email" value={form.email} onChange={update("email")} required />
          <label>Password</label>
          <input type="password" value={form.password} onChange={update("password")} required />
          <label>Account type</label>
          <select value={form.role} onChange={update("role")}>
            <option value="citizen">Citizen</option>
            <option value="officer">Officer</option>
          </select>
          {form.role === "officer" && (
            <>
              <label>Department</label>
              <input value={form.department} onChange={update("department")} placeholder="e.g. Public Works" />
            </>
          )}
          <button className="btn" type="submit" style={{ width: "100%" }}>Register</button>
        </form>
        <p style={{ marginTop: 14, fontSize: "0.9rem" }}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
