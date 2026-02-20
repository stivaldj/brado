"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { Download, Eye } from "lucide-react";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";

import { apiClient } from "@/lib/api/client";
import { normalizeResult } from "@/lib/format/interview";
import { useSessionStore } from "@/lib/state/session.store";

import { ApiErrorNotice } from "@/components/api-error-notice";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/use-toast";

function buildRadarData(vetor?: Record<string, number>) {
  if (!vetor) return [];
  return Object.entries(vetor).map(([dimension, value]) => ({ dimension, value }));
}

function getMetric(value: number | undefined) {
  return typeof value === "number" ? value.toFixed(3) : "n/d";
}

export default function ResultsPage() {
  const { toast } = useToast();
  const sessionId = useSessionStore((state) => state.sessionId);
  const lastResult = useSessionStore((state) => state.lastResult);
  const setLastResult = useSessionStore((state) => state.setLastResult);

  const fetchResult = useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error("Sem sessão ativa");
      return apiClient.interview.result(sessionId);
    },
    onSuccess: (payload) => {
      const normalized = normalizeResult(payload);
      setLastResult(normalized);
      toast({ title: "Resultado atualizado" });
    },
    onError: (error: Error) => {
      toast({ title: "Falha ao carregar resultado", description: error.message, variant: "destructive" });
    },
  });

  const exportMutation = useMutation({
    mutationFn: async (format: "json" | "pdf") => {
      if (!sessionId) throw new Error("Sem sessão ativa");
      const blob = await apiClient.interview.exportFile(sessionId, format);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `resultado-${sessionId}.${format}`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    },
    onSuccess: () => {
      toast({ title: "Export concluído" });
    },
    onError: (error: Error) => {
      toast({ title: "Falha no export", description: error.message, variant: "destructive" });
    },
  });

  const result = lastResult;
  const metrics = result?.metricas;
  const ranking = result?.ranking ?? [];
  const radarData = buildRadarData(result?.vetor);

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Resultados</h1>
          <p className="text-sm text-muted-foreground">Métricas, vetor 8D e ranking explicável.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => fetchResult.mutate()} disabled={!sessionId || fetchResult.isPending}>
            {fetchResult.isPending ? "Atualizando..." : "Atualizar resultado"}
          </Button>
          <Button variant="outline" onClick={() => exportMutation.mutate("json")} disabled={!sessionId || exportMutation.isPending}>
            <Download className="mr-1 h-4 w-4" /> Exportar JSON
          </Button>
          <Button onClick={() => exportMutation.mutate("pdf")} disabled={!sessionId || exportMutation.isPending}>
            <Download className="mr-1 h-4 w-4" /> Exportar PDF
          </Button>
        </div>
      </div>

      {!result ? (
        <Card>
          <CardHeader>
            <CardTitle>Sem resultado em cache</CardTitle>
            <CardDescription>Finalize a entrevista ou clique em atualizar resultado.</CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      <Tabs defaultValue="analise" className="space-y-4">
        <TabsList>
          <TabsTrigger value="analise">Análise</TabsTrigger>
          <TabsTrigger value="raw">RAW JSON</TabsTrigger>
        </TabsList>

        <TabsContent value="analise" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Esquerda-Direita</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold">{getMetric(metrics?.esquerda_direita)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Confiança</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold">{getMetric(metrics?.confianca)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Consistência</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold">{getMetric(metrics?.consistencia)}</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Vetor 8D</CardTitle>
              <CardDescription>Representação radar das dimensões calculadas.</CardDescription>
            </CardHeader>
            <CardContent>
              {radarData.length ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="dimension" />
                      <Radar dataKey="value" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.4} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Vetor indisponível.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Ranking</CardTitle>
              <CardDescription>Lista de similaridade com explicações detalhadas.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Nome</TableHead>
                    <TableHead>Sigla</TableHead>
                    <TableHead>Similaridade</TableHead>
                    <TableHead>Ação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ranking.length ? (
                    ranking.map((item, index) => (
                      <TableRow key={`${item.nome}-${index}`}>
                        <TableCell>
                          <Badge variant="outline">{item.tipo ?? "n/d"}</Badge>
                        </TableCell>
                        <TableCell>{item.nome}</TableCell>
                        <TableCell>{item.sigla ?? "-"}</TableCell>
                        <TableCell>{item.similaridade.toFixed(3)}</TableCell>
                        <TableCell>
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="outline" size="sm">
                                <Eye className="mr-1 h-4 w-4" /> Ver explicação
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>{item.nome}</DialogTitle>
                                <DialogDescription>{item.sigla ?? "Sem sigla"}</DialogDescription>
                              </DialogHeader>
                              <p className="mt-3 text-sm leading-6">{item.explicacao ?? "Explicação indisponível."}</p>
                              <DialogClose asChild>
                                <Button className="mt-4" variant="outline">
                                  Fechar
                                </Button>
                              </DialogClose>
                            </DialogContent>
                          </Dialog>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground">
                        Ranking indisponível.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="raw">
          <Card>
            <CardHeader>
              <CardTitle>Resultado bruto</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-[560px] overflow-auto rounded-md border bg-muted/30 p-3 text-xs">
                {JSON.stringify(result ?? {}, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <ApiErrorNotice error={(fetchResult.error as Error | null) ?? (exportMutation.error as Error | null)} />
    </section>
  );
}
