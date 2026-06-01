import type { ApiError } from "@/types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

class HttpClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries = MAX_RETRIES,
  ): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    const token = localStorage.getItem("auth_token");
    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        const error: ApiError = {
          message: (errorBody as Record<string, string>).message ?? response.statusText,
          code: (errorBody as Record<string, string>).code ?? "UNKNOWN_ERROR",
          status: response.status,
        };
        throw error;
      }

      if (response.status === 204) {
        return undefined as T;
      }

      return response.json() as Promise<T>;
    } catch (error) {
      // Only retry on network errors, not on API errors (which have a status)
      const isNetworkError = error instanceof TypeError && !("status" in error);
      if (isNetworkError && retries > 0) {
        await sleep(RETRY_DELAY_MS * (MAX_RETRIES - retries + 1));
        return this.request<T>(endpoint, options, retries - 1);
      }
      throw error;
    }
  }

  get<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.set(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return this.request<T>(`${endpoint}${query ? `?${query}` : ""}`);
  }

  post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  patch<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }
}

export const httpClient = new HttpClient();
