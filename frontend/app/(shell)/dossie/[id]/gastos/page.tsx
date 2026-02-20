"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { getExpensesByParlamentar } from "@/lib/data";
import { useUiStore } from "@/lib/state/ui.store";

import { PageHeaderV2 } from "@/components/layout/page-header-v2";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { GlossyCard } from "@/components/ui/glossy-card";
import { Label } from "@/components/typography/Label";
import { TimelineVoteEntry } from "@/components/votes/TimelineVoteEntry";

function money(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

export default function DossieGastosPage() {
  const params = useParams<{ id: string }>();
  const setSelectedParlamentar = useUiStore((state) => state.setSelectedParlamentar);

  useEffect(() => {
    setSelectedParlamentar(params.id);
  }, [params.id, setSelectedParlamentar]);

  const expensesQuery = useQuery({
    queryKey: ["expenses", params.id],
    queryFn: () => getExpensesByParlamentar(params.id),
  });

  if (expensesQuery.isLoading) return <LoadingState />;
  if (expensesQuery.isError) return <ErrorState message="Falha ao carregar despesas." onRetry={() => expensesQuery.refetch()} />;

  const total = expensesQuery.data?.reduce((acc, item) => acc + item.value, 0) ?? 0;
  const outliers = expensesQuery.data?.filter((item) => item.outlier) ?? [];
  const topSuppliers = [...(expensesQuery.data ?? [])]
    .sort((a, b) => b.value - a.value)
    .slice(0, 4);

  return (
    <div className="v2-content">
      <section className="space-y-6">
        <PageHeaderV2
          kicker="Monitoramento financeiro"
          title="Gastos"
          subtitle="CEAP, verbas e outliers de despesas recentes."
        />

        <div className="grid grid-cols-4 gap-4 max-xl:grid-cols-2 max-md:grid-cols-1">
          <GlossyCard className="p-5">
            <Label>CEAP</Label>
            <p className="mt-2 text-3xl font-bold text-[var(--v2-text-main)]">{money(total * 0.52)}</p>
          </GlossyCard>
          <GlossyCard className="p-5">
            <Label>Verbas de Gabinete</Label>
            <p className="mt-2 text-3xl font-bold text-[var(--v2-text-main)]">{money(total * 0.28)}</p>
          </GlossyCard>
          <GlossyCard className="p-5">
            <Label>Maiores Fornecedores</Label>
            <p className="mt-2 text-3xl font-bold text-[var(--v2-text-main)]">{topSuppliers.length}</p>
          </GlossyCard>
          <GlossyCard className="p-5">
            <Label>Outliers</Label>
            <p className="mt-2 text-3xl font-bold text-[var(--v2-text-main)]">{outliers.length}</p>
          </GlossyCard>
        </div>

        <div className="grid grid-cols-[2fr_1fr] gap-4 max-xl:grid-cols-1">
          <GlossyCard className="p-0">
            <div className="v2-card-head">
              <Label className="mb-0">Decomposição de Gastos (Anual)</Label>
            </div>
            <div className="flex gap-8 p-6 max-lg:flex-col">
              <div className="flex h-44 flex-1 items-end gap-2 rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-canvas-deep)] p-3">
                {[78, 46, 62, 41, 89, 33].map((h, i) => (
                  <div
                    key={h + i}
                    style={{
                      height: `${h}%`,
                      width: "100%",
                      borderRadius: "3px 3px 0 0",
                      background: i % 2 === 0 ? "var(--v2-accent)" : "var(--v2-text-subtle)",
                      opacity: i % 2 === 0 ? 1 : 0.42,
                    }}
                  />
                ))}
              </div>
              <div className="w-[210px] space-y-3">
                <div>
                  <Label>Total acumulado</Label>
                  <p className="mt-1 text-2xl font-bold text-[var(--v2-text-main)]">{money(total)}</p>
                </div>
                <div>
                  <Label>Principais rubricas</Label>
                  <p className="mt-1 text-sm text-[var(--v2-text-muted)]">
                    • Divulgação: 45%
                    <br />
                    • Consultoria: 30%
                    <br />
                    • Viagens: 15%
                  </p>
                </div>
              </div>
            </div>
          </GlossyCard>

          <GlossyCard className="p-0">
            <div className="v2-card-head">
              <Label className="mb-0">Maiores Fornecedores</Label>
            </div>
            <div className="space-y-1 p-6">
              {topSuppliers.map((item) => (
                <div key={item.id} className="v2-stat-list-item">
                  <span className="text-sm text-[var(--v2-text-main)]">{item.vendor}</span>
                  <Label>{money(item.value)}</Label>
                </div>
              ))}
            </div>
          </GlossyCard>
        </div>

        <GlossyCard className="p-0">
          <div className="v2-card-head">
            <Label className="mb-0">Movimentação Recente</Label>
          </div>
          <div className="space-y-4 p-6">
            {expensesQuery.data?.slice(0, 10).map((expense) => (
              <div key={expense.id}>
                <TimelineVoteEntry
                  date={expense.date}
                  outcome={expense.outlier ? "Adiado/Abst." : "Aprovado"}
                  topic={expense.category}
                  code={expense.vendor}
                  yes={Math.round(expense.value)}
                  no={0}
                  abstention={expense.outlier ? 1 : 0}
                />
                <div className="ml-8 mt-1 text-xs text-[var(--v2-text-muted)]">
                  Valor {money(expense.value)}
                  {expense.outlier ? (
                    <span className="ml-2 rounded-[4px] border border-[var(--v2-danger)] bg-[color-mix(in_srgb,var(--v2-danger)_18%,transparent)] px-2 py-0.5 font-[var(--font-ui-mono)] text-[10px] uppercase tracking-[0.1em] text-[var(--v2-danger-soft)]">
                      Outlier
                    </span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </GlossyCard>
      </section>
    </div>
  );
}
