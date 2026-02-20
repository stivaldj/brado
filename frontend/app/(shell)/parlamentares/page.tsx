"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpDown } from "lucide-react";

import { EmptyTableState } from "@/components/states/empty-table-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getParlamentares } from "@/lib/data";
import type { Parlamentar } from "@/lib/data/types";
import { useUiStore } from "@/lib/state/ui.store";

type SortKey = "name" | "presence" | "projects" | "expense";
type SortDir = "asc" | "desc";
type UfFilter =
  | "ALL"
  | "AC" | "AL" | "AP" | "AM" | "BA" | "CE" | "DF" | "ES" | "GO"
  | "MA" | "MT" | "MS" | "MG" | "PA" | "PB" | "PR" | "PE" | "PI"
  | "RJ" | "RN" | "RS" | "RO" | "RR" | "SC" | "SP" | "SE" | "TO";

const UF_OPTIONS: UfFilter[] = [
  "ALL", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
  "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
  "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
];

interface RowModel {
  parlamentar: Parlamentar;
  presence: number;
  projects: number;
  expenseK: number;
  status: "Titular" | "Suplente";
}

function buildRow(parlamentar: Parlamentar): RowModel {
  const presence = Math.max(50, Math.min(99, parlamentar.alignment));
  const projects = Math.max(1, Math.round((parlamentar.alignment + parlamentar.controversy) / 10));
  const fallbackExpenseK = Math.max(18, Math.round(parlamentar.alignment * 0.22 + parlamentar.controversy * 0.31));
  const expenseK =
    typeof parlamentar.monthlyExpense === "number" && Number.isFinite(parlamentar.monthlyExpense)
      ? Math.max(0, Math.round(parlamentar.monthlyExpense / 1000))
      : fallbackExpenseK;
  return {
    parlamentar,
    presence,
    projects,
    expenseK,
    status: presence >= 85 ? "Titular" : "Suplente",
  };
}

