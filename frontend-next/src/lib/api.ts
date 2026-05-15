/**
 * Client HTTP vers le backend FastAPI (Railway).
 * Utiliser cote serveur (Server Components / API Routes).
 * Pour le client-side, utiliser fetch() directement avec le token Clerk.
 */

/** URL de base du backend FastAPI, sans slash final (l'env peut en contenir un). */
export const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

type ApiResponse<T = unknown> = T;

function buildClient(token: string) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? `Erreur ${res.status}`);
    }

    return res.json() as Promise<T>;
  }

  return {
    get: <T = ApiResponse>(path: string) => request<T>("GET", path),
    post: <T = ApiResponse>(path: string, body?: unknown) => request<T>("POST", path, body),
    put: <T = ApiResponse>(path: string, body?: unknown) => request<T>("PUT", path, body),
    delete: <T = ApiResponse>(path: string) => request<T>("DELETE", path),
  };
}

export { buildClient as apiClient };
