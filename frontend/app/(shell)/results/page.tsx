"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";

import { apiClient } from "@/lib/api/client";
import { normalizeResult } from "@/lib/format/interview";
import { useSessionStore } from "@/lib/state/session.store";

import { PageHeaderV2 } from "@/components/layout/page-header-v2";
import { EmptyTableState } from "@/components/states/empty-table-state";
import { Button } from "@/components/ui/button";
import { GlossyCard } from "@/components/ui/glossy-card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

function buildRadarData(vetor?: Record<string, number>) {
  if (!vetor) return [];
  return Object.entries(vetor).map(([dimension, value]) => ({ dimension, value }));
}

export default function ResultsPage() {
  const sessionId = useSessionStore((state) => state.sessionId);
  const lastResult = useSessionStore((state) => state.lastResult);
  const setLastResult = useSessionStore((state) => state.setLastResult);

  const fetchResult = useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error("Sem sessão ativa");
      return apiClient.interview.result(sessionId);
    },
    onSuccess: (payload) => setLastResult(normalizeResult(payload)),
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
  });

  const radarData = buildRadarData(lastResult?.vetor);

  return (
    <div className="v2-content">
      <section className="space-y-6">
        <PageHeaderV2
          kicker="Análise de resultado"
          title="Resultados"
          subtitle="Métricas consolidadas, vetor de dimensões e ranking explicável."
          rightSlot={
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => fetchResult.mutate()} disabled={!sessionId || fetchResult.isPending}>Atualizar</Button>
              <Button variant="outline" onClick={() => exportMutation.mutate("json")} disabled={!sessionId}><Download className="mr-1 h-4 w-4" />JSON</Button>
              <Button onClick={() => exportMutation.mutate("pdf")} disabled={!sessionId}><Download className="mr-1 h-4 w-4" />PDF</Button>
            </div>
          }
        />

        {!lastResult ? <EmptyTableState title="Sem resultado em cache" description="Finalize a entrevista para gerar o primeiro resultado." /> : null}

        <Tabs defaultValue="analise">
          <TabsList>
            <TabsTrigger value="analise">Análise</TabsTrigger>
            <TabsTrigger value="raw">RAW JSON</TabsTrigger>
          </TabsList>

          <TabsContent value="analise" className="mt-4 space-y-4">
            <div className="grid grid-cols-3 gap-4 max-xl:grid-cols-2 max-md:grid-cols-1">
              <GlossyCard className="p-5"><p className="text-xs text-[var(--v2-text-subtle)]">Esquerda-Direita</p><p className="mt-2 text-2xl font-bold text-[var(--v2-text-main)]">{lastResult?.metricas?.esquerda_direita?.toFixed(3) ?? "n/d"}</p></GlossyCard>
              <GlossyCard className="p-5"><p className="text-xs text-[var(--v2-text-subtle)]">Confiança</p><p className="mt-2 text-2xl font-bold text-[var(--v2-text-main)]">{lastResult?.metricas?.confianca?.toFixed(3) ?? "n/d"}</p></GlossyCard>
              <GlossyCard className="p-5"><p className="text-xs text-[var(--v2-text-subtle)]">Consistência</p><p className="mt-2 text-2xl font-bold text-[var(--v2-text-main)]">{lastResult?.metricas?.consistencia?.toFixed(3) ?? "n/d"}</p></GlossyCard>
            </div>

            <div className="grid grid-cols-5 gap-4 max-xl:grid-cols-1">
              <GlossyCard className="xl:col-span-3 p-0" hoverLift={false}>
                <div className="v2-card-head">
                  <p className="v2-card-kicker">Vetor 8D</p>
                </div>
                <div className="h-72 p-5">
                  {radarData.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="var(--v2-border-strong)" />
                        <PolarAngleAxis dataKey="dimension" tick={{ fill: "var(--v2-text-muted)", fontSize: 11 }} />
                        <Radar dataKey="value" stroke="var(--v2-accent)" fill="var(--v2-accent)" fillOpacity={0.35} />
                      </RadarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="mt-8 text-sm text-[var(--v2-text-muted)]">Vetor indisponível.</p>
                  )}
                </div>
              </GlossyCard>

              <GlossyCard className="xl:col-span-2 p-0" hoverLift={false}>
                <div className="v2-card-head">
                  <p className="v2-card-kicker">Ranking</p>
                </div>
                <ul className="space-y-2 p-5 text-sm">
                  {lastResult?.ranking?.length ? (
                    lastResult.ranking.map((item, index) => (
                      <li key={`${item.nome}-${index}`} className="rounded-md border border-[var(--v2-border)] p-3">
                        <p className="font-semibold text-[var(--v2-text-main)]">{item.nome}</p>
                        <p className="text-xs text-[var(--v2-text-muted)]">{item.sigla ?? "sem sigla"} · {item.similaridade.toFixed(3)}</p>
                      </li>
                    ))
                  ) : (
                    <li className="text-[var(--v2-text-muted)]">Ranking indisponível.</li>
                  )}
                </ul>
              </GlossyCard>
            </div>
          </TabsContent>

          <TabsContent value="raw" className="mt-4">
            <GlossyCard className="p-0" hoverLift={false}>
              <div className="v2-card-head">
                <p className="v2-card-kicker">RAW JSON</p>
              </div>
              <pre className="m-5 max-h-[560px] overflow-auto rounded-md border border-[var(--v2-border)] bg-[var(--v2-bg-canvas-deep)] p-3 text-xs text-[var(--v2-text-muted)]">
                {JSON.stringify(lastResult ?? {}, null, 2)}
              </pre>
            </GlossyCard>
          </TabsContent>
        </Tabs>
      </section>
    </div>
  );
}
