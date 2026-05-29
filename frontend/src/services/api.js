const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

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
  createResearch: (payload) =>
    request("/research", { method: "POST", body: JSON.stringify(payload) }),
  listResearch: () => request("/research"),
  getResearch: (id) => request(`/research/${id}`),
  runResearch: (id) => request(`/research/${id}/run`, { method: "POST" }),
  getProgress: (id) => request(`/research/${id}/progress`),
  getJob: (jobId) => request(`/jobs/${jobId}`),
  getReport: (id) => request(`/research/${id}/report`),
  exportMarkdown: (id) => request(`/research/${id}/export/markdown`),
  exportPdf: (id) => request(`/research/${id}/export/pdf`),
};

export function getExportUrl(id, format) {
  return `${API_BASE}/research/${id}/export/${format}`;
}
