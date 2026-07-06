import axios from "axios";

export const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

const client = axios.create({ baseURL: API_BASE });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
