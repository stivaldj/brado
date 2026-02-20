import {
  ApiError,
  type ApiErrorBody,
  type AuthMeResponse,
  type BudgetSimulationRequest,
  type BudgetSimulationResponse,
  type DeputadoDespesaItem,
  type DeputadoDespesaResumo,
  type DeputadoNormalizado,
  type InterviewAnswerRequest,
  type InterviewAnswerResponse,
  type InterviewResult,
  type InterviewStartRequest,
  type InterviewStartResponse,
  type PropositionsResponse,
  type TokenResponse,
} from "@/lib/api/types";
import { useSessionStore } from "@/lib/state/session.store";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:18000";
const CIVIC_API_BASE_URL = process.env.NEXT_PUBLIC_CIVIC_API_BASE_URL ?? API_BASE_URL;
const API_PREFIX = "/api/v1";

function resolveExpiresAt(tokenPayload: TokenResponse): number {
  if (tokenPayload.expires_at) {
    return tokenPayload.expires_at > 1_000_000_000_000
      ? tokenPayload.expires_at
      : tokenPayload.expires_at * 1000;
  }

  if (tokenPayload.expires_in) {
    return Date.now() + tokenPayload.expires_in * 1000;
  }

  return Date.now() + 30 * 60 * 1000;
}

function ensureClientId(): string {
  const state = useSessionStore.getState();
  if (state.clientId) {
    return state.clientId;
  }

  const nextClientId =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? `brado-web-${crypto.randomUUID()}`
      : `brado-web-${Date.now()}`;

  state.setAuth({
    token: state.token,
    expiresAt: state.expiresAt,
    clientId: nextClientId,
  });

  return nextClientId;
}

async function safeJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    const text = await response.text();
    return text || null;
  }
  return response.json();
}

async function fetchWithTimeout(url: string, init?: RequestInit, timeoutMs = 10_000): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), Math.max(3000, timeoutMs));
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

async function request<T>(path: string, init?: RequestInit, retry = true): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, init);

  if (response.status === 401 && retry && path !== `${API_PREFIX}/auth/token`) {
    await ensureToken();

    const token = useSessionStore.getState().token;
    const retryHeaders = {
      ...(init?.headers ?? {}),
      Authorization: token ? `Bearer ${token}` : "",
    } as HeadersInit;

    return request<T>(path, { ...init, headers: retryHeaders }, false);
  }

  if (!response.ok) {
    const body = (await safeJson(response)) as ApiErrorBody;
    const message =
      typeof body?.message === "string"
        ? body.message
        : typeof body?.detail === "string"
          ? body.detail
          : "Falha ao processar requisição.";
    throw new ApiError(message, response.status, body);
  }

  return (await safeJson(response)) as T;
}

