import { GlossyCard } from "@/components/ui/glossy-card";
import { Skeleton } from "@/components/ui/skeleton";

export function LoadingState() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {Array.from({ length: 4 }).map((_, index) => (
        <GlossyCard key={index} className="p-6" hoverLift={false}>
          <Skeleton className="h-4 w-32" />
          <Skeleton className="mt-4 h-6 w-2/3" />
          <Skeleton className="mt-2 h-4 w-full" />
          <Skeleton className="mt-2 h-4 w-4/5" />
          <Skeleton className="mt-6 h-8 w-36" />
        </GlossyCard>
      ))}
    </div>
  );
}
