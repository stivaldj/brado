import { apiClient } from "@/lib/api/client";
import type { DeputadoDespesaResumo } from "@/lib/api/types";
import type { Expense, Parlamentar, ParlamentarFilters, Project, Vote, VoteFilters } from "@/lib/data/types";
import type { DeputadoNormalizado } from "@/lib/api/types";
import { buildExpensesForParlamentar } from "@/lib/mocks/expenses";
import { parlamentaresMock } from "@/lib/mocks/parlamentares";
import { buildProjectsForParlamentar } from "@/lib/mocks/projects";
import { buildVotesForParlamentar } from "@/lib/mocks/votes";

const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS === "true";
const FETCH_TIMEOUT_MS = Math.max(3000, Number(process.env.NEXT_PUBLIC_CIVIC_FETCH_TIMEOUT_MS ?? "10000"));

const voteCache = new Map<string, Vote[]>();
const projectsCache = new Map<string, Project[]>();
const expensesCache = new Map<string, Expense[]>();

function ensureVotes(id: string) {
  if (!voteCache.has(id)) {
    voteCache.set(id, buildVotesForParlamentar(id, 60));
  }
  return voteCache.get(id) ?? [];
}

function ensureProjects(id: string) {
  if (!projectsCache.has(id)) {
    projectsCache.set(id, buildProjectsForParlamentar(id, 16));
  }
  return projectsCache.get(id) ?? [];
}

function ensureExpenses(id: string) {
  if (!expensesCache.has(id)) {
    expensesCache.set(id, buildExpensesForParlamentar(id, 44));
  }
  return expensesCache.get(id) ?? [];
}

function scoreFromId(id: number, offset: number) {
  return 45 + ((id + offset) % 46);
}

function buildFallbackPhotoUrl(id: string, name: string) {
  if (/^\d+$/.test(id)) {
    return `https://www.camara.leg.br/internet/deputado/bandep/${id}.jpg`;
  }
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=453930&color=FFF8F0&size=128&bold=true`;
}

function mapDeputadoToParlamentar(item: DeputadoNormalizado): Parlamentar {
  const id = String(item.id);
  const name = item.status_nome || item.nome_civil || `Deputado ${id}`;
  const party = item.status_sigla_partido || "-";
  const uf = item.status_sigla_uf || "-";
  return {
    id,
    name,
    party,
    uf,
    monthlyExpense: undefined,
    photoUrl: item.foto_url || buildFallbackPhotoUrl(id, name),
    role: "Deputado Federal",
    bio: `Perfil normalizado (${party}/${uf}).`,
    alignment: scoreFromId(item.id, 7),
    controversy: scoreFromId(item.id, 19),
  };
}

async function fetchDeputadosNormalizados(params?: Record<string, string | number>): Promise<DeputadoNormalizado[]> {
  return apiClient.deputados.listNormalized(params, FETCH_TIMEOUT_MS);
}

export async function getParlamentares(filters?: ParlamentarFilters): Promise<Parlamentar[]> {
  const q = filters?.q?.trim().toLowerCase() ?? "";

  let items: Parlamentar[];
  if (useMocks) {
    items = parlamentaresMock.map((item) => ({
      ...item,
      photoUrl: item.photoUrl ?? buildFallbackPhotoUrl(item.id, item.name),
    }));
  } else {
    const [apiRows, expenseSummary] = await Promise.all([
      fetchDeputadosNormalizados({ limit: 513 }),
      apiClient.deputados.expenseSummary(600, FETCH_TIMEOUT_MS).catch(() => [] as DeputadoDespesaResumo[]),
    ]);
    const expenseById = new Map<number, number>(
      expenseSummary.map((row) => [row.id, Number(row.avg_last_3_months_liquido || row.latest_total_liquido || 0)])
    );
    items = apiRows.map((row) => {
      const parlamentar = mapDeputadoToParlamentar(row);
      parlamentar.monthlyExpense = expenseById.get(row.id);
      return parlamentar;
    });
  }

  if (q) {
    items = items.filter((item) => [item.name, item.party, item.uf].join(" ").toLowerCase().includes(q));
  }
  if (filters?.uf) {
    items = items.filter((item) => item.uf === filters.uf);
  }
  if (filters?.party) {
    items = items.filter((item) => item.party === filters.party);
  }

  if (filters?.sort === "alignment") {
    items.sort((a, b) => b.alignment - a.alignment);
  }
  if (filters?.sort === "controversy") {
    items.sort((a, b) => b.controversy - a.controversy);
  }

  return items;
}

export async function getParlamentarById(id: string): Promise<Parlamentar | null> {
  if (!useMocks && /^\d+$/.test(id)) {
    const row = await apiClient.deputados.getNormalizedById(Number(id), FETCH_TIMEOUT_MS);
    if (row) {
      return mapDeputadoToParlamentar(row);
    }
    return null;
  }

  if (!useMocks) {
    return null;
  }

  const mock = parlamentaresMock.find((item) => item.id === id);
  if (!mock) return null;
  return {
    ...mock,
    photoUrl: mock.photoUrl ?? buildFallbackPhotoUrl(mock.id, mock.name),
  };
}

export async function getDeputadoNormalizadoById(id: number): Promise<DeputadoNormalizado | null> {
  if (!Number.isFinite(id) || id <= 0) return null;
  if (useMocks) return null;
  return apiClient.deputados.getNormalizedById(id, FETCH_TIMEOUT_MS);
}

export async function getVotesByParlamentar(id: string, filters?: VoteFilters): Promise<Vote[]> {
  if (!useMocks) {
    return [];
  }

  const q = filters?.q?.trim().toLowerCase() ?? "";
  const base = ensureVotes(id);

  if (!q) return base;

  return base.filter((item) => `${item.title} ${item.description} ${item.topic} ${item.code}`.toLowerCase().includes(q));
}

export async function getProjectsByParlamentar(id: string): Promise<Project[]> {
  if (!useMocks) {
    return [];
  }
  return ensureProjects(id);
}

export async function getExpensesByParlamentar(id: string): Promise<Expense[]> {
  if (!useMocks && /^\d+$/.test(id)) {
    const rows = await apiClient.deputados.expensesById(Number(id), { limit: 300, page: 1 }, FETCH_TIMEOUT_MS);
    return rows.map((item) => {
      const isoDate = item.data_documento
        ? item.data_documento
        : `${String(item.ano).padStart(4, "0")}-${String(item.mes).padStart(2, "0")}-01`;
      const value = Number(item.valor_liquido ?? item.valor_documento ?? 0);
      const outlier = value > 15000;
      return {
        id: String(item.id),
        parlamentarId: id,
        date: isoDate,
        category: item.tipo_despesa || "Despesa parlamentar",
        vendor: item.nome_fornecedor || "Fornecedor não informado",
        value,
        outlier,
      };
    });
  }

  if (!useMocks) {
    return [];
  }
  return ensureExpenses(id);
}

export async function getPropositions(limit = 20) {
  if (useMocks) {
    const items = ensureProjects("mendes").slice(0, limit).map((project, index) => ({
      id: project.id,
      title: project.title,
      sigla: project.code,
      kind: "PROPOSIÇÃO",
      summary: `Prioridade ${project.priority} · ${project.status}`,
      sequence: index + 1,
    }));

    return { items };
  }

  return apiClient.legislative.propositions(limit);
}
