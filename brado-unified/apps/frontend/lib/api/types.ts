export interface TokenResponse {
  access_token: string;
  expires_in?: number;
  expires_at?: number;
  token_type?: string;
}

export interface AuthMeResponse {
  subject: string;
  ttl: number;
  [key: string]: unknown;
}

export interface InterviewQuestion {
  id?: string;
  question_id?: string;
  text: string;
  tags?: string[];
  dimensions?: string[];
  [key: string]: unknown;
}

export interface InterviewStartRequest {
  user_id?: string;
}

export interface InterviewStartResponse {
  session_id: string;
  question?: InterviewQuestion | null;
  next_question?: InterviewQuestion | null;
  answered_count?: number;
  [key: string]: unknown;
}

export interface InterviewAnswerRequest {
  answer: number;
  question_id?: string;
}

export interface InterviewAnswerResponse {
  session_id?: string;
  next_question?: InterviewQuestion | null;
  answered_count?: number;
  done?: boolean;
  [key: string]: unknown;
}

export interface RankingItem {
  tipo?: string;
  nome: string;
  sigla?: string;
  similaridade: number;
  explicacao?: string;
  [key: string]: unknown;
}

export interface InterviewResult {
  session_id?: string;
  metricas?: {
    esquerda_direita?: number;
    confianca?: number;
    consistencia?: number;
    [key: string]: unknown;
  };
  vetor?: Record<string, number>;
  ranking?: RankingItem[];
  [key: string]: unknown;
}

export interface BudgetAllocation {
  category: string;
  percent: number;
}

export interface BudgetSimulationRequest {
  allocations: BudgetAllocation[];
}

export interface BudgetSimulationResponse {
  valid: boolean;
  total_percent: number;
  tradeoffs: string[];
  [key: string]: unknown;
}

export interface PropositionItem {
  id?: string | number;
  title?: string;
  summary?: string;
  kind?: string;
  sigla?: string;
  [key: string]: unknown;
}

export interface PropositionsResponse {
  items: PropositionItem[];
  [key: string]: unknown;
}

export interface ApiErrorBody {
  detail?: unknown;
  message?: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  public status: number;
  public technical?: unknown;

  constructor(message: string, status: number, technical?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.technical = technical;
  }
}
