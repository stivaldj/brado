"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { useSessionStore } from "@/lib/state/session.store";

import { ApiErrorNotice } from "@/components/api-error-notice";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const sessionId = useSessionStore((state) => state.sessionId);
  const answeredCount = useSessionStore((state) => state.answeredCount);
  const lastResult = useSessionStore((state) => state.lastResult);
  const authMe = useSessionStore((state) => state.authMe);

  const propositionsQuery = useQuery({
    queryKey: ["propositions", "preview"],
    queryFn: () => apiClient.legislative.propositions(5),
  });

  const meQuery = useQuery({
    queryKey: ["auth", "dashboard"],
    queryFn: apiClient.authMe,
  });

  const me = meQuery.data ?? authMe;

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Visão rápida da sessão, API e últimas proposições.</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Sessão atual</CardTitle>
            <CardDescription>Status da entrevista política.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {sessionId ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">session_id</span>
                  <Badge variant="outline">{sessionId}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Respondidas</span>
                  <Badge>{answeredCount}</Badge>
                </div>
                <Separator />
                <div className="flex flex-wrap gap-2">
                  <Button asChild size="sm">
                    <Link href="/interview">Continuar</Link>
                  </Button>
                  <Button asChild size="sm" variant="outline">
                    <Link href="/results">Ver resultado</Link>
                  </Button>
                </div>
              </>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">Nenhuma sessão ativa.</p>
                <Button asChild>
                  <Link href="/interview">Iniciar entrevista</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Status API</CardTitle>
            <CardDescription>Autenticação e disponibilidade.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {meQuery.isLoading ? (
              <Skeleton className="h-16" />
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Subject</span>
                  <Badge variant="secondary">{me?.subject ?? "indisponível"}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">TTL</span>
                  <Badge variant="outline">{typeof me?.ttl === "number" ? `${me.ttl}s` : "n/d"}</Badge>
                </div>
                <Badge variant={me ? "default" : "destructive"}>{me ? "Conectado" : "Falha"}</Badge>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Últimas proposições</CardTitle>
            <CardDescription>Resumo das discussões recentes.</CardDescription>
          </CardHeader>
          <CardContent>
            {propositionsQuery.isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-4" />
                <Skeleton className="h-4" />
                <Skeleton className="h-4" />
              </div>
            ) : propositionsQuery.data?.items?.length ? (
              <ul className="space-y-2 text-sm">
                {propositionsQuery.data.items.slice(0, 3).map((item, index) => (
                  <li key={String(item.id ?? index)} className="line-clamp-1">
                    {item.title ?? JSON.stringify(item).slice(0, 80)}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">Sem dados no momento.</p>
            )}
            <div className="mt-4">
              <Button asChild variant="outline" size="sm">
                <Link href="/propositions">Abrir proposições</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {lastResult ? (
        <Card>
          <CardHeader>
            <CardTitle>Último resultado em cache</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-44 overflow-auto rounded-md border bg-muted/30 p-3 text-xs">
              {JSON.stringify(lastResult, null, 2)}
            </pre>
          </CardContent>
        </Card>
      ) : null}

      <ApiErrorNotice error={(propositionsQuery.error as Error | null) ?? (meQuery.error as Error | null)} />
    </section>
  );
}
