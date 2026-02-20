"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, BarChart3, ExternalLink, FileSpreadsheet, Globe, Mail, MapPin, Phone, Vote } from "lucide-react";

import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { getDeputadoNormalizadoById } from "@/lib/data";

type TabKey = "resumo" | "gabinete" | "pessoal" | "redes";

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="block text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--v2-text-subtle)]">{label}</span>
      <span className="mt-0.5 block text-sm font-medium text-[var(--v2-text-main)]">{value || "-"}</span>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-[10px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)] p-4">
      <span className={`block text-2xl font-bold ${accent ? "text-[var(--v2-accent)]" : "text-[var(--v2-text-main)]"}`}>{value}</span>
      <span className="mt-1 block text-[11px] uppercase tracking-[0.07em] text-[var(--v2-text-subtle)]">{label}</span>
    </div>
  );
}

function ActionButton({ href, icon: Icon, label, external }: { href: string; icon: React.FC<{ className?: string }>; label: string; external?: boolean }) {
  const cls = "flex items-center gap-2 rounded-[8px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)] px-3 py-2.5 text-xs font-semibold text-[var(--v2-text-muted)] transition-colors hover:border-[var(--v2-accent)] hover:text-[var(--v2-accent)]";
  if (external) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={cls}>
        <Icon className="h-3.5 w-3.5 shrink-0" />
        <span className="truncate">{label}</span>
      </a>
    );
  }
  return (
    <Link href={href} className={cls}>
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">{label}</span>
    </Link>
  );
}

function InfoRow({
  label,
  value,
  link,
  icon,
}: {
  label: string;
  value?: string | null;
  link?: boolean;
  icon?: React.ReactNode;
}) {
  const display = value || "-";
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[var(--v2-border)] pb-3 last:border-b-0 last:pb-0">
      <span className="shrink-0 text-sm text-[var(--v2-text-muted)]">{label}</span>
      {link && value ? (
        <a
          href={value}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 break-all text-right text-sm text-[var(--v2-accent)] hover:underline"
        >
          {icon}
          {display}
        </a>
      ) : (
        <span className="flex items-center gap-1 break-words text-right text-sm text-[var(--v2-text-main)]">
          {icon}
          {display}
        </span>
      )}
    </div>
  );
}

