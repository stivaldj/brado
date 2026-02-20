"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { z } from "zod";

import { apiClient } from "@/lib/api/client";

import { PageHeaderV2 } from "@/components/layout/page-header-v2";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GlossyCard } from "@/components/ui/glossy-card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";

const categories = ["Saúde", "Educação", "Segurança", "Infraestrutura", "Assistência social", "Meio ambiente"] as const;

const schema = z.object({
  allocations: z.array(
    z.object({
      category: z.string(),
      percent: z.number().min(0).max(100),
    })
  ),
});

export default function BudgetPage() {
  const [values, setValues] = React.useState<Record<string, number>>({
    Saúde: 20,
    Educação: 20,
    Segurança: 15,
    Infraestrutura: 15,
    "Assistência social": 15,
    "Meio ambiente": 15,
  });

  const total = Object.values(values).reduce((acc, value) => acc + value, 0);
  const isValidTotal = total === 100;

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = { allocations: categories.map((category) => ({ category, percent: values[category] })) };
      schema.parse(payload);
      return apiClient.budget.simulate(payload);
    },
  });

  const setCategory = (category: string, value: number) => {
    const safe = Math.max(0, Math.min(100, Math.round(value)));
    setValues((prev) => ({ ...prev, [category]: safe }));
  };

  return (
    <div className="v2-content">
      <section className="space-y-6">
        <PageHeaderV2
          kicker="Impacto estimado"
          title="Simulador de Orçamento"
          subtitle="Ajuste percentuais e valide tradeoffs da distribuição."
        />

        <div className="grid grid-cols-3 gap-4 max-xl:grid-cols-1">
          <GlossyCard className="xl:col-span-2 p-0">
            <div className="v2-card-head">
              <p className="v2-card-kicker">Distribuição por categoria</p>
            </div>
            <div className="space-y-4 p-6">
              {categories.map((category) => (
                <div key={category} className="grid grid-cols-[180px_1fr_100px] items-center gap-2 max-md:grid-cols-1">
                  <span className="text-sm text-[var(--v2-text-muted)]">{category}</span>
                  <Slider value={[values[category]]} min={0} max={100} step={1} onValueChange={([value]) => setCategory(category, value)} />
                  <Input type="number" min={0} max={100} value={values[category]} onChange={(event) => setCategory(category, Number(event.target.value))} />
                </div>
              ))}

              <div className="mt-6 rounded-md border border-[var(--v2-border)] bg-[var(--v2-bg-canvas-deep)] p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm text-[var(--v2-text-muted)]">Total</span>
                  <Badge variant={isValidTotal ? "default" : "destructive"}>{total}%</Badge>
                </div>
                <Progress value={Math.min(total, 100)} />
              </div>

              <Button className="mt-4" onClick={() => mutation.mutate()} disabled={!isValidTotal || mutation.isPending}>
                {mutation.isPending ? "Simulando..." : "Simular orçamento"}
              </Button>
            </div>
          </GlossyCard>

          <GlossyCard className="p-0">
            <div className="v2-card-head">
              <p className="v2-card-kicker">Resultado</p>
            </div>
            <div className="p-6">
              {mutation.data ? (
                <>
                  <p className="mt-3 text-sm text-[var(--v2-text-muted)]">Total retornado: {mutation.data.total_percent}%</p>
                  <ul className="mt-3 space-y-2 text-sm">
                    {(mutation.data.tradeoffs ?? []).map((tradeoff, index) => (
                      <li key={`${tradeoff}-${index}`} className="rounded-md border border-[var(--v2-border)] p-2">{tradeoff}</li>
                    ))}
                  </ul>
                </>
              ) : (
                <p className="mt-3 text-sm text-[var(--v2-text-muted)]">Sem simulação executada.</p>
              )}
            </div>
          </GlossyCard>
        </div>
      </section>
    </div>
  );
}
