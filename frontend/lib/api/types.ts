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

export interface DeputadoNormalizado {
  id: number;
  uri?: string | null;
  nome_civil?: string | null;
  cpf?: string | null;
  sexo?: string | null;
  url_website?: string | null;
  rede_social?: string[];
  data_nascimento?: string | null;
  data_falecimento?: string | null;
  uf_nascimento?: string | null;
  municipio_nascimento?: string | null;
  escolaridade?: string | null;
  status_nome?: string | null;
  status_nome_eleitoral?: string | null;
  status_sigla_partido?: string | null;
  status_sigla_uf?: string | null;
  status_id_legislatura?: number | null;
  status_situacao?: string | null;
  status_condicao_eleitoral?: string | null;
  status_data?: string | null;
  status_email?: string | null;
  foto_url?: string | null;
  foto_sha256?: string | null;
  foto_content_type?: string | null;
  gabinete_nome?: string | null;
  gabinete_predio?: string | null;
  gabinete_sala?: string | null;
  gabinete_andar?: string | null;
  gabinete_telefone?: string | null;
  gabinete_email?: string | null;
  atualizado_em?: number | null;
}

export interface DeputadoDespesaResumo {
  id: number;
  latest_year: number;
  latest_month: number;
  latest_total_liquido: number;
  avg_last_3_months_liquido: number;
  months_considered: number;
}

export interface DeputadoDespesaItem {
  id: number;
  deputado_id: number;
  ano: number;
  mes: number;
  data_documento?: string | null;
  tipo_despesa?: string | null;
  nome_fornecedor?: string | null;
  cnpj_cpf_fornecedor?: string | null;
  cod_lote?: number | null;
  cod_documento?: string | null;
  parcela?: number | null;
  tipo_documento?: string | null;
  num_documento?: string | null;
  num_ressarcimento?: string | null;
  valor_documento?: number | null;
  valor_glosa?: number | null;
  valor_liquido?: number | null;
  url_documento?: string | null;
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
