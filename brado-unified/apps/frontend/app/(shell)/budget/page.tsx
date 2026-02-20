"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, Info } from "lucide-react";
import { z } from "zod";

import { apiClient } from "@/lib/api/client";

import { ApiErrorNotice } from "@/components/api-error-notice";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";
import { useToast } from "@/components/ui/use-toast";

const categories = [
  "Saúde",
  "Educação",
  "Segurança",
  "Infraestrutura",
  "Assistência social",
  "Meio ambiente",
] as const;

const schema = z.object({
  allocations: z.array(
    z.object({
      category: z.string(),
      percent: z.number().min(0).max(100),
    })
  ),
});

export default function BudgetPage() {
  const { toast } = useToast();
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
      const payload = {
        allocations: categories.map((category) => ({
          category,
          percent: values[category],
        })),
      };

      schema.parse(payload);
      return apiClient.budget.simulate(payload);
    },
    onError: (error: Error) => {
      toast({ title: "Falha na simulação", description: error.message, variant: "destructive" });
    },
  });

  const setCategory = (category: string, value: number) => {
    const safe = Math.max(0, Math.min(100, Math.round(value)));
    setValues((prev) => ({ ...prev, [category]: safe }));
  };

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Simulador de Orçamento</h1>
        <p className="text-sm text-muted-foreground">Ajuste percentuais e veja tradeoffs da distribuição.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Alocação por categoria</CardTitle>
          <CardDescription>Total precisa fechar exatamente em 100% para simular.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {categories.map((category) => (
            <div key={category} className="grid gap-2 md:grid-cols-[180px_1fr_100px] md:items-center">
              <Label>{category}</Label>
              <Slider value={[values[category]]} min={0} max={100} step={1} onValueChange={([value]) => setCategory(category, value)} />
              <Input
                type="number"
                min={0}
                max={100}
                value={values[category]}
                onChange={(event) => setCategory(category, Number(event.target.value))}
              />
            </div>
          ))}

          <div className="space-y-2 rounded-lg border bg-muted/20 p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total</span>
              <Badge variant={isValidTotal ? "default" : "destructive"}>{total}%</Badge>
            </div>
            <Progress value={Math.min(total, 100)} />
            {!isValidTotal ? (
              <p className="text-xs text-destructive">Ajuste para 100% para liberar a simulação.</p>
            ) : null}
          </div>

          <Button onClick={() => mutation.mutate()} disabled={!isValidTotal || mutation.isPending}>
            {mutation.isPending ? "Simulando..." : "Simular orçamento"}
          </Button>
        </CardContent>
      </Card>

      {mutation.data ? (
        <Card>
          <CardHeader>
            <CardTitle>Resultado da simulação</CardTitle>
            <CardDescription>
              Valid: <Badge variant={mutation.data.valid ? "default" : "destructive"}>{String(mutation.data.valid)}</Badge>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-sm text-muted-foreground">Total retornado: {mutation.data.total_percent}%</p>
            <ul className="space-y-2">
              {mutation.data.tradeoffs?.length ? (
                mutation.data.tradeoffs.map((tradeoff, index) => (
                  <li key={`${tradeoff}-${index}`} className="flex items-start gap-2 rounded-md border p-2 text-sm">
                    {tradeoff.toLowerCase().includes("risco") ? (
                      <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-600" />
                    ) : (
                      <Info className="mt-0.5 h-4 w-4 text-blue-600" />
                    )}
                    <span>{tradeoff}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-muted-foreground">Sem tradeoffs retornados.</li>
              )}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      <ApiErrorNotice error={mutation.error as Error | null} />
    </section>
  );
}
