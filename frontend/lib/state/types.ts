import type { AuthMeResponse, InterviewQuestion, InterviewResult } from "@/lib/api/types";

export type Answers = Record<string, number>;

export interface SessionState {
  token: string | null;
  expiresAt: number | null;
  clientId: string | null;
  authMe: AuthMeResponse | null;
  sessionId: string | null;
  answeredCount: number;
  answers: Answers;
  currentQuestion: InterviewQuestion | null;
  lastResult: InterviewResult | null;
  setAuth: (payload: { token: string | null; expiresAt: number | null; clientId: string }) => void;
  setAuthMe: (auth: AuthMeResponse | null) => void;
  setSession: (sessionId: string | null) => void;
  setAnsweredCount: (count: number) => void;
  upsertAnswer: (questionId: string, value: number) => void;
  setCurrentQuestion: (question: InterviewQuestion | null) => void;
  setLastResult: (result: InterviewResult | null) => void;
  clearSessionOnly: () => void;
  resetAll: () => void;
}
