import type { Vote } from "@/lib/data/types";

const topics = ["Economia", "Segurança", "Saúde", "Educação", "Infraestrutura", "Tributário"];

function seeded(seed: string) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i += 1) {
    h ^= seed.charCodeAt(i);
    h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24);
  }
  return () => {
    h += 0x6d2b79f5;
    let t = Math.imul(h ^ (h >>> 15), 1 | h);
    t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function buildVotesForParlamentar(parlamentarId: string, count = 60): Vote[] {
  const rnd = seeded(parlamentarId);
  const now = new Date("2026-02-19T12:00:00.000Z").getTime();

  return Array.from({ length: count }).map((_, i) => {
    const n = i + 1;
    const dayOffset = i * 2;
    const date = new Date(now - dayOffset * 86_400_000);
    const favor = rnd() > 0.33;
    const controversial = rnd() > 0.72;
    const aligned = rnd() > 0.24;
    const yes = Math.floor(220 + rnd() * 220);
    const no = Math.floor(40 + rnd() * 180);
    const abstention = Math.floor(rnd() * 30);
    const topic = topics[i % topics.length];

    return {
      id: `${parlamentarId}-vote-${n}`,
      parlamentarId,
      date: date.toISOString(),
      title: `Votação ${n} sobre ${topic.toLowerCase()} e governança pública`,
      description: "Discussão em plenário com impacto fiscal e social. Análise de aderência ao programa partidário.",
      voteType: favor ? "favor" : "contra",
      alignedWithParty: aligned,
      controversial,
      outcome: yes > no ? "Aprovado" : rnd() > 0.8 ? "Adiado/Abst." : "Rejeitado",
      topic,
      code: `PLP ${60 + n}/2024`,
      yes,
      no,
      abstention,
      context: "A matéria foi alvo de pressão de frentes parlamentares e impacto direto no orçamento setorial.",
      externalUrl: `https://www.camara.leg.br/propostas-legislativas/${100000 + n}`,
    };
  });
}
