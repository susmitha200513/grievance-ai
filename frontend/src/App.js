import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import Navbar from "./components/Navbar";
import ChatWidget from "./components/ChatWidget";
import Login from "./pages/Login";
import Register from "./pages/Register";
import FileComplaint from "./pages/FileComplaint";
import MyComplaints from "./pages/MyComplaints";
import ComplaintDetail from "./pages/ComplaintDetail";
import OfficerDashboard from "./pages/OfficerDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import HealthScore from "./pages/HealthScore";

function Protected({ roles, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/login" />;
  return children;
}

function AppRoutes() {
  const { user } = useAuth();
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Navbar />
        <Routes>
          <Route path="/" element={<Navigate to={user ? "/complaints" : "/login"} />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/file-complaint" element={<Protected roles={["citizen"]}><FileComplaint /></Protected>} />
          <Route path="/complaints" element={<Protected roles={["citizen"]}><MyComplaints /></Protected>} />
          <Route path="/complaints/:id" element={<Protected roles={["citizen", "officer", "admin"]}><ComplaintDetail /></Protected>} />

          <Route path="/officer" element={<Protected roles={["officer"]}><OfficerDashboard /></Protected>} />

          <Route path="/admin" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          <Route path="/health-score" element={<Protected roles={["admin", "officer"]}><HealthScore /></Protected>} />
        </Routes>
        {user && <ChatWidget />}
      </div>
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
