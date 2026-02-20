import type { InterviewQuestion, InterviewResult, RankingItem } from "@/lib/api/types";

export function normalizeQuestion(payload: unknown): InterviewQuestion | null {
  if (!payload || typeof payload !== "object") return null;
  const source = payload as Record<string, unknown>;
  const text =
    (typeof source.text === "string" && source.text) ||
    (typeof source.question === "string" && source.question) ||
    (typeof source.statement === "string" && source.statement) ||
    "";

  if (!text) return null;

  const tags = Array.isArray(source.tags) ? source.tags.filter((value): value is string => typeof value === "string") : [];
  const dimensions = Array.isArray(source.dimensions)
    ? source.dimensions.filter((value): value is string => typeof value === "string")
    : [];

  return {
    ...source,
    id: typeof source.id === "string" ? source.id : undefined,
    question_id: typeof source.question_id === "string" ? source.question_id : undefined,
    text,
    tags,
    dimensions,
  };
}

export function normalizeResult(payload: unknown): InterviewResult {
  if (!payload || typeof payload !== "object") {
    return {};
  }

  const source = payload as Record<string, unknown>;
  const rankingSource =
    (Array.isArray(source.ranking) && source.ranking) ||
    (Array.isArray(source.similaridade) && source.similaridade) ||
    [];

  const ranking = rankingSource
    .filter((item): item is Record<string, unknown> => !!item && typeof item === "object")
    .map<RankingItem>((item) => ({
      ...item,
      tipo: typeof item.tipo === "string" ? item.tipo : typeof item.type === "string" ? item.type : undefined,
      nome: typeof item.nome === "string" ? item.nome : typeof item.name === "string" ? item.name : "Sem nome",
      sigla: typeof item.sigla === "string" ? item.sigla : undefined,
      similaridade:
        typeof item.similaridade === "number"
          ? item.similaridade
          : typeof item.score === "number"
            ? item.score
            : 0,
      explicacao:
        typeof item.explicacao === "string"
          ? item.explicacao
          : typeof item.explanation === "string"
            ? item.explanation
            : undefined,
    }));

  let metricasSource: Record<string, unknown> = source;
  if (source.metricas && typeof source.metricas === "object") {
    metricasSource = source.metricas as Record<string, unknown>;
  }

  const vetor =
    source.vetor && typeof source.vetor === "object" ? (source.vetor as Record<string, number>) : undefined;

  return {
    ...source,
    session_id: typeof source.session_id === "string" ? source.session_id : undefined,
    metricas: {
      esquerda_direita:
        typeof metricasSource.esquerda_direita === "number"
          ? metricasSource.esquerda_direita
          : typeof metricasSource.left_right === "number"
            ? metricasSource.left_right
            : undefined,
      confianca: typeof metricasSource.confianca === "number" ? metricasSource.confianca : undefined,
      consistencia: typeof metricasSource.consistencia === "number" ? metricasSource.consistencia : undefined,
    },
    vetor,
    ranking,
  };
}
