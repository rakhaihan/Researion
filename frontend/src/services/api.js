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
  listResearch: (params = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        qs.set(key, String(value));
      }
    });
    const query = qs.toString();
    return request(`/research${query ? `?${query}` : ""}`);
  },
  getResearch: (id) => request(`/research/${id}`),
  runResearch: (id) => request(`/research/${id}/run`, { method: "POST" }),
  getProgress: (id) => request(`/research/${id}/progress`),
  getJob: (jobId) => request(`/jobs/${jobId}`),
  getReport: (id) => request(`/research/${id}/report`),
  getQuality: (id) => request(`/research/${id}/quality`),
  regenerateReport: (id) =>
    request(`/research/${id}/regenerate-report`, { method: "POST" }),
  listDocuments: () => request("/documents"),
  getDocument: (id) => request(`/documents/${id}`),
  getDocumentStatus: (id) => request(`/documents/${id}/status`),
  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),
  listWorkspaces: () => request("/workspaces"),
  getWorkspace: (id) => request(`/workspaces/${id}`),
  createWorkspace: (payload) =>
    request("/workspaces", { method: "POST", body: JSON.stringify(payload) }),
  updateWorkspace: (id, payload) =>
    request(`/workspaces/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteWorkspace: (id) => request(`/workspaces/${id}`, { method: "DELETE" }),
  listWorkspaceMembers: (id) => request(`/workspaces/${id}/members`),
  addWorkspaceMember: (id, payload) =>
    request(`/workspaces/${id}/members`, { method: "POST", body: JSON.stringify(payload) }),
  updateWorkspaceMember: (workspaceId, memberId, payload) =>
    request(`/workspaces/${workspaceId}/members/${memberId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  removeWorkspaceMember: (workspaceId, memberId) =>
    request(`/workspaces/${workspaceId}/members/${memberId}`, { method: "DELETE" }),
  pinResearch: (id) => request(`/research/${id}/pin`, { method: "POST" }),
  unpinResearch: (id) => request(`/research/${id}/unpin`, { method: "POST" }),
  archiveResearch: (id) => request(`/research/${id}/archive`, { method: "POST" }),
  restoreResearch: (id) => request(`/research/${id}/restore`, { method: "POST" }),
  listShareLinks: (id) => request(`/research/${id}/share`),
  createShareLink: (id, payload) =>
    request(`/research/${id}/share`, { method: "POST", body: JSON.stringify(payload) }),
  revokeShareLink: (researchId, shareId) =>
    request(`/research/${researchId}/share/${shareId}`, { method: "DELETE" }),
  listVersions: (id) => request(`/research/${id}/versions`),
  getVersion: (researchId, versionId) =>
    request(`/research/${researchId}/versions/${versionId}`),
  compareVersions: (researchId, fromVersion, toVersion) =>
    request(
      `/research/${researchId}/versions/compare?from_version=${fromVersion}&to_version=${toVersion}`,
    ),
  restoreVersion: (researchId, versionId) =>
    request(`/research/${researchId}/versions/${versionId}/restore`, { method: "POST" }),
  listComments: (id) => request(`/research/${id}/comments`),
  createComment: (id, payload) =>
    request(`/research/${id}/comments`, { method: "POST", body: JSON.stringify(payload) }),
  updateComment: (researchId, commentId, payload) =>
    request(`/research/${researchId}/comments/${commentId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteComment: (researchId, commentId) =>
    request(`/research/${researchId}/comments/${commentId}`, { method: "DELETE" }),
  getPublicReport: (token) => request(`/public/reports/${token}`),
};

export function getPublicApiBase() {
  return API_BASE;
}

export async function uploadDocument(file) {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (response.status === 401) {
    clearAuth();
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!response.ok) {
    let detail = `Upload failed: ${response.status}`;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return response.json();
}

api.uploadDocument = uploadDocument;

export async function subscribeProgressStream(researchId, onEvent, signal) {
  const token = getToken();
  const headers = { Accept: "text/event-stream" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}/research/${researchId}/progress/stream`, {
    headers,
    signal,
  });

  if (response.status === 401) {
    clearAuth();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  if (!response.ok) {
    throw new Error(`SSE failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      const line = part.split("\n").find((l) => l.startsWith("data: "));
      if (!line) continue;
      try {
        const payload = JSON.parse(line.slice(6));
        onEvent(payload);
        if (payload.status === "completed" || payload.status === "failed") return;
      } catch {
        /* ignore malformed chunks */
      }
    }
  }
}

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
