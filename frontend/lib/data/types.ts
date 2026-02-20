export type VoteType = "favor" | "contra";
export type VoteOutcome = "Aprovado" | "Rejeitado" | "Adiado/Abst.";

export interface Parlamentar {
  id: string;
  name: string;
  party: string;
  uf: string;
  monthlyExpense?: number;
  photoUrl?: string;
  role: string;
  bio: string;
  alignment: number;
  controversy: number;
}

export interface Vote {
  id: string;
  parlamentarId: string;
  date: string;
  title: string;
  description: string;
  voteType: VoteType;
  alignedWithParty: boolean;
  controversial: boolean;
  outcome: VoteOutcome;
  topic: string;
  code: string;
  yes?: number;
  no?: number;
  abstention?: number;
  context: string;
  externalUrl?: string;
}

export interface Project {
  id: string;
  parlamentarId: string;
  code: string;
  title: string;
  status: "Em tramitação" | "Aprovado" | "Arquivado";
  priority: "Baixa" | "Média" | "Alta";
  updatedAt: string;
}

export interface Expense {
  id: string;
  parlamentarId: string;
  date: string;
  category: string;
  vendor: string;
  value: number;
  outlier: boolean;
}

export interface VoteFilters {
  q?: string;
}

export interface ParlamentarFilters {
  q?: string;
  uf?: string;
  party?: string;
  sort?: "alignment" | "controversy";
}
