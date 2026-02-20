import { create } from "zustand";
import { createJSONStorage, devtools, persist } from "zustand/middleware";

interface UiState {
  selectedParlamentarId: string | null;
  globalSearchQuery: string;
  shell: {
    sidebarCollapsed: boolean;
  };
  setSelectedParlamentar: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  toggleSidebar: () => void;
}

export const useUiStore = create<UiState>()(
  devtools(
    persist(
      (set) => ({
        selectedParlamentarId: null,
        globalSearchQuery: "",
        shell: {
          sidebarCollapsed: false,
        },
        setSelectedParlamentar: (selectedParlamentarId) => set({ selectedParlamentarId }),
        setSearchQuery: (globalSearchQuery) => set({ globalSearchQuery }),
        toggleSidebar: () =>
          set((state) => ({
            shell: {
              ...state.shell,
              sidebarCollapsed: !state.shell.sidebarCollapsed,
            },
          })),
      }),
      {
        name: "brado-ui-store",
        storage: createJSONStorage(() => localStorage),
      }
    ),
    { name: "ui-store" }
  )
);
