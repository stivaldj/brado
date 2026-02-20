import { Badge } from "@/components/ui/badge";
import { GlossyCard } from "@/components/ui/glossy-card";
import { Label } from "@/components/typography/Label";
import { cn } from "@/lib/utils";

interface VoteCardProps {
  date: string;
  title: string;
  description: string;
  voteType: "favor" | "contra";
  alignedWithParty: boolean;
  controversial: boolean;
  onClick?: () => void;
}

export function VoteCard({ date, title, description, voteType, alignedWithParty, controversial, onClick }: VoteCardProps) {
  const parsed = new Date(date);
  const DateLabel = parsed.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <GlossyCard
      className={cn("flex h-full min-h-[300px] cursor-pointer flex-col p-0", controversial && "border-[var(--v2-danger)]")}
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(event) => {
        if ((event.key === "Enter" || event.key === " ") && onClick) {
          event.preventDefault();
          onClick();
        }
      }}
    >
      <div className="v2-card-head">
        <div className="flex items-center justify-between gap-2">
          <Label className="mb-0 text-[10px]">{DateLabel}</Label>
          <div className="flex items-center gap-2">
            {controversial ? (
              <span className="rounded-[4px] border border-[var(--v2-danger)] bg-[color-mix(in_srgb,var(--v2-danger)_18%,transparent)] px-1.5 py-0.5 text-[9px] uppercase tracking-[0.1em] text-[var(--v2-danger-soft)]">
                Controverso
              </span>
            ) : null}
            <span className="h-2.5 w-2.5 rounded-full border border-[var(--v2-border-strong)]" />
            <span className="h-2.5 w-2.5 rounded-full border border-[var(--v2-border-strong)]" />
            <span className="h-2.5 w-2.5 rounded-full border border-[var(--v2-border-strong)]" />
          </div>
        </div>
      </div>

      <div className="flex flex-1 flex-col p-5">
        <h3 className="text-[1.02rem] font-semibold leading-[1.35] text-[var(--v2-text-main)]">{title}</h3>
        <p className="mt-3 flex-1 text-[0.83rem] leading-[1.55] text-[var(--v2-text-muted)]">{description}</p>

        <footer className="mt-5 flex items-center justify-between border-t border-[var(--v2-border)] pt-4">
          <div className="flex items-center gap-3">
            <Label className="mb-0 text-[10px]">Voto:</Label>
            <Badge
              className={cn(
                "rounded-[4px] px-2.5 py-1 text-[10px]",
                voteType === "favor"
                  ? "border-[var(--v2-accent)] bg-[color-mix(in_srgb,var(--v2-accent)_20%,transparent)] text-[var(--v2-text-main)]"
                  : "border-[var(--v2-border)] bg-transparent text-[var(--v2-text-muted)]"
              )}
            >
              {voteType === "favor" ? "Favorável" : "Contrário"}
            </Badge>
          </div>
          <span className={cn("mono-label text-[10px] tracking-[0.1em]", alignedWithParty ? "text-[var(--v2-text-muted)]" : "text-[var(--v2-accent-soft)]")}>
            {alignedWithParty ? "ALINHADO" : "DIVERGENTE"}
          </span>
        </footer>
      </div>
    </GlossyCard>
  );
}
