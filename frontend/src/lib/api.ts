// Thin API client for the CRUX FastAPI backend.
// Tokens are stored in localStorage; requests attach the access token and
// transparently refresh on 401.

const TOKEN_KEY = "crux_access_token";
const REFRESH_KEY = "crux_refresh_token";

export const tokenStore = {
  get access() {
    return typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
  },
  get refresh() {
    return typeof window !== "undefined" ? localStorage.getItem(REFRESH_KEY) : null;
  },
  set(access: string, refresh?: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    if (typeof window === "undefined") return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function refreshAccess(): Promise<boolean> {
  const refresh = tokenStore.refresh;
  if (!refresh) return false;
  const res = await fetch("/api/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  tokenStore.set(data.access_token, data.refresh_token);
  return true;
}

export async function api<T = any>(
  path: string,
  options: RequestInit & { auth?: boolean; retry?: boolean } = {},
): Promise<T> {
  const { auth = true, retry = true, headers, ...rest } = options;
  const h = new Headers(headers);
  if (!(rest.body instanceof FormData)) h.set("Content-Type", "application/json");
  if (auth && tokenStore.access) h.set("Authorization", `Bearer ${tokenStore.access}`);

  const res = await fetch(path.startsWith("/api") ? path : `/api${path}`, { ...rest, headers: h });

  if (res.status === 401 && auth && retry) {
    if (await refreshAccess()) return api<T>(path, { ...options, retry: false });
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {}
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Convenience helpers
export const apiGet = <T = any>(p: string) => api<T>(p, { method: "GET" });
export const apiPost = <T = any>(p: string, body?: any) =>
  api<T>(p, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body ?? {}) });
export const apiPatch = <T = any>(p: string, body?: any) =>
  api<T>(p, { method: "PATCH", body: JSON.stringify(body ?? {}) });
export const apiDelete = <T = any>(p: string) => api<T>(p, { method: "DELETE" });
