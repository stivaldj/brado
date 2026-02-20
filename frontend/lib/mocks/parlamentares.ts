import type { Parlamentar } from "@/lib/data/types";

export const parlamentaresMock: Parlamentar[] = [
  { id: "mendes", name: "João Mendes", party: "PL", uf: "SP", role: "Deputado Federal", bio: "Atuação em pauta fiscal e segurança.", alignment: 82, controversy: 41 },
  { id: "tavares", name: "Carla Tavares", party: "PSB", uf: "PE", role: "Deputada Federal", bio: "Foco em educação e assistência social.", alignment: 71, controversy: 23 },
  { id: "araujo", name: "Rafael Araújo", party: "MDB", uf: "MG", role: "Deputado Federal", bio: "Comissões de infraestrutura e energia.", alignment: 65, controversy: 38 },
  { id: "ferraz", name: "Lia Ferraz", party: "PT", uf: "BA", role: "Deputada Federal", bio: "Defesa de políticas públicas de saúde.", alignment: 77, controversy: 35 },
  { id: "monteiro", name: "Bruno Monteiro", party: "UNIÃO", uf: "GO", role: "Deputado Federal", bio: "Atuação em agro e logística.", alignment: 69, controversy: 47 },
  { id: "pires", name: "Nina Pires", party: "PSD", uf: "RS", role: "Deputada Federal", bio: "Projetos de inovação cívica.", alignment: 74, controversy: 19 },
  { id: "alves", name: "Tiago Alves", party: "REPUBLICANOS", uf: "RJ", role: "Deputado Federal", bio: "Temas de segurança digital.", alignment: 58, controversy: 44 },
  { id: "xavier", name: "Patrícia Xavier", party: "PSDB", uf: "PR", role: "Deputada Federal", bio: "Controle de gastos e accountability.", alignment: 63, controversy: 27 },
];
