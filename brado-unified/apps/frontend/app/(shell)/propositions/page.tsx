"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { PropositionItem } from "@/lib/api/types";

import { ApiErrorNotice } from "@/components/api-error-notice";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/components/ui/use-toast";

const pageSize = 5;

function getText(item: PropositionItem) {
  return item.title ?? item.summary ?? JSON.stringify(item).slice(0, 120);
}

export default function PropositionsPage() {
  const { toast } = useToast();
  const [limit, setLimit] = React.useState(20);
  const [query, setQuery] = React.useState("");
  const [page, setPage] = React.useState(1);

  const propositionsQuery = useQuery({
    queryKey: ["propositions", limit],
    queryFn: () => apiClient.legislative.propositions(limit),
  });

  const items = propositionsQuery.data?.items ?? [];
  const filtered = items.filter((item) => JSON.stringify(item).toLowerCase().includes(query.toLowerCase()));

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const start = (page - 1) * pageSize;
  const pageItems = filtered.slice(start, start + pageSize);

  React.useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Proposições</h1>
          <p className="text-sm text-muted-foreground">Busca rápida, paginação local e inspeção RAW JSON.</p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            min={1}
            max={200}
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value) || 20)}
            className="w-24"
            aria-label="Limite"
          />
          <Button
            variant="outline"
            onClick={() => {
              propositionsQuery.refetch();
              toast({ title: "Proposições atualizadas" });
            }}
            disabled={propositionsQuery.isFetching}
          >
            {propositionsQuery.isFetching ? "Atualizando..." : "Atualizar"}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Busca</CardTitle>
          <CardDescription>Use filtro textual para reduzir a lista.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Command>
            <CommandInput placeholder="Buscar por texto ou sigla..." />
            <CommandList>
              <CommandEmpty>Nenhuma sugestão.</CommandEmpty>
              <CommandGroup heading="Sugestões">
                {items.slice(0, 20).map((item, index) => (
                  <CommandItem
                    key={String(item.id ?? index)}
                    value={getText(item)}
                    keywords={[item.sigla ?? "", item.kind ?? ""]}
                    onSelect={(value) => setQuery(value)}
                  >
                    {getText(item)}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>

          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filtro ativo" aria-label="Filtro" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lista</CardTitle>
          <CardDescription>
            {filtered.length} item(ns) após filtro · página {page} de {totalPages}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Título</TableHead>
                <TableHead>Sigla</TableHead>
                <TableHead>Ação</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pageItems.length ? (
                pageItems.map((item, index) => (
                  <TableRow key={String(item.id ?? `${index}-${getText(item)}`)}>
                    <TableCell>{String(item.id ?? "-")}</TableCell>
                    <TableCell>{getText(item)}</TableCell>
                    <TableCell>{item.sigla ?? "-"}</TableCell>
                    <TableCell>
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm">
                            Ver RAW
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Proposição</DialogTitle>
                            <DialogDescription>{getText(item)}</DialogDescription>
                          </DialogHeader>
                          <pre className="max-h-[420px] overflow-auto rounded-md border bg-muted/20 p-3 text-xs">
                            {JSON.stringify(item, null, 2)}
                          </pre>
                          <DialogClose asChild>
                            <Button className="mt-3" variant="outline">
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
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    Sem itens para exibir.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <div className="mt-4 flex items-center justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage((prev) => Math.max(1, prev - 1))} disabled={page <= 1}>
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={page >= totalPages}
            >
              Próxima
            </Button>
          </div>
        </CardContent>
      </Card>

      <ApiErrorNotice error={propositionsQuery.error as Error | null} />
    </section>
  );
}
