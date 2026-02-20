"use client";

import Link from "next/link";

import { useUiStore } from "@/lib/state/ui.store";

import { Button } from "@/components/ui/button";
import { PageHeaderV2 } from "@/components/layout/page-header-v2";
import { GlossyCard } from "@/components/ui/glossy-card";

export default function HomePage() {
  const selectedParlamentarId = useUiStore((state) => state.selectedParlamentarId);
  const href = selectedParlamentarId ? `/dossie/${selectedParlamentarId}/votos` : "/parlamentares";

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <GlossyCard className="w-full max-w-2xl p-10" hoverLift={false}>
        <PageHeaderV2
          kicker="Manifesto"
          title="Painel Analítico Legislativo"
          subtitle="Análise de votos, proposições e perfil político com visual unificado."
        />
        <Button asChild size="lg">
          <Link href={href}>Entrar no painel</Link>
        </Button>
      </GlossyCard>
    </main>
  );
}
