import { Badge } from "@/components/ui/badge";
import { GlossyCard } from "@/components/ui/glossy-card";
import type { Parlamentar } from "@/lib/data/types";

interface ParlamentarCardProps {
  parlamentar: Parlamentar;
  onClick?: () => void;
}

function getFallbackPhotoUrl(id: string, name: string) {
  if (/^\d+$/.test(id)) {
    return `https://www.camara.leg.br/internet/deputado/bandep/${id}.jpg`;
  }
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=453930&color=FFF8F0&size=128&bold=true`;
}

export function ParlamentarCard({ parlamentar, onClick }: ParlamentarCardProps) {
  const imageUrl = parlamentar.photoUrl ?? getFallbackPhotoUrl(parlamentar.id, parlamentar.name);

  return (
    <GlossyCard
      className="cursor-pointer p-0"
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
        <div className="flex items-center justify-between gap-3">
          <span className="v2-card-kicker">Perfil</span>
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full border border-[var(--v2-border-strong)]" />
            <span className="h-2.5 w-2.5 rounded-full border border-[var(--v2-border-strong)]" />
            <span className="h-2.5 w-2.5 rounded-full border border-[var(--v2-border-strong)]" />
          </div>
        </div>
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <img
              src={imageUrl}
              alt={`Foto de ${parlamentar.name}`}
              className="h-11 w-11 rounded-[10px] border border-[var(--v2-border-strong)] object-cover"
            />
            <div>
              <p className="text-[15px] font-semibold text-[var(--v2-text-main)]">{parlamentar.name}</p>
              <p className="text-xs uppercase tracking-[0.09em] text-[var(--v2-text-muted)]">{parlamentar.role}</p>
            </div>
          </div>
          <Badge variant="outline">{parlamentar.party}</Badge>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 border-t border-[var(--v2-border)] pt-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.1em] text-[var(--v2-text-subtle)]">UF</p>
            <p className="mt-1 text-sm text-[var(--v2-text-main)]">{parlamentar.uf}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.1em] text-[var(--v2-text-subtle)]">Polêmica</p>
            <p className="mt-1 text-sm text-[var(--v2-text-main)]">{parlamentar.controversy}</p>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between border-t border-[var(--v2-border)] pt-3 text-sm">
          <span className="text-[var(--v2-text-muted)]">Alinhamento</span>
          <strong className="rounded-[6px] border border-[var(--v2-border-strong)] bg-[var(--v2-bg-surface-muted)] px-2.5 py-1 text-[var(--v2-accent-soft)]">
            {parlamentar.alignment}%
          </strong>
        </div>
      </div>
    </GlossyCard>
  );
}
