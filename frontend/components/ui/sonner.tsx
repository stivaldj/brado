"use client";

import { X } from "lucide-react";

import { cn } from "@/lib/utils";

import { Button } from "./button";
import { useToastStore } from "./use-toast";

export function Toaster() {
  const toasts = useToastStore((state) => state.toasts);
  const dismiss = useToastStore((state) => state.dismiss);

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-[360px] max-w-[90vw] flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "pointer-events-auto rounded-lg border bg-card p-3 shadow-md",
            toast.variant === "destructive" && "border-destructive/40 bg-destructive/10"
          )}
          role="status"
          aria-live="polite"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">{toast.title}</p>
              {toast.description ? (
                <p className="mt-1 text-xs text-muted-foreground">{toast.description}</p>
              ) : null}
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={() => dismiss(toast.id)}
              aria-label="Fechar notificação"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
