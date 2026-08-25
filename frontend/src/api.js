const API_BASE_URL = "https://id-tool-extract-1.onrender.com";
export async function startGroup() {
  const response = await fetch(`${API_BASE_URL}/group/start`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to start group");
  return response.json();
}

export async function finishGroup(tripId) {
  const response = await fetch(`${API_BASE_URL}/group/finish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trip_id: tripId }),
  });
  if (!response.ok) throw new Error("Failed to finish group");
  return response.json();
}

export async function extractIdDetails(file, tripId) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("trip_id", tripId);

  const response = await fetch(`${API_BASE_URL}/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const message = errorBody?.detail || `Extraction failed: ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}

export function getDownloadUrl(tripId) {
  return `${API_BASE_URL}/download-csv/${tripId}`;
}