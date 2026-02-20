import { Badge } from "@/components/ui/badge";
import { GlossyCard } from "@/components/ui/glossy-card";
import { Label } from "@/components/typography/Label";

interface TimelineVoteEntryProps {
  date: string;
  outcome: "Aprovado" | "Rejeitado" | "Adiado/Abst.";
  topic: string;
  code: string;
  yes?: number;
  no?: number;
  abstention?: number;
}

export function TimelineVoteEntry({ date, outcome, topic, code, yes, no, abstention }: TimelineVoteEntryProps) {
  const formatted = new Date(date).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="relative pl-7">
      <span className="absolute left-[6px] top-0 h-full w-px bg-[var(--v2-border)]" />
      <span className="absolute left-0 top-5 h-3.5 w-3.5 rounded-full border border-[var(--v2-border-strong)] bg-[var(--v2-bg-canvas)]" />
      <GlossyCard className="p-0" hoverLift={false}>
        <div className="v2-card-head">
          <Label className="mb-0">{formatted}</Label>
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full border border-[var(--v2-border-strong)]" />
            <span className="h-2.5 w-2.5 rounded-full border border-[var(--v2-border-strong)]" />
            <span className="h-2.5 w-2.5 rounded-full border border-[var(--v2-border-strong)]" />
          </div>
        </div>
        <div className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">{outcome}</Badge>
              <Badge variant="secondary">{topic}</Badge>
              <span className="text-sm font-semibold text-[var(--v2-text-main)]">{code}</span>
            </div>
          </div>
          {typeof yes === "number" || typeof no === "number" || typeof abstention === "number" ? (
            <div className="text-xs text-[var(--v2-text-muted)]">SIM {yes ?? 0} | NAO {no ?? 0} | ABS {abstention ?? 0}</div>
          ) : null}
        </div>
      </GlossyCard>
    </div>
  );
}
