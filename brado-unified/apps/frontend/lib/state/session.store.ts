import { create } from "zustand";
import { createJSONStorage, devtools, persist } from "zustand/middleware";

import type { SessionState } from "./types";

export const useSessionStore = create<SessionState>()(
  devtools(
    persist(
      (set) => ({
        token: null,
        expiresAt: null,
        clientId: null,
        authMe: null,
        sessionId: null,
        answeredCount: 0,
        answers: {},
        currentQuestion: null,
        lastResult: null,
        setAuth: ({ token, expiresAt, clientId }) => set({ token, expiresAt, clientId }),
        setAuthMe: (authMe) => set({ authMe }),
        setSession: (sessionId) => set({ sessionId }),
        setAnsweredCount: (answeredCount) => set({ answeredCount }),
        upsertAnswer: (questionId, value) =>
          set((state) => ({
            answers: {
              ...state.answers,
              [questionId]: value,
            },
          })),
        setCurrentQuestion: (currentQuestion) => set({ currentQuestion }),
        setLastResult: (lastResult) => set({ lastResult }),
        clearSessionOnly: () =>
          set({
            sessionId: null,
            answeredCount: 0,
            answers: {},
            currentQuestion: null,
            lastResult: null,
          }),
        resetAll: () =>
          set({
            token: null,
            expiresAt: null,
            clientId: null,
            authMe: null,
            sessionId: null,
            answeredCount: 0,
            answers: {},
            currentQuestion: null,
            lastResult: null,
          }),
      }),
      {
        name: "brado-session-store",
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          token: state.token,
          expiresAt: state.expiresAt,
          clientId: state.clientId,
          sessionId: state.sessionId,
          answeredCount: state.answeredCount,
          answers: state.answers,
        }),
      }
    ),
    { name: "session-store" }
  )
);
