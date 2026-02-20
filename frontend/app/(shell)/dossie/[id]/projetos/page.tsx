"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { getProjectsByParlamentar } from "@/lib/data";
import { useUiStore } from "@/lib/state/ui.store";

import { PageHeaderV2 } from "@/components/layout/page-header-v2";
import { EmptyTableState } from "@/components/states/empty-table-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { GlossyCard } from "@/components/ui/glossy-card";
import { Label } from "@/components/typography/Label";

export default function DossieProjetosPage() {
  const params = useParams<{ id: string }>();
  const setSelectedParlamentar = useUiStore((state) => state.setSelectedParlamentar);

  useEffect(() => {
    setSelectedParlamentar(params.id);
  }, [params.id, setSelectedParlamentar]);

  const projectsQuery = useQuery({
    queryKey: ["projects", params.id],
    queryFn: () => getProjectsByParlamentar(params.id),
  });

  if (projectsQuery.isLoading) return <LoadingState />;
  if (projectsQuery.isError) return <ErrorState message="Falha ao carregar projetos." onRetry={() => projectsQuery.refetch()} />;
  if (!projectsQuery.data?.length) return <EmptyTableState title="Sem projetos vinculados" />;

  const statusClass: Record<string, string> = {
    Aprovado: "border-[var(--v2-border-strong)] bg-[var(--v2-bg-surface-strong)] text-[var(--v2-text-main)]",
    "Em tramitação": "border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] text-[var(--v2-text-muted)]",
    Arquivado: "border-[var(--v2-danger)] bg-[color-mix(in_srgb,var(--v2-danger)_18%,transparent)] text-[var(--v2-danger-soft)]",
  };

  const priorityClass: Record<string, string> = {
    Alta: "border-[var(--v2-border-strong)] bg-[var(--v2-bg-surface-strong)] text-[var(--v2-accent-soft)]",
    "Média": "border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] text-[var(--v2-text-main)]",
    Baixa: "border-[var(--v2-border)] bg-[var(--v2-bg-canvas-deep)] text-[var(--v2-text-muted)]",
  };

  return (
    <div className="v2-content">
      <section className="space-y-6">
        <PageHeaderV2
          kicker="Portfólio Legislativo"
          title="Projetos"
          subtitle="Painel de proposições e tramitação em curso."
        />

        <GlossyCard className="overflow-hidden p-0" hoverLift={false}>
          <div className="v2-card-head">
            <Label className="mb-0">Projetos apresentados</Label>
          </div>
          <div className="grid grid-cols-[1.5fr_220px_220px] border-b border-[var(--v2-border)] px-5 py-3 max-md:hidden">
            <Label>Título e Código</Label>
            <Label>Status</Label>
            <Label>Prioridade</Label>
          </div>

          <div className="divide-y divide-[var(--v2-border)]">
            {projectsQuery.data.map((project) => (
              <article
                key={project.id}
                className="grid grid-cols-[1.5fr_220px_220px] items-center gap-4 px-5 py-4 transition-colors hover:bg-white/[0.015] max-md:grid-cols-1"
              >
                <div className="space-y-2">
                  <p className="text-[15px] font-semibold text-[var(--v2-text-main)]">{project.title}</p>
                  <div className="flex items-center gap-3">
                    <Label>{project.code}</Label>
                    <Label>{new Date(project.updatedAt).toLocaleDateString("pt-BR")}</Label>
                  </div>
                </div>

                <div className="max-md:flex max-md:justify-start">
                  <span
                    className={`inline-flex rounded-[4px] border px-2.5 py-1 font-[var(--font-ui-mono)] text-[10px] uppercase tracking-[0.1em] ${statusClass[project.status]}`}
                  >
                    {project.status}
                  </span>
                </div>

                <div className="max-md:flex max-md:justify-start">
                  <span
                    className={`inline-flex rounded-[4px] border px-2.5 py-1 font-[var(--font-ui-mono)] text-[10px] uppercase tracking-[0.1em] ${priorityClass[project.priority]}`}
                  >
                    Prioridade {project.priority}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </GlossyCard>
      </section>
    </div>
  );
}
