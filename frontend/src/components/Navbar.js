import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="navbar">
      <div className="brand">🏛️ Grievance AI Engine</div>
      <div>
        {!user && (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
        {user && user.role === "citizen" && (
          <>
            <Link to="/complaints">My Complaints</Link>
            <Link to="/file-complaint">File Complaint</Link>
          </>
        )}
        {user && user.role === "officer" && <Link to="/officer">Officer Dashboard</Link>}
        {user && user.role === "admin" && (
          <>
            <Link to="/admin">Admin Dashboard</Link>
            <Link to="/health-score">Constituency Health</Link>
          </>
        )}
        {user && <button onClick={handleLogout}>Logout ({user.name})</button>}
      </div>
    </div>
  );
}