export async function ensureToken(): Promise<{ accessToken: string; expiresAt: number }> {
  const state = useSessionStore.getState();
  const now = Date.now();

  if (state.token && state.expiresAt && now < state.expiresAt - 15_000) {
    return { accessToken: state.token, expiresAt: state.expiresAt };
  }

  const clientId = ensureClientId();
  const payload = await request<TokenResponse>(`${API_PREFIX}/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ client_id: clientId }),
  });

  const expiresAt = resolveExpiresAt(payload);
  useSessionStore.getState().setAuth({
    token: payload.access_token,
    expiresAt,
    clientId,
  });

  return { accessToken: payload.access_token, expiresAt };
}

export async function authMe(): Promise<AuthMeResponse> {
  const token = (await ensureToken()).accessToken;

  const me = await request<AuthMeResponse>(`${API_PREFIX}/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  useSessionStore.getState().setAuthMe(me);
  return me;
}

export async function apiFetch<T>(path: string, init?: RequestInit, requireAuth = true): Promise<T> {
  const headers = new Headers(init?.headers);

  if (requireAuth && path.startsWith(API_PREFIX)) {
    const token = (await ensureToken()).accessToken;
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }

  return request<T>(path, {
    ...init,
    headers,
  });
}

export const apiClient = {
  ensureToken,
  authMe,
  apiFetch,
  interview: {
    start: (payload: InterviewStartRequest) =>
      apiFetch<InterviewStartResponse>(`${API_PREFIX}/interview/start`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    answer: (sessionId: string, payload: InterviewAnswerRequest) =>
      apiFetch<InterviewAnswerResponse>(`${API_PREFIX}/interview/${sessionId}/answer`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    finish: (sessionId: string) =>
      apiFetch<InterviewResult>(`${API_PREFIX}/interview/${sessionId}/finish`, {
        method: "POST",
      }),
    result: (sessionId: string) =>
      apiFetch<InterviewResult>(`${API_PREFIX}/interview/${sessionId}/result`, {
        method: "GET",
      }),
    exportFile: async (sessionId: string, format: "json" | "pdf") => {
      const token = (await ensureToken()).accessToken;
      const response = await fetch(
        `${API_BASE_URL}${API_PREFIX}/interview/${sessionId}/export?format=${format}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new ApiError("Falha no export", response.status, await safeJson(response));
      }

      return response.blob();
    },
  },
  budget: {
    simulate: (payload: BudgetSimulationRequest) =>
      apiFetch<BudgetSimulationResponse>(`${API_PREFIX}/budget/simulate`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
  legislative: {
    propositions: (limit = 20) =>
      apiFetch<PropositionsResponse>(`${API_PREFIX}/legislative/propositions?limit=${limit}`, {
        method: "GET",
      }),
  },
  deputados: {
    listNormalized: async (params?: Record<string, string | number>, timeoutMs = 10_000) => {
      const query = new URLSearchParams();
      Object.entries(params ?? {}).forEach(([key, value]) => query.set(key, String(value)));
      if (!query.has("limit")) {
        query.set("limit", "513");
      }
      const url = `${CIVIC_API_BASE_URL}/deputados/normalizados?${query.toString()}`;
      const response = await fetchWithTimeout(url, { method: "GET" }, timeoutMs);

      if (!response.ok) {
        throw new ApiError("Falha ao carregar deputados normalizados.", response.status, await safeJson(response));
      }
      return (await safeJson(response)) as DeputadoNormalizado[];
    },
    getNormalizedById: async (id: number, timeoutMs = 10_000) => {
      const url = `${CIVIC_API_BASE_URL}/deputados/normalizados/${id}`;
      const response = await fetchWithTimeout(url, { method: "GET" }, timeoutMs);

      if (response.status === 404) {
        return null;
      }
      if (!response.ok) {
        throw new ApiError(`Falha ao carregar perfil do deputado ${id}.`, response.status, await safeJson(response));
      }
      return (await safeJson(response)) as DeputadoNormalizado;
    },
    expenseSummary: async (limit = 600, timeoutMs = 10_000) => {
      const url = `${CIVIC_API_BASE_URL}/deputados/despesas/resumo?limit=${Math.max(1, limit)}`;
      const response = await fetchWithTimeout(url, { method: "GET" }, timeoutMs);
      if (!response.ok) {
        throw new ApiError("Falha ao carregar resumo de despesas.", response.status, await safeJson(response));
      }
      return (await safeJson(response)) as DeputadoDespesaResumo[];
    },
    expensesById: async (
      deputadoId: number,
      params?: { ano?: number; mes?: number; limit?: number; page?: number },
      timeoutMs = 10_000
    ) => {
      const query = new URLSearchParams();
      if (params?.ano) query.set("ano", String(params.ano));
      if (params?.mes) query.set("mes", String(params.mes));
      if (params?.limit) query.set("limit", String(params.limit));
      if (params?.page) query.set("page", String(params.page));
      const url = `${CIVIC_API_BASE_URL}/deputados/${deputadoId}/despesas${query.toString() ? `?${query.toString()}` : ""}`;
      const response = await fetchWithTimeout(url, { method: "GET" }, timeoutMs);
      if (!response.ok) {
        throw new ApiError(`Falha ao carregar despesas do deputado ${deputadoId}.`, response.status, await safeJson(response));
      }
      return (await safeJson(response)) as DeputadoDespesaItem[];
    },
  },
};
