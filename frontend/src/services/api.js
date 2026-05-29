import { clearAuth, getToken } from "./auth";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export function getApiBase() {
  return API_BASE;
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearAuth();
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Session expired. Please log in again.");
  }

  if (!response.ok) {
    let errorMessage = `Request failed: ${response.status}`;
    try {
      const data = await response.json();
      errorMessage = data.detail || errorMessage;
    } catch {
      const errorText = await response.text();
      if (errorText) errorMessage = errorText;
    }
    throw new Error(errorMessage);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response;
}

export const api = {
  health: () => request("/health"),
  register: (payload) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) =>
    request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/auth/me"),
  createResearch: (payload) =>
    request("/research", { method: "POST", body: JSON.stringify(payload) }),
  listResearch: () => request("/research"),
  getResearch: (id) => request(`/research/${id}`),
  runResearch: (id) => request(`/research/${id}/run`, { method: "POST" }),
  getProgress: (id) => request(`/research/${id}/progress`),
  getJob: (jobId) => request(`/jobs/${jobId}`),
  getReport: (id) => request(`/research/${id}/report`),
};

export async function downloadExport(researchId, format) {
  const token = getToken();
  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/research/${researchId}/export/${format}`, {
    headers,
  });

  if (response.status === 401) {
    clearAuth();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  if (!response.ok) {
    throw new Error(`Export failed: ${response.status}`);
  }

  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : `research-export.${format === "pdf" ? "pdf" : "md"}`;

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
