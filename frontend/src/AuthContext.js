import React, { createContext, useState, useContext } from "react";
import client from "./api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });

  const persist = (token, user) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    setUser(user);
  };

  const login = async (email, password) => {
    const res = await client.post("/auth/login", { email, password });
    persist(res.data.access_token, res.data.user);
    return res.data.user;
  };

  const register = async (name, email, password, role, department) => {
    const res = await client.post("/auth/register", { name, email, password, role, department });
    persist(res.data.access_token, res.data.user);
    return res.data.user;
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
