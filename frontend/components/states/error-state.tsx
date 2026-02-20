import { AlertTriangle } from "lucide-react";

import { Label } from "@/components/typography/Label";
import { Button } from "@/components/ui/button";
import { GlossyCard } from "@/components/ui/glossy-card";

export function ErrorState({ message = "Ocorreu uma falha ao carregar os dados.", onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <GlossyCard className="p-8" hoverLift={false}>
      <Label className="mb-2">Erro</Label>
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 text-[var(--v2-danger-soft)]" />
        <div>
          <p className="font-semibold text-[var(--v2-text-main)]">Falha de carregamento</p>
          <p className="mt-1 text-sm text-[var(--v2-text-muted)]">{message}</p>
          {onRetry ? (
            <Button type="button" onClick={onRetry} variant="outline" className="mt-4">
              Tentar novamente
            </Button>
          ) : null}
        </div>
      </div>
    </GlossyCard>
  );
}
