import Link from "next/link";

import { PageHeaderV2 } from "@/components/layout/page-header-v2";
import { Button } from "@/components/ui/button";
import { GlossyCard } from "@/components/ui/glossy-card";

export function EmptyDossieState({ parlamentarId }: { parlamentarId?: string }) {
  return (
    <div className="v2-content">
      <GlossyCard className="space-y-6 p-8" hoverLift={false}>
        <PageHeaderV2
          kicker="Dossiê"
          title="Dossiê não inicializado"
          subtitle="Não há atividade consolidada para exibir neste parlamentar."
        />
        <Button asChild>
          <Link href={parlamentarId ? `/dossie/${parlamentarId}/votos` : "/parlamentares"}>Começar Integração de Dados</Link>
        </Button>
      </GlossyCard>
    </div>
  );
}
