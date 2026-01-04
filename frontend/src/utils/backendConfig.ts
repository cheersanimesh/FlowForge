// Backend URL configuration management

const BACKEND_URL_KEY = 'workflow_backend_url';
const DEFAULT_BACKEND_URL = 'https://backend-app-production-b88e.up.railway.app';

export function getBackendUrl(): string {
  const stored = localStorage.getItem(BACKEND_URL_KEY);
  return stored || DEFAULT_BACKEND_URL;
}

export function setBackendUrl(url: string): void {
  // Normalize the URL - remove trailing slashes
  const normalizedUrl = url.trim().replace(/\/+$/, '');
  localStorage.setItem(BACKEND_URL_KEY, normalizedUrl);
}

export function getApiBaseUrl(): string {
  const backendUrl = getBackendUrl();
  // If the URL already contains /api, use it as is, otherwise append /api
  if (backendUrl.endsWith('/api')) {
    return backendUrl;
  }
  return `${backendUrl}`;
}

