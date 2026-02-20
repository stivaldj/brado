"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { CheckCircle2, ChevronRight, Loader2 } from "lucide-react";

import { apiClient } from "@/lib/api/client";
import { normalizeQuestion, normalizeResult } from "@/lib/format/interview";
import { useSessionStore } from "@/lib/state/session.store";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const TOTAL_QUESTIONS = 25;

const LIKERT_META: Record<number, { label: string; color: string }> = {
  1: { label: "Discordo totalmente", color: "var(--v2-danger)" },
  2: { label: "Discordo muito", color: "var(--v2-danger-soft)" },
  3: { label: "Discordo", color: "var(--v2-text-subtle)" },
  4: { label: "Neutro", color: "var(--v2-text-muted)" },
  5: { label: "Concordo", color: "var(--v2-text-subtle)" },
  6: { label: "Concordo muito", color: "var(--v2-accent-soft)" },
  7: { label: "Concordo totalmente", color: "var(--v2-accent)" },
};

export default function InterviewPage() {
  const router = useRouter();
  const [userId, setUserId] = React.useState("");
  const [hoveredValue, setHoveredValue] = React.useState<number | null>(null);

  const sessionId = useSessionStore((state) => state.sessionId);
  const currentQuestion = useSessionStore((state) => state.currentQuestion);
  const answeredCount = useSessionStore((state) => state.answeredCount);
  const setSession = useSessionStore((state) => state.setSession);
  const setAnsweredCount = useSessionStore((state) => state.setAnsweredCount);
  const setCurrentQuestion = useSessionStore((state) => state.setCurrentQuestion);
  const upsertAnswer = useSessionStore((state) => state.upsertAnswer);
  const setLastResult = useSessionStore((state) => state.setLastResult);

  const startMutation = useMutation({
    mutationFn: () => apiClient.interview.start({ user_id: userId || undefined }),
    onSuccess: (data) => {
      setSession(data.session_id);
      setAnsweredCount(typeof data.answered_count === "number" ? data.answered_count : 0);
      setCurrentQuestion(normalizeQuestion(data.question ?? data.next_question ?? null));
    },
  });

  const answerMutation = useMutation({
    mutationFn: async (answer: number) => {
      if (!sessionId || !currentQuestion) throw new Error("Não há sessão ativa");
      const qid = currentQuestion.question_id ?? currentQuestion.id ?? `q-${answeredCount + 1}`;
      return apiClient.interview.answer(sessionId, { answer, question_id: qid });
    },
    onSuccess: (data, answer) => {
      const questionId = currentQuestion?.question_id ?? currentQuestion?.id ?? `q-${answeredCount + 1}`;
      upsertAnswer(questionId, answer);
      setCurrentQuestion(normalizeQuestion(data.next_question ?? null));
      setAnsweredCount(typeof data.answered_count === "number" ? data.answered_count : answeredCount + 1);
    },
  });

  const finishMutation = useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error("Inicie uma sessão primeiro");
      return apiClient.interview.finish(sessionId);
    },
    onSuccess: (resultPayload) => {
      setLastResult(normalizeResult(resultPayload));
      router.push("/results");
    },
  });

  const progressPct = TOTAL_QUESTIONS > 0 ? Math.min(100, (answeredCount / TOTAL_QUESTIONS) * 100) : 0;
  const isComplete = answeredCount >= TOTAL_QUESTIONS || (!currentQuestion && answeredCount > 0);

  return (
    <div className="v2-content">
      {/* Page header */}
      <header className="v2-page-header">
        <div>
          <p className="v2-page-kicker">Coleta de opinião</p>
          <h1 className="text-[22px] font-bold leading-[1.2] text-[var(--v2-text-main)]">
            Entrevista política
          </h1>
          <p className="mt-1 text-[13px] text-[var(--v2-text-muted)]">
            Questionário Likert 1–7 · 25 questões · Análise de 8 dimensões políticas
          </p>
        </div>
        {sessionId ? (
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--v2-text-subtle)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--v2-ok)]" />
            Sessão ativa
          </div>
        ) : null}
      </header>

      <div className="grid gap-5 xl:grid-cols-[1fr_300px]">
        {/* Main area */}
        <div className="flex flex-col gap-5">

          {/* Progress bar */}
          {sessionId ? (
            <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
              <div className="flex items-center justify-between px-5 py-3">
                <span className="text-[11px] font-bold uppercase tracking-[0.1em] text-[var(--v2-text-subtle)]">
                  Progresso
                </span>
                <span className="font-mono text-sm font-bold text-[var(--v2-accent-soft)]">
                  {answeredCount} / {TOTAL_QUESTIONS}
                </span>
              </div>
              <div className="h-1.5 w-full bg-[var(--v2-bg-surface-muted)]">
                <div
                  className="h-full bg-[var(--v2-accent)] transition-all duration-500"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </div>
          ) : null}

          {/* Start card */}
          {!sessionId ? (
            <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
              <div className="border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-5 py-3">
                <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">
                  Iniciar entrevista
                </span>
              </div>
              <div className="p-6">
                <p className="text-sm leading-6 text-[var(--v2-text-muted)]">
                  Responda 25 perguntas sobre temas políticos e descubra seu posicionamento
                  em 8 dimensões. O resultado aponta os partidos com perfil mais próximo ao seu.
                </p>
                <div className="mt-5 flex flex-wrap items-center gap-3">
                  <Input
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    placeholder="Identificador (opcional)"
                    className="w-52"
                  />
                  <Button onClick={() => startMutation.mutate()} disabled={startMutation.isPending}>
                    {startMutation.isPending ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Iniciando...</>
                    ) : (
                      <>Iniciar agora <ChevronRight className="ml-1 h-4 w-4" /></>
                    )}
                  </Button>
                </div>
                {startMutation.isError ? (
                  <p className="mt-3 text-sm text-[var(--v2-danger-soft)]">
                    Erro ao iniciar. Verifique se o backend está rodando.
                  </p>
                ) : null}
              </div>
            </div>
          ) : null}

          {/* Question card */}
          {sessionId && !isComplete ? (
            <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
              <div className="flex items-center justify-between border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-5 py-3">
                <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">
                  Pergunta {answeredCount + 1} de {TOTAL_QUESTIONS}
                </span>
                {currentQuestion ? (
                  <span className="font-mono text-[10px] text-[var(--v2-text-subtle)]">
                    {currentQuestion.question_id ?? currentQuestion.id ?? "—"}
                  </span>
                ) : null}
              </div>

              <div className="p-6">
                {currentQuestion ? (
                  <>
                    <p className="text-base font-medium leading-[1.7] text-[var(--v2-text-main)]">
                      {currentQuestion.text}
                    </p>

                    {/* Likert buttons */}
                    <div className="mt-6">
                      <div className="flex gap-2">
                        {[1, 2, 3, 4, 5, 6, 7].map((value) => {
                          const meta = LIKERT_META[value];
                          const isHovered = hoveredValue === value;
                          return (
                            <button
                              key={value}
                              type="button"
                              disabled={answerMutation.isPending}
                              onClick={() => answerMutation.mutate(value)}
                              onMouseEnter={() => setHoveredValue(value)}
                              onMouseLeave={() => setHoveredValue(null)}
                              aria-label={meta.label}
                              className="relative flex flex-1 items-center justify-center rounded-[8px] border py-3 text-sm font-bold transition-all disabled:opacity-40"
                              style={{
                                borderColor: isHovered ? meta.color : "var(--v2-border)",
                                background: isHovered
                                  ? `color-mix(in srgb, ${meta.color} 18%, transparent)`
                                  : "var(--v2-bg-surface-muted)",
                                color: isHovered ? meta.color : "var(--v2-text-muted)",
                              }}
                            >
                              {answerMutation.isPending && value === 4 ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              ) : (
                                value
                              )}
                            </button>
                          );
                        })}
                      </div>

                      {/* Scale labels */}
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--v2-danger-soft)]">
                          Discordo
                        </span>
                        <span
                          className="text-[11px] font-semibold transition-all"
                          style={{
                            color: hoveredValue ? LIKERT_META[hoveredValue].color : "var(--v2-text-subtle)",
                          }}
                        >
                          {hoveredValue ? LIKERT_META[hoveredValue].label : "Neutro (4)"}
                        </span>
                        <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--v2-accent-soft)]">
                          Concordo
                        </span>
                      </div>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-[var(--v2-text-muted)]">Carregando próxima pergunta...</p>
                )}
              </div>
            </div>
          ) : null}

          {/* Complete state */}
          {sessionId && isComplete ? (
            <div className="flex flex-col items-center gap-4 rounded-[12px] border border-[var(--v2-ok)] bg-[color-mix(in_srgb,var(--v2-ok)_10%,transparent)] p-8 text-center">
              <CheckCircle2 className="h-10 w-10 text-[var(--v2-ok)]" />
              <div>
                <p className="text-lg font-bold text-[var(--v2-text-main)]">Todas as perguntas respondidas!</p>
                <p className="mt-1 text-sm text-[var(--v2-text-muted)]">
                  Clique em "Calcular resultado" para ver seu perfil político.
                </p>
              </div>
              <Button onClick={() => finishMutation.mutate()} disabled={finishMutation.isPending} className="mt-2">
                {finishMutation.isPending ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Calculando...</>
                ) : (
                  "Calcular resultado"
                )}
              </Button>
            </div>
          ) : null}

          {/* Finish early */}
          {sessionId && !isComplete && answeredCount >= 5 ? (
            <div className="flex justify-end">
              <Button
                variant="secondary"
                onClick={() => finishMutation.mutate()}
                disabled={finishMutation.isPending}
              >
                {finishMutation.isPending ? "Calculando..." : `Finalizar com ${answeredCount} respostas`}
              </Button>
            </div>
          ) : null}
        </div>

        {/* Right sidebar */}
        <div className="flex flex-col gap-4">
          {/* Session info */}
          <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
            <div className="border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-4 py-2.5">
              <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">Sessão</span>
            </div>
            <div className="space-y-3 p-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--v2-text-subtle)]">ID</p>
                <p className="mt-0.5 break-all font-mono text-xs text-[var(--v2-text-muted)]">{sessionId ?? "—"}</p>
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--v2-text-subtle)]">Respondidas</p>
                <p className="mt-0.5 text-2xl font-bold text-[var(--v2-accent)]">{answeredCount}</p>
              </div>
            </div>
          </div>

          {/* Dimensions */}
          <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
            <div className="border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-4 py-2.5">
              <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">
                8 dimensões
              </span>
            </div>
            <div className="p-4">
              {["Econômico", "Social", "Ambiental", "Segurança", "Federalismo", "Anticorrupção", "Ext. exterior", "Laicidade"].map(
                (dim, i) => (
                  <div key={dim} className="flex items-center gap-2 border-b border-[var(--v2-border)] py-1.5 last:border-b-0">
                    <span
                      className="h-1.5 w-1.5 shrink-0 rounded-full"
                      style={{
                        background:
                          i < (answeredCount / TOTAL_QUESTIONS) * 8
                            ? "var(--v2-accent)"
                            : "var(--v2-border-strong)",
                      }}
                    />
                    <span className="text-xs text-[var(--v2-text-muted)]">{dim}</span>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Scale legend */}
          <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
            <div className="border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-4 py-2.5">
              <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">
                Escala
              </span>
            </div>
            <div className="space-y-2 p-4">
              {[1, 2, 3, 4, 5, 6, 7].map((v) => (
                <div key={v} className="flex items-center gap-2">
                  <span
                    className="flex h-5 w-5 shrink-0 items-center justify-center rounded-[4px] text-[10px] font-bold"
                    style={{
                      background: `color-mix(in srgb, ${LIKERT_META[v].color} 20%, transparent)`,
                      color: LIKERT_META[v].color,
                      border: `1px solid color-mix(in srgb, ${LIKERT_META[v].color} 40%, transparent)`,
                    }}
                  >
                    {v}
                  </span>
                  <span className="text-[11px] text-[var(--v2-text-muted)]">{LIKERT_META[v].label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
