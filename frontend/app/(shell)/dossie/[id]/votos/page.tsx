"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { EmptyDossieState } from "@/components/states/empty-dossie-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { PageHeaderV2 } from "@/components/layout/page-header-v2";
import { Label } from "@/components/typography/Label";
import { Badge } from "@/components/ui/badge";
import { GlossyCard } from "@/components/ui/glossy-card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TimelineVoteEntry } from "@/components/votes/TimelineVoteEntry";
import { VoteCard } from "@/components/votes/VoteCard";
import { getExpensesByParlamentar, getParlamentarById, getVotesByParlamentar } from "@/lib/data";
import { useUiStore } from "@/lib/state/ui.store";

function toCurrency(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(value);
}

export default function DossieVotosPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const setSelectedParlamentar = useUiStore((state) => state.setSelectedParlamentar);

  useEffect(() => {
    setSelectedParlamentar(id);
  }, [id, setSelectedParlamentar]);

  const parlamentarQuery = useQuery({
    queryKey: ["parlamentar", id],
    queryFn: () => getParlamentarById(id),
  });
  const votesQuery = useQuery({
    queryKey: ["votes", id],
    queryFn: () => getVotesByParlamentar(id),
  });
  const expensesQuery = useQuery({
    queryKey: ["expenses", id],
    queryFn: () => getExpensesByParlamentar(id),
  });

  if (parlamentarQuery.isLoading || votesQuery.isLoading || expensesQuery.isLoading) return <LoadingState />;
  if (parlamentarQuery.isError || votesQuery.isError || expensesQuery.isError) {
    return (
      <ErrorState
        message="Falha ao carregar o dossiê de votações."
        onRetry={() => {
          parlamentarQuery.refetch();
          votesQuery.refetch();
          expensesQuery.refetch();
        }}
      />
    );
  }

  const parlamentar = parlamentarQuery.data;
  const votes = votesQuery.data ?? [];
  const expenses = expensesQuery.data ?? [];
  if (!parlamentar || votes.length === 0) return <EmptyDossieState parlamentarId={id} />;

  const alignedCount = votes.filter((item) => item.alignedWithParty).length;
  const favorableCount = votes.filter((item) => item.voteType === "favor").length;
  const controversyCount = votes.filter((item) => item.controversial).length;
  const approvalCount = votes.filter((item) => item.outcome === "Aprovado").length;
  const totalSpent = expenses.reduce((acc, item) => acc + item.value, 0);
  const metrics = {
    alignmentPercent: Math.round((alignedCount / votes.length) * 100),
    favorablePercent: Math.round((favorableCount / votes.length) * 100),
    controversyCount,
    approvalPercent: Math.round((approvalCount / votes.length) * 100),
    totalSpent,
  };

  const latestVotes = votes.slice(0, 6);
  const timelineVotes = votes.slice(0, 20);
  const topVendors = [...expenses].sort((a, b) => b.value - a.value).slice(0, 4);

  return (
    <div className="v2-content">
      <section className="space-y-6">
        <PageHeaderV2
          kicker="Dossiê por abas"
          title={parlamentar.name}
          subtitle={`${parlamentar.role} · ${parlamentar.uf} · ${parlamentar.party}`}
          rightSlot={
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{parlamentar.party}</Badge>
              <Badge variant="secondary">Alinhamento {metrics.alignmentPercent}%</Badge>
              <Badge variant={metrics.controversyCount > 10 ? "destructive" : "outline"}>Controvérsias {metrics.controversyCount}</Badge>
            </div>
          }
        />

        <GlossyCard className="p-6 md:p-7" hoverLift={false}>
          <div className="grid grid-cols-[1.4fr_1fr] gap-6 max-lg:grid-cols-1">
            <div>
              <Label>Resumo analítico</Label>
              <p className="mt-2 text-lg leading-7 text-[var(--v2-text-main)]">
                Atuação concentrada em votações de alto impacto, com padrão de alinhamento partidário estável e variação de
                posicionamento em pautas controversas.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge variant="secondary">{votes.length} votações monitoradas</Badge>
                <Badge variant="outline">{expenses.length} despesas analisadas</Badge>
                <Badge variant="outline">Perfil {parlamentar.uf}</Badge>
              </div>
            </div>
            <div className="rounded-[14px] border border-[var(--v2-border)] bg-[var(--v2-bg-canvas-deep)] p-4">
              <Label>Risco reputacional</Label>
              <p className="mt-2 text-3xl font-bold text-[var(--v2-text-main)]">{metrics.controversyCount}</p>
              <p className="mt-2 text-sm text-[var(--v2-text-muted)]">Eventos com alta divergência pública nas últimas janelas de votação.</p>
            </div>
          </div>
        </GlossyCard>

        <div className="grid grid-cols-4 gap-4 max-xl:grid-cols-2 max-md:grid-cols-1">
          <GlossyCard className="p-5">
            <Label>Alinhamento partidário</Label>
            <p className="mt-2 text-3xl font-bold text-[var(--v2-text-main)]">{metrics.alignmentPercent}%</p>
            <Progress value={metrics.alignmentPercent} className="mt-3" />
          </GlossyCard>
          <GlossyCard className="p-5">
            <Label>Votos favoráveis</Label>
            <p className="mt-2 text-3xl font-bold text-[var(--v2-text-main)]">{metrics.favorablePercent}%</p>
            <Progress value={metrics.favorablePercent} className="mt-3" />
          </GlossyCard>
          <GlossyCard className="p-5">
            <Label>Taxa de aprovação</Label>
            <p className="mt-2 text-3xl font-bold text-[var(--v2-text-main)]">{metrics.approvalPercent}%</p>
            <Progress value={metrics.approvalPercent} className="mt-3" />
          </GlossyCard>
          <GlossyCard className="p-5">
            <Label>Despesa anual</Label>
            <p className="mt-2 text-3xl font-bold text-[var(--v2-text-main)]">{toCurrency(metrics.totalSpent)}</p>
            <p className="mt-3 text-sm text-[var(--v2-text-muted)]">{expenses.length} lançamentos monitorados</p>
          </GlossyCard>
        </div>

        <div className="grid grid-cols-[2fr_1fr] gap-4 max-xl:grid-cols-1">
          <GlossyCard className="p-6" hoverLift={false}>
            <Tabs defaultValue="cards">
              <TabsList>
                <TabsTrigger value="cards">Votos recentes</TabsTrigger>
                <TabsTrigger value="timeline">Timeline</TabsTrigger>
              </TabsList>

              <TabsContent value="cards" className="mt-4">
                <div className="grid grid-cols-2 gap-4 max-lg:grid-cols-1">
                  {latestVotes.map((vote) => (
                    <VoteCard
                      key={vote.id}
                      date={vote.date}
                      title={vote.title}
                      description={vote.description}
                      voteType={vote.voteType}
                      alignedWithParty={vote.alignedWithParty}
                      controversial={vote.controversial}
                    />
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="timeline" className="mt-4">
                <div className="space-y-4">
                  {timelineVotes.map((vote) => (
                    <TimelineVoteEntry
                      key={vote.id}
                      date={vote.date}
                      outcome={vote.outcome}
                      topic={vote.topic}
                      code={vote.code}
                      yes={vote.yes}
                      no={vote.no}
                      abstention={vote.abstention}
                    />
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </GlossyCard>

          <GlossyCard className="p-6" hoverLift={false}>
            <Label>Bio e contexto</Label>
            <p className="mt-2 text-sm leading-6 text-[var(--v2-text-muted)]">{parlamentar.bio}</p>

            <Label className="mt-6 block">Maiores fornecedores</Label>
            <div className="mt-2 space-y-2">
              {topVendors.map((expense) => (
                <div key={expense.id} className="flex items-center justify-between rounded-md border border-[var(--v2-border)] p-3">
                  <span className="text-sm text-[var(--v2-text-main)]">{expense.vendor}</span>
                  <span className="text-xs text-[var(--v2-text-muted)]">{toCurrency(expense.value)}</span>
                </div>
              ))}
            </div>
          </GlossyCard>
        </div>
      </section>
    </div>
  );
}
