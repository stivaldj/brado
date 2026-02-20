import { Label } from "@/components/typography/Label";
import { GlossyCard } from "@/components/ui/glossy-card";

export function EmptyTableState({ title = "Sem resultados", description = "Ajuste os filtros para continuar." }: { title?: string; description?: string }) {
  return (
    <GlossyCard className="p-8 text-center" hoverLift={false}>
      <Label className="mb-2">Estado vazio</Label>
      <p className="text-lg font-semibold text-[var(--v2-text-main)]">{title}</p>
      <p className="mt-2 text-sm text-[var(--v2-text-muted)]">{description}</p>
    </GlossyCard>
  );
}
