"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface DialogContextValue {
  open: boolean;
  setOpen: (next: boolean) => void;
}

const DialogContext = React.createContext<DialogContextValue | null>(null);

function useDialogContext() {
  const ctx = React.useContext(DialogContext);
  if (!ctx) {
    throw new Error("Dialog components must be used within Dialog");
  }
  return ctx;
}

export function Dialog({
  open,
  onOpenChange,
  children,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}) {
  const [internalOpen, setInternalOpen] = React.useState(false);
  const controlled = typeof open === "boolean";
  const currentOpen = controlled ? open : internalOpen;

  const setOpen = React.useCallback(
    (next: boolean) => {
      if (!controlled) {
        setInternalOpen(next);
      }
      onOpenChange?.(next);
    },
    [controlled, onOpenChange]
  );

  return <DialogContext.Provider value={{ open: currentOpen, setOpen }}>{children}</DialogContext.Provider>;
}

export function DialogTrigger({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) {
  const { setOpen } = useDialogContext();

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<any>, {
      onClick: (event: React.MouseEvent) => {
        (children as React.ReactElement<any>).props?.onClick?.(event);
        setOpen(true);
      },
    });
  }

  return (
    <button type="button" onClick={() => setOpen(true)}>
      {children}
    </button>
  );
}

export function DialogContent({ className, children }: { className?: string; children: React.ReactNode }) {
  const { open, setOpen } = useDialogContext();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setOpen(false)}>
      <div
        className={cn("w-full max-w-2xl rounded-xl border bg-background p-6 shadow-xl", className)}
        onClick={(event) => event.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}

export function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col space-y-1.5", className)} {...props} />;
}

export function DialogTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn("text-lg font-semibold", className)} {...props} />;
}

export function DialogDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm text-muted-foreground", className)} {...props} />;
}

export function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mt-4 flex justify-end", className)} {...props} />;
}

export function DialogClose({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) {
  const { setOpen } = useDialogContext();

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<any>, {
      onClick: (event: React.MouseEvent) => {
        (children as React.ReactElement<any>).props?.onClick?.(event);
        setOpen(false);
      },
    });
  }

  return (
    <button type="button" onClick={() => setOpen(false)}>
      {children}
    </button>
  );
}
