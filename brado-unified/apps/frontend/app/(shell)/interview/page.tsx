"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { apiClient } from "@/lib/api/client";
import { normalizeQuestion, normalizeResult } from "@/lib/format/interview";
import { useSessionStore } from "@/lib/state/session.store";

import { ApiErrorNotice } from "@/components/api-error-notice";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useToast } from "@/components/ui/use-toast";

const likertValues = [1, 2, 3, 4, 5, 6, 7];

export default function InterviewPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [userId, setUserId] = React.useState("");

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
      const nextQuestion = normalizeQuestion(data.question ?? data.next_question ?? null);
      setSession(data.session_id);
      setAnsweredCount(typeof data.answered_count === "number" ? data.answered_count : 0);
      setCurrentQuestion(nextQuestion);
      toast({ title: "Sessão iniciada" });
    },
    onError: (error: Error) => {
      toast({
        title: "Falha ao iniciar sessão",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const answerMutation = useMutation({
    mutationFn: async (answer: number) => {
      if (!sessionId || !currentQuestion) {
        throw new Error("Não há sessão ou pergunta ativa.");
      }

      const qid = currentQuestion.question_id ?? currentQuestion.id ?? `q-${answeredCount + 1}`;
      return apiClient.interview.answer(sessionId, { answer, question_id: qid });
    },
    onSuccess: (data, answer) => {
      const questionId = currentQuestion?.question_id ?? currentQuestion?.id ?? `q-${answeredCount + 1}`;
      upsertAnswer(questionId, answer);

      const nextQuestion = normalizeQuestion(data.next_question ?? null);
      setCurrentQuestion(nextQuestion);
      setAnsweredCount(typeof data.answered_count === "number" ? data.answered_count : answeredCount + 1);

      if (!nextQuestion) {
        toast({ title: "Sem próxima pergunta", description: "Você já pode finalizar para calcular o resultado." });
      }
    },
    onError: (error: Error) => {
      toast({
        title: "Falha ao enviar resposta",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const finishMutation = useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error("Inicie uma sessão primeiro.");
      return apiClient.interview.finish(sessionId);
    },
    onSuccess: (resultPayload) => {
      const result = normalizeResult(resultPayload);
      setLastResult(result);
      toast({ title: "Resultado calculado" });
      router.push("/results");
    },
    onError: (error: Error) => {
      toast({ title: "Falha ao finalizar", description: error.message, variant: "destructive" });
    },
  });

  const reloadResultMutation = useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error("Inicie uma sessão primeiro.");
      return apiClient.interview.result(sessionId);
    },
    onSuccess: (resultPayload) => {
      const result = normalizeResult(resultPayload);
      setLastResult(result);
      toast({ title: "Resultado recarregado" });
      router.push("/results");
    },
    onError: (error: Error) => {
      toast({ title: "Falha ao recarregar", description: error.message, variant: "destructive" });
    },
  });

  React.useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (answerMutation.isPending || !currentQuestion) return;
      if (!/^[1-7]$/.test(event.key)) return;
      answerMutation.mutate(Number(event.key));
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [answerMutation, currentQuestion]);

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Entrevista</h1>
        <p className="text-sm text-muted-foreground">Fluxo de perguntas Likert 1-7 com recuperação de falhas.</p>
      </div>

      {!sessionId ? (
        <Card>
          <CardHeader>
            <CardTitle>Iniciar sessão</CardTitle>
            <CardDescription>Você pode informar `user_id` opcional para rastreio.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="user_id">User ID (opcional)</Label>
              <Input id="user_id" placeholder="ex: eleitor-123" value={userId} onChange={(e) => setUserId(e.target.value)} />
            </div>
            <Button onClick={() => startMutation.mutate()} disabled={startMutation.isPending}>
              {startMutation.isPending ? "Iniciando..." : "Iniciar entrevista"}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Pergunta atual</CardTitle>
          <CardDescription>
            {sessionId ? `Sessão ${sessionId} · ${answeredCount} respondidas` : "Inicie uma sessão para receber perguntas."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {answerMutation.isPending ? <Skeleton className="h-16" /> : null}

          {currentQuestion ? (
            <>
              <p className="text-base leading-7">{currentQuestion.text}</p>

              {currentQuestion.tags?.length ? (
                <div className="flex flex-wrap gap-1">
                  {currentQuestion.tags.map((tag) => (
                    <Badge key={tag} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
              ) : null}

              {currentQuestion.dimensions?.length ? (
                <div className="flex flex-wrap gap-2">
                  {currentQuestion.dimensions.map((dimension) => (
                    <Tooltip key={dimension}>
                      <TooltipTrigger asChild>
                        <Badge variant="secondary" className="cursor-help">
                          {dimension}
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <span>Dimensão potencialmente impactada</span>
                      </TooltipContent>
                    </Tooltip>
                  ))}
                </div>
              ) : null}

              <div className="grid grid-cols-7 gap-2">
                {likertValues.map((value) => (
                  <Button
                    key={value}
                    type="button"
                    variant="outline"
                    aria-label={`Responder ${value}`}
                    onClick={() => answerMutation.mutate(value)}
                    disabled={answerMutation.isPending}
                  >
                    {value}
                  </Button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">Atalho de teclado: use as teclas 1..7.</p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Sem pergunta ativa. Inicie sessão ou finalize para calcular.</p>
          )}

          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => finishMutation.mutate()} disabled={!sessionId || finishMutation.isPending}>
              {finishMutation.isPending ? "Calculando..." : "Finalizar e calcular"}
            </Button>
            <Button
              variant="outline"
              onClick={() => reloadResultMutation.mutate()}
              disabled={!sessionId || reloadResultMutation.isPending}
            >
              {reloadResultMutation.isPending ? "Carregando..." : "Recarregar resultado"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <ApiErrorNotice
        error={
          (startMutation.error as Error | null) ??
          (answerMutation.error as Error | null) ??
          (finishMutation.error as Error | null) ??
          (reloadResultMutation.error as Error | null)
        }
      />
    </section>
  );
}