export default function ParlamentarPerfilPage() {
  const params = useParams<{ id: string }>();
  const deputadoId = useMemo(() => Number(params?.id ?? 0), [params]);
  const [tab, setTab] = useState<TabKey>("resumo");

  const perfilQuery = useQuery({
    queryKey: ["deputado-normalizado", deputadoId],
    queryFn: () => getDeputadoNormalizadoById(deputadoId),
    enabled: Number.isFinite(deputadoId) && deputadoId > 0,
  });

  const perfil = perfilQuery.data;
  const profileName = perfil?.status_nome ?? perfil?.nome_civil ?? `Deputado #${deputadoId}`;
  const electoralName = perfil?.status_nome_eleitoral ?? profileName;
  const party = perfil?.status_sigla_partido ?? "-";
  const uf = perfil?.status_sigla_uf ?? "-";
  const situation = perfil?.status_situacao ?? "-";
  const legislature = String(perfil?.status_id_legislatura ?? "-");
  const condition = perfil?.status_condicao_eleitoral ?? "-";
  const updatedAt = perfil?.atualizado_em ? new Date(perfil.atualizado_em * 1000).toLocaleDateString("pt-BR") : "-";
  const photoUrl = perfil?.foto_url ?? `https://www.camara.leg.br/internet/deputado/bandep/${deputadoId}.jpg`;

  const tabs: { id: TabKey; label: string }[] = [
    { id: "resumo", label: "Visão Geral" },
    { id: "gabinete", label: "Gabinete" },
    { id: "pessoal", label: "Pessoal" },
    { id: "redes", label: "Redes" },
  ];

  if (perfilQuery.isLoading) {
    return (
      <div className="v2-content">
        <LoadingState />
      </div>
    );
  }

  if (perfilQuery.isError) {
    return (
      <div className="v2-content">
        <ErrorState message="Não foi possível carregar o perfil." onRetry={() => perfilQuery.refetch()} />
      </div>
    );
  }

  return (
    <div className="v2-content">
      {/* Back breadcrumb */}
      <div className="flex items-center gap-2">
        <Link
          href="/parlamentares"
          className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.08em] text-[var(--v2-text-subtle)] transition-colors hover:text-[var(--v2-accent)]"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Parlamentares
        </Link>
        <span className="text-[var(--v2-border-strong)]">/</span>
        <span className="truncate text-xs font-semibold uppercase tracking-[0.08em] text-[var(--v2-text-muted)]">{electoralName}</span>
      </div>

      {/* Main grid: left profile card + right content */}
      <div className="grid gap-5 xl:grid-cols-[300px_1fr]">

        {/* ── Left: profile card ── */}
        <div className="flex flex-col gap-4">

          {/* Photo + identity */}
          <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)]">
            {/* Photo */}
            <div className="relative aspect-[4/3] w-full overflow-hidden bg-[var(--v2-bg-canvas-deep)]">
              <img
                src={photoUrl}
                alt={electoralName}
                className="h-full w-full object-cover object-top"
                style={{ filter: "grayscale(30%) brightness(0.9) contrast(1.08)" }}
              />
              <div className="absolute bottom-2 right-2 rounded-[6px] border border-[color-mix(in_srgb,var(--v2-accent)_60%,transparent)] bg-[color-mix(in_srgb,var(--v2-bg-canvas-deep)_80%,transparent)] px-2.5 py-1 backdrop-blur-sm">
                <span className="font-bold tracking-[0.1em] text-[var(--v2-accent)]" style={{ fontSize: 11 }}>{party} — {uf}</span>
              </div>
            </div>

            {/* Name + meta */}
            <div className="bg-[var(--v2-bg-surface)] p-5">
              <h1 className="text-[22px] font-bold leading-[1.1] tracking-[-0.02em] text-[var(--v2-text-main)]">
                {electoralName}
              </h1>
              <p className="mt-1 text-sm font-medium text-[var(--v2-accent-soft)]">
                Deputado Federal · {uf}
              </p>

              <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-dotted border-[var(--v2-border)] pt-4">
                <MetaItem label="Situação" value={situation} />
                <MetaItem label="Condição" value={condition} />
                <MetaItem label="Legislatura" value={legislature} />
                <MetaItem label="Atualizado" value={updatedAt} />
              </div>
            </div>
          </div>

          {/* Status indicator */}
          <div className="flex items-center gap-2.5 rounded-[8px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)] px-4 py-3">
            <span
              className={`h-2 w-2 shrink-0 rounded-full ${situation === "Exercício" ? "bg-[var(--v2-ok)]" : "bg-[var(--v2-text-subtle)]"}`}
            />
            <span className="text-sm font-medium text-[var(--v2-text-muted)]">
              {situation === "Exercício" ? "Em exercício" : situation}
            </span>
          </div>

          {/* Dossiê quick links */}
          <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
            <div className="border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-4 py-2.5">
              <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">Dossiê analítico</span>
            </div>
            <div className="flex flex-col gap-1.5 p-3">
              <ActionButton href={`/dossie/${deputadoId}/votos`} icon={Vote} label="Votos e posicionamentos" />
              <ActionButton href={`/dossie/${deputadoId}/gastos`} icon={BarChart3} label="Gastos CEAP detalhados" />
              <ActionButton href={`/dossie/${deputadoId}/projetos`} icon={FileSpreadsheet} label="Projetos de lei" />
            </div>
          </div>

          {/* External links */}
          {(perfil?.uri || perfil?.url_website || perfil?.status_email) ? (
            <div className="overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
              <div className="border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)] px-4 py-2.5">
                <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--v2-text-subtle)]">Links externos</span>
              </div>
              <div className="flex flex-col gap-1.5 p-3">
                {perfil?.uri ? (
                  <ActionButton href={perfil.uri} icon={ExternalLink} label="Página na Câmara" external />
                ) : null}
                {perfil?.url_website ? (
                  <ActionButton href={perfil.url_website} icon={Globe} label="Site oficial" external />
                ) : null}
                {perfil?.status_email ? (
                  <ActionButton href={`mailto:${perfil.status_email}`} icon={Mail} label={perfil.status_email} external />
                ) : null}
              </div>
            </div>
          ) : null}
        </div>

        {/* ── Right: stats + tabs ── */}
        <div className="flex flex-col gap-5">

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard label="Legislatura" value={legislature} accent />
            <StatCard label="Partido" value={party} accent />
            <StatCard label="Estado" value={uf} />
            <StatCard label="Condição" value={condition} />
          </div>

          {/* Tabbed detail section */}
          <div className="flex-1 overflow-hidden rounded-[12px] border border-[var(--v2-border)] bg-[var(--v2-bg-surface)]">
            {/* Tab bar */}
            <div className="flex overflow-x-auto border-b border-[var(--v2-border)] bg-[var(--v2-bg-surface-muted)]">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTab(t.id)}
                  className={
                    tab === t.id
                      ? "shrink-0 border-b-[2px] border-[var(--v2-accent)] px-5 py-3 text-sm font-semibold text-[var(--v2-text-main)] transition-colors"
                      : "shrink-0 border-b-[2px] border-transparent px-5 py-3 text-sm font-semibold text-[var(--v2-text-muted)] transition-colors hover:text-[var(--v2-text-main)]"
                  }
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="p-5">
              {tab === "resumo" ? (
                <div className="space-y-3">
                  <InfoRow label="Nome civil" value={perfil?.nome_civil} />
                  <InfoRow label="Nome eleitoral" value={perfil?.status_nome_eleitoral} />
                  <InfoRow label="Email parlamentar" value={perfil?.status_email} icon={<Mail className="h-3 w-3" />} />
                  <InfoRow label="Status" value={perfil?.status_situacao} />
                  <InfoRow label="Data de status" value={perfil?.status_data} />
                  <InfoRow label="URI Câmara" value={perfil?.uri} link />
                </div>
              ) : null}

              {tab === "gabinete" ? (
                <div className="space-y-3">
                  <InfoRow label="Gabinete" value={perfil?.gabinete_nome} />
                  <InfoRow label="Prédio" value={perfil?.gabinete_predio} />
                  <InfoRow label="Sala / Andar" value={`${perfil?.gabinete_sala ?? "-"} / ${perfil?.gabinete_andar ?? "-"}`} />
                  <InfoRow label="Telefone" value={perfil?.gabinete_telefone} icon={<Phone className="h-3 w-3" />} />
                  <InfoRow label="Email" value={perfil?.gabinete_email} icon={<Mail className="h-3 w-3" />} />
                  <InfoRow label="Website" value={perfil?.url_website} link icon={<Globe className="h-3 w-3" />} />
                </div>
              ) : null}

              {tab === "pessoal" ? (
                <div className="space-y-3">
                  <InfoRow label="Sexo" value={perfil?.sexo} />
                  <InfoRow label="Data de nascimento" value={perfil?.data_nascimento} />
                  <InfoRow
                    label="Naturalidade"
                    value={`${perfil?.municipio_nascimento ?? "-"} — ${perfil?.uf_nascimento ?? "-"}`}
                    icon={<MapPin className="h-3 w-3" />}
                  />
                  <InfoRow label="Escolaridade" value={perfil?.escolaridade} />
                  {perfil?.data_falecimento ? <InfoRow label="Falecimento" value={perfil.data_falecimento} /> : null}
                </div>
              ) : null}

              {tab === "redes" ? (
                <div className="space-y-3">
                  {(perfil?.rede_social ?? []).length === 0 ? (
                    <p className="text-sm text-[var(--v2-text-muted)]">Nenhuma rede social registrada.</p>
                  ) : (
                    (perfil?.rede_social ?? []).map((url) => (
                      <a
                        key={url}
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 rounded-[8px] border border-[var(--v2-border)] px-4 py-3 text-sm text-[var(--v2-text-main)] transition-colors hover:border-[var(--v2-accent)] hover:text-[var(--v2-accent)]"
                      >
                        <ExternalLink className="h-3.5 w-3.5 shrink-0 text-[var(--v2-text-subtle)]" />
                        <span className="break-all">{url}</span>
                      </a>
                    ))
                  )}
                  {perfil?.foto_sha256 ? (
                    <div className="mt-4 rounded-[8px] border border-[var(--v2-border)] bg-[var(--v2-bg-canvas-deep)] px-4 py-3">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--v2-text-subtle)]">Hash da foto</p>
                      <p className="mt-1 break-all font-mono text-xs text-[var(--v2-text-muted)]">{perfil.foto_sha256}</p>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
