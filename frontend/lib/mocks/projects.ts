import type { Project } from "@/lib/data/types";

const statuses: Project["status"][] = ["Em tramitação", "Aprovado", "Arquivado"];
const priorities: Project["priority"][] = ["Baixa", "Média", "Alta"];

export function buildProjectsForParlamentar(parlamentarId: string, count = 14): Project[] {
  return Array.from({ length: count }).map((_, i) => {
    const id = i + 1;
    return {
      id: `${parlamentarId}-project-${id}`,
      parlamentarId,
      code: `PL ${1500 + id}/2025`,
      title: `Projeto ${id} de modernização de serviços públicos digitais`,
      status: statuses[id % statuses.length],
      priority: priorities[id % priorities.length],
      updatedAt: new Date(Date.now() - id * 4 * 86_400_000).toISOString(),
    };
  });
}