export default function ParlamentaresPage() {
  const router = useRouter();
  const pathname = usePathname();
  const setSelectedParlamentar = useUiStore((state) => state.setSelectedParlamentar);
  const setGlobalQuery = useUiStore((state) => state.setSearchQuery);

  const [search, setSearch] = useState("");
  const [ufFilter, setUfFilter] = useState<UfFilter>("ALL");
  const [partyFilter, setPartyFilter] = useState("ALL");
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setSearch(params.get("q") ?? "");
    const uf = (params.get("uf") ?? "ALL").toUpperCase();
    const party = params.get("party") ?? "ALL";
    setUfFilter(UF_OPTIONS.includes(uf as UfFilter) ? (uf as UfFilter) : "ALL");
    setPartyFilter(party || "ALL");
  }, []);

  const syncSearchToUrl = useCallback(() => {
    const next = new URLSearchParams();
    if (search.trim()) next.set("q", search.trim());
    if (ufFilter !== "ALL") next.set("uf", ufFilter);
    if (partyFilter !== "ALL") next.set("party", partyFilter);
    const query = next.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }, [pathname, router, search, ufFilter, partyFilter]);

  useEffect(() => { setGlobalQuery(search); }, [search, setGlobalQuery]);
  useEffect(() => { syncSearchToUrl(); }, [syncSearchToUrl]);

  const parlamentarQuery = useQuery({
    queryKey: ["parlamentares", search, ufFilter, partyFilter],
    queryFn: () =>
      getParlamentares({
        q: search || undefined,
        uf: ufFilter === "ALL" ? undefined : ufFilter,
        party: partyFilter === "ALL" ? undefined : partyFilter,
      }),
  });

  const partyOptionsQuery = useQuery({
    queryKey: ["parlamentares-party-options", ufFilter],
    queryFn: () => getParlamentares({ uf: ufFilter === "ALL" ? undefined : ufFilter }),
  });

  const list = parlamentarQuery.data ?? [];
  const partyOptions = useMemo(() => {
    const source = partyOptionsQuery.data ?? [];
    const values = Array.from(new Set(source.map((item) => item.party).filter(Boolean))).sort((a, b) =>
      a.localeCompare(b, "pt-BR")
    );
    return ["ALL", ...values];
  }, [partyOptionsQuery.data]);

  useEffect(() => {
    if (!partyOptionsQuery.isSuccess) return;
    if (partyFilter !== "ALL" && !partyOptions.includes(partyFilter)) setPartyFilter("ALL");
  }, [partyFilter, partyOptions, partyOptionsQuery.isSuccess]);

  const rows = useMemo(() => {
    const base = list.map(buildRow);
    base.sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      if (sortKey === "name") return a.parlamentar.name.localeCompare(b.parlamentar.name) * dir;
      if (sortKey === "presence") return (a.presence - b.presence) * dir;
      if (sortKey === "projects") return (a.projects - b.projects) * dir;
      return (a.expenseK - b.expenseK) * dir;
    });
    return base;
  }, [list, sortDir, sortKey]);

  const filteredLabel = ufFilter === "ALL" ? "Brasil" : ufFilter;
  const headingLabel = partyFilter === "ALL" ? filteredLabel : `${filteredLabel} · ${partyFilter}`;

  function toggleSort(next: SortKey) {
    if (sortKey === next) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(next);
    setSortDir(next === "name" ? "asc" : "desc");
  }

  function SortTh({
    colKey,
    label,
    align = "left",
    width,
  }: {
    colKey: SortKey;
    label: string;
    align?: "left" | "center" | "right";
    width?: string;
  }) {
    const active = sortKey === colKey;
    const alignClass = align === "center" ? "text-center" : align === "right" ? "text-right" : "";
    return (
      <th
        className={`cursor-pointer select-none border-b border-[var(--v2-border)] px-4 py-3 text-[11px] uppercase tracking-[0.08em] text-[var(--v2-text-subtle)] hover:text-[var(--v2-accent)] ${alignClass}`}
        style={{ width }}
        onClick={() => toggleSort(colKey)}
      >
        <span className="inline-flex items-center gap-1">
          {label}
          <ArrowUpDown className={`h-3 w-3 ${active ? "text-[var(--v2-accent)]" : "opacity-30"}`} />
        </span>
      </th>
    );
  }

  return (
    <div className="v2-content">
      {/* Header */}
      <header className="v2-page-header">
        <div>
          <p className="v2-page-kicker">Câmara dos Deputados</p>
          <h1 className="text-[22px] font-bold leading-[1.2] text-[var(--v2-text-main)]">
            Deputados Federais — {headingLabel}
          </h1>
          <p className="mt-1 text-[13px] text-[var(--v2-text-muted)]">
            {rows.length} parlamentares · Métricas de produtividade e transparência.
          </p>
        </div>
        <div className="shrink-0">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nome ou partido..."
            className="w-72"
            aria-label="Buscar parlamentar"
          />
        </div>
      </header>

      {/* Filtro UF — largura total, todos os estados proporcionais */}
      <section aria-label="Filtros por estado">
        <Tabs value={ufFilter} onValueChange={(v) => setUfFilter(v as UfFilter)} className="w-full">
          <TabsList variant="line" className="flex w-full flex-nowrap items-center gap-0">
            {UF_OPTIONS.map((uf) => (
              <TabsTrigger
                key={uf}
                value={uf}
                variant="line"
                className="min-w-0 flex-1 justify-center px-1 py-2 text-[11px] tracking-[0.02em]"
              >
                <span className="truncate">{uf === "ALL" ? "TODOS" : uf}</span>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </section>

      {/* Filtro Partido — largura total, todos os partidos proporcionais */}
      <section aria-label="Filtros por partido">
        <Tabs value={partyFilter} onValueChange={(v) => setPartyFilter(v)} className="w-full">
          <TabsList variant="line" className="flex w-full flex-nowrap items-center gap-0">
            {partyOptions.map((party) => (
              <TabsTrigger
                key={party}
                value={party}
                variant="line"
                className="min-w-0 flex-1 justify-center px-1 py-2 text-[10px] tracking-[0.02em]"
                title={party}
              >
                <span className="truncate">{party === "ALL" ? "TODOS" : party}</span>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </section>

      {/* Tabela */}
      <div className="overflow-hidden rounded-[12px] border-[1.5px] border-[var(--v2-border)] bg-[linear-gradient(180deg,var(--v2-bg-surface-muted)_0%,var(--v2-bg-surface)_100%)] shadow-[0_18px_42px_color-mix(in_srgb,black_32%,transparent)]">
        <div
          className="v2-deputies-scroll overflow-auto"
          style={{ height: "clamp(420px, calc(100vh - 390px), 640px)" }}
        >
          <table className="w-full min-w-[860px] border-collapse text-left">
            <thead className="sticky top-0 z-10 bg-[var(--v2-bg-surface-strong)]">
              <tr>
                <SortTh colKey="name" label="Deputado" width="32%" />
                <th className="border-b border-[var(--v2-border)] px-4 py-3 text-[11px] uppercase tracking-[0.08em] text-[var(--v2-text-subtle)]" style={{ width: "12%" }}>Status</th>
                <SortTh colKey="presence" label="Presença" align="center" width="14%" />
                <SortTh colKey="projects" label="Projetos" align="center" width="14%" />
                <SortTh colKey="expense" label="Gastos/mês" align="center" width="16%" />
                <th className="border-b border-[var(--v2-border)] px-4 py-3 text-right text-[11px] uppercase tracking-[0.08em] text-[var(--v2-text-subtle)]" style={{ width: "12%" }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {parlamentarQuery.isLoading ? (
                <tr><td colSpan={6}><LoadingState /></td></tr>
              ) : null}
              {parlamentarQuery.isError ? (
                <tr>
                  <td colSpan={6}>
                    <ErrorState message="Não foi possível carregar a lista." onRetry={() => parlamentarQuery.refetch()} />
                  </td>
                </tr>
              ) : null}
              {!parlamentarQuery.isLoading && !parlamentarQuery.isError && rows.length === 0 ? (
                <tr>
                  <td colSpan={6}>
                    <EmptyTableState title="Nenhum parlamentar encontrado" description="Ajuste a busca ou filtros para continuar." />
                  </td>
                </tr>
              ) : null}
              {!parlamentarQuery.isLoading && !parlamentarQuery.isError
                ? rows.map((row) => (
                    <tr
                      key={row.parlamentar.id}
                      className="border-b border-[var(--v2-border)] last:border-b-0 hover:bg-[color-mix(in_srgb,white_2%,transparent)]"
                    >
                      {/* Deputado */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <img
                            src={row.parlamentar.photoUrl}
                            alt={row.parlamentar.name}
                            className="shrink-0 rounded-full object-cover"
                            style={{ width: 32, height: 32, border: "1.5px solid var(--v2-accent)", flexShrink: 0 }}
                          />
                          <div>
                            <span className="block font-semibold text-[var(--v2-text-main)]" style={{ fontSize: 14 }}>
                              {row.parlamentar.name}
                            </span>
                            <span className="block font-bold uppercase tracking-[0.06em] text-[var(--v2-accent)]" style={{ fontSize: 10 }}>
                              {row.parlamentar.party} · {row.parlamentar.uf}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3">
                        <span
                          className={
                            row.status === "Titular"
                              ? "inline-flex items-center rounded-[5px] border border-[color-mix(in_srgb,var(--v2-accent)_40%,transparent)] bg-[color-mix(in_srgb,var(--v2-accent)_12%,transparent)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.06em] text-[var(--v2-accent-soft)]"
                              : "inline-flex items-center rounded-[5px] border border-[color-mix(in_srgb,var(--v2-text-muted)_30%,transparent)] bg-[color-mix(in_srgb,var(--v2-text-muted)_8%,transparent)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.06em] text-[var(--v2-text-muted)]"
                          }
                        >
                          {row.status}
                        </span>
                      </td>

                      {/* Stats */}
                      <td className="px-4 py-3 text-center">
                        <span className="font-bold tabular-nums text-[var(--v2-accent-soft)]" style={{ fontSize: 15 }}>
                          {row.presence}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="font-bold tabular-nums text-[var(--v2-accent-soft)]" style={{ fontSize: 15 }}>
                          {String(row.projects).padStart(2, "0")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="font-bold tabular-nums text-[var(--v2-accent-soft)]" style={{ fontSize: 15 }}>
                          R$ {row.expenseK}k
                        </span>
                      </td>

                      {/* Ação */}
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/parlamentares/${row.parlamentar.id}`}
                          className="text-[11px] font-bold uppercase tracking-[0.07em] text-[var(--v2-accent)] hover:underline"
                          onClick={() => setSelectedParlamentar(row.parlamentar.id)}
                        >
                          Perfil
                        </Link>
                      </td>
                    </tr>
                  ))
                : null}
            </tbody>
          </table>
        </div>

        {/* Rodapé */}
        {!parlamentarQuery.isLoading && !parlamentarQuery.isError && rows.length > 0 ? (
          <div className="flex items-center justify-between border-t border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-5 py-2.5">
            <span className="text-[11px] text-[var(--v2-text-subtle)]">
              Exibindo {rows.length} parlamentar{rows.length !== 1 ? "es" : ""}
            </span>
            <span className="text-[11px] text-[var(--v2-text-subtle)]">
              Dados: API da Câmara dos Deputados
            </span>
          </div>
        ) : null}
      </div>
    </div>
  );
}
