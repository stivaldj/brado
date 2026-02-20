"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Bot, CircleDollarSign, LayoutList, Users2 } from "lucide-react";

import { apiClient } from "@/lib/api/client";
import { getPropositions } from "@/lib/data";
import { useSessionStore } from "@/lib/state/session.store";

const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

function QuickCard({
  href,
  icon: Icon,
  label,
  description,
}: {
  href: string;
  icon: React.FC<{ className?: string }>;
  label: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="group flex items-start gap-4 rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)] p-5 transition-all hover:border-[var(--v2-accent)] hover:bg-[color-mix(in_srgb,var(--v2-accent)_5%,var(--v2-bg-surface))]"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] transition-colors group-hover:border-[var(--v2-accent)] group-hover:text-[var(--v2-accent)]">
        <Icon className="h-4 w-4 text-[var(--v2-text-subtle)] group-hover:text-[var(--v2-accent)]" />
      </div>
      <div>
        <p className="font-semibold text-[var(--v2-text-main)]">{label}</p>
        <p className="mt-0.5 text-xs text-[var(--v2-text-muted)]">{description}</p>
      </div>
    </Link>
  );
}

function StatTile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)] p-5">
      <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">{label}</p>
      <p className="mt-2 text-2xl font-bold text-[var(--v2-text-main)]">{value}</p>
      {sub ? <p className="mt-1 text-xs text-[var(--v2-text-muted)]">{sub}</p> : null}
    </div>
  );
}

export default function DashboardPage() {
  const sessionId = useSessionStore((state) => state.sessionId);
  const answeredCount = useSessionStore((state) => state.answeredCount);
  const lastResult = useSessionStore((state) => state.lastResult);

  const propositionsQuery = useQuery({
    queryKey: ["propositions", "macro"],
    queryFn: () => getPropositions(5),
  });

  const meQuery = useQuery({
    queryKey: ["auth", "dashboard"],
    queryFn: () => (useMocks ? Promise.resolve({ subject: "demo-user" }) : apiClient.authMe()),
  });

  const topParty = lastResult?.ranking?.[0];

  return (
    <div className="v2-content">
      {/* Header */}
      <header>
        <p className="v2-page-kicker">Brado · Plataforma cívica</p>
        <h1 className="text-[22px] font-bold leading-[1.2] text-[var(--v2-text-main)]">Dashboard</h1>
        <p className="mt-1 text-[13px] text-[var(--v2-text-muted)]">
          Visão geral da sessão, entrevista e dados legislativos.
        </p>
      </header>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile
          label="Sessão"
          value={sessionId ? "Ativa" : "Inativa"}
          sub={sessionId ? `${answeredCount} respostas` : "Inicie a entrevista"}
        />
        <StatTile
          label="API"
          value={meQuery.data ? "Conectada" : meQuery.isLoading ? "..." : "Erro"}
          sub={meQuery.data?.subject ?? "backend"}
        />
        <StatTile
          label="Proposições"
          value={String(propositionsQuery.data?.items.length ?? 0)}
          sub="últimas carregadas"
        />
        <StatTile
          label="Seu partido"
          value={topParty?.sigla ?? "—"}
          sub={topParty ? `Sim. ${(topParty.similaridade * 100).toFixed(0)}%` : "Complete a entrevista"}
        />
      </div>

      {/* Quick access */}
      <section>
        <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">
          Acesso rápido
        </p>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <QuickCard
            href="/parlamentares"
            icon={Users2}
            label="Parlamentares"
            description="Lista e filtros de todos os 513 deputados federais com dados reais da Câmara."
          />
          <QuickCard
            href="/propositions"
            icon={LayoutList}
            label="Proposições"
            description="Projetos de lei em tramitação com busca textual e filtros."
          />
          <QuickCard
            href="/interview"
            icon={Bot}
            label="Entrevista política"
            description="25 questões Likert para mapear seu posicionamento em 8 dimensões."
          />
          <QuickCard
            href="/results"
            icon={BarChart3}
            label="Resultados"
            description="Radar 8D e ranking de partidos com base na sua entrevista."
          />
          <QuickCard
            href="/budget"
            icon={CircleDollarSign}
            label="Simulador de orçamento"
            description="Distribua verbas por categoria e veja os impactos estimados."
          />
        </div>
      </section>

      {/* Two-column: feed + ranking */}
      <div className="grid gap-4 xl:grid-cols-[1fr_300px]">
        {/* Propositions feed */}
        <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
          <div className="border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-5 py-3">
            <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">
              Feed de proposições
            </span>
          </div>
          <div className="divide-y divide-[var(--v2-border)]">
            {propositionsQuery.isLoading ? (
              <p className="p-5 text-sm text-[var(--v2-text-muted)]">Carregando...</p>
            ) : propositionsQuery.data?.items.length ? (
              propositionsQuery.data.items.map((item, i) => (
                <div key={String(item.id ?? i)} className="flex items-center justify-between gap-4 px-5 py-3">
                  <span className="text-sm text-[var(--v2-text-main)]">{item.title ?? `Proposição ${i + 1}`}</span>
                  <span className="shrink-0 rounded-[5px] border border-[var(--v2-border)] px-2 py-0.5 font-mono text-[10px] text-[var(--v2-text-subtle)]">
                    {item.sigla ?? "n/d"}
                  </span>
                </div>
              ))
            ) : (
              <p className="p-5 text-sm text-[var(--v2-text-muted)]">Nenhuma proposição carregada.</p>
            )}
          </div>
        </div>

        {/* Last interview result */}
        <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
          <div className="border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-4 py-3">
            <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">
              Último ranking
            </span>
          </div>
          {lastResult?.ranking?.length ? (
            <div className="divide-y divide-[var(--v2-border)]">
              {lastResult.ranking.slice(0, 6).map((item, i) => (
                <div key={`${item.nome}-${i}`} className="flex items-center justify-between px-4 py-2.5">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-[10px] text-[var(--v2-text-subtle)]">
                      #{i + 1}
                    </span>
                    <div>
                      <p className="text-[13px] font-semibold text-[var(--v2-text-main)]">{item.nome}</p>
                      <p className="text-[10px] text-[var(--v2-text-subtle)]">{item.sigla ?? "—"}</p>
                    </div>
                  </div>
                  <span
                    className="font-mono text-[12px] font-bold"
                    style={{ color: i === 0 ? "var(--v2-accent)" : "var(--v2-text-muted)" }}
                  >
                    {(item.similaridade * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-5">
              <p className="text-sm text-[var(--v2-text-muted)]">Sem resultado disponível.</p>
              <Link
                href="/interview"
                className="mt-3 inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-[0.08em] text-[var(--v2-accent)] hover:underline"
              >
                Iniciar entrevista →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
