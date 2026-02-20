"use client";

import { create } from "zustand";

export type ToastVariant = "default" | "destructive";

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
}

interface ToastState {
  toasts: ToastItem[];
  toast: (input: Omit<ToastItem, "id">) => string;
  dismiss: (id: string) => void;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  toast: (input) => {
    const id = crypto.randomUUID();
    set((state) => ({
      toasts: [...state.toasts, { ...input, id }],
    }));

    window.setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((item) => item.id !== id),
      }));
    }, 4000);

    return id;
  },
  dismiss: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((item) => item.id !== id),
    }));
  },
}));

export function useToast() {
  const toast = useToastStore((state) => state.toast);
  const dismiss = useToastStore((state) => state.dismiss);
  return { toast, dismiss };
}
