import { getApiBaseUrl, getBackendUrl } from '../utils/backendConfig';
import type { WorkflowSpec, RunStartResponse, RunResponse } from '../types';

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const apiBase = getApiBaseUrl();
  const url = `${apiBase}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function startWorkflowRun(spec: WorkflowSpec): Promise<RunStartResponse> {
  return apiRequest<RunStartResponse>('/run', {
    method: 'POST',
    body: JSON.stringify(spec),
  });
}

export async function getWorkflowRunStatus(runId: string): Promise<RunResponse> {
  return apiRequest<RunResponse>(`/run/${runId}`, {
    method: 'GET',
  });
}

export async function runWorkflow(spec: { nodes: any[]; edges: any[] }) {
  return apiRequest<any>('/run', {
    method: 'POST',
    body: JSON.stringify(spec),
  });
}

export async function fetchPreview(previewPath: string) {
  // Preview path is relative to backend root (e.g., runs/{run_id}/preview_0_b1.json)
  // We need to fetch it directly from the backend
  const backendUrl = getBackendUrl();
  const response = await fetch(`${backendUrl}/${previewPath}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch preview: ${response.statusText}`);
  }
  return response.json();
}

export async function healthCheck() {
  return apiRequest<{ status: string }>('/health');
}

export async function uploadCsvFile(file: File): Promise<{ path: string; filename: string }> {
  const backendUrl = getBackendUrl();
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${backendUrl}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function downloadFile(filePath: string, _filename?: string): Promise<Blob> {
  const backendUrl = getBackendUrl();
  // Encode each path segment (preserving slashes)
  // This ensures paths like "runs/123/output.csv" work correctly
  const encodedPath = filePath.split('/').map(segment => encodeURIComponent(segment)).join('/');
  const url = new URL(`/download/${encodedPath}`, backendUrl).toString();
  
  const response = await fetch(url, {
    method: 'GET',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.blob();
}

export async function downloadNodeResult(runId: string, nodeId: string, _filename?: string): Promise<Blob> {
  const apiBase = getApiBaseUrl();
  const url = new URL(`/get_result`, apiBase);
  url.searchParams.append('run_id', runId);
  url.searchParams.append('node_id', nodeId);
  
  const response = await fetch(url.toString(), {
    method: 'GET',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  // Handle streaming response
  return response.blob();
}

