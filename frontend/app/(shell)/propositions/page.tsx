"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";

import { getPropositions } from "@/lib/data";

import { PageHeaderV2 } from "@/components/layout/page-header-v2";
import { EmptyTableState } from "@/components/states/empty-table-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Button } from "@/components/ui/button";
import { GlossyCard } from "@/components/ui/glossy-card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function PropositionsPage() {
  const router = useRouter();
  const pathname = usePathname();
  const [limit, setLimit] = React.useState(20);
  const [query, setQuery] = React.useState("");

  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setQuery(params.get("q") ?? "");
  }, []);

  React.useEffect(() => {
    const next = new URLSearchParams();
    if (query.trim()) next.set("q", query.trim());
    const encoded = next.toString();
    router.replace(encoded ? `${pathname}?${encoded}` : pathname, { scroll: false });
  }, [pathname, query, router]);

  const propositionsQuery = useQuery({
    queryKey: ["propositions", limit],
    queryFn: () => getPropositions(limit),
  });

  const items = propositionsQuery.data?.items ?? [];
  const filtered = items.filter((item) => JSON.stringify(item).toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="v2-content">
      <section className="space-y-6">
        <PageHeaderV2
          kicker="Tramitação"
          title="Proposições"
          subtitle="Busca, inspeção e acompanhamento de itens legislativos."
          rightSlot={
            <div className="flex items-center gap-2">
              <Input value={String(limit)} onChange={(event) => setLimit(Number(event.target.value) || 20)} className="w-20" aria-label="Limite" />
              <Button variant="outline" onClick={() => propositionsQuery.refetch()}>Atualizar</Button>
            </div>
          }
        />

        <GlossyCard className="p-0" hoverLift={false}>
          <div className="v2-card-head">
            <span className="v2-card-kicker">Busca textual</span>
          </div>
          <div className="p-4">
            <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por texto ou sigla" aria-label="Buscar proposições" />
          </div>
        </GlossyCard>

        {propositionsQuery.isLoading ? <LoadingState /> : null}
        {propositionsQuery.isError ? <ErrorState message={(propositionsQuery.error as Error).message} onRetry={() => propositionsQuery.refetch()} /> : null}
        {!propositionsQuery.isLoading && !propositionsQuery.isError && filtered.length === 0 ? <EmptyTableState /> : null}

        {!propositionsQuery.isLoading && !propositionsQuery.isError && filtered.length ? (
          <GlossyCard className="p-0" hoverLift={false}>
            <div className="v2-card-head">
              <span className="v2-card-kicker">{filtered.length} itens encontrados</span>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Título</TableHead>
                  <TableHead>Sigla</TableHead>
                  <TableHead>Resumo</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((item, index) => (
                  <TableRow key={String(item.id ?? index)}>
                    <TableCell>{String(item.id ?? "-")}</TableCell>
                    <TableCell>{item.title ?? "-"}</TableCell>
                    <TableCell>{item.sigla ?? "-"}</TableCell>
                    <TableCell>{item.summary ?? "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </GlossyCard>
        ) : null}
      </section>
    </div>
  );
}
