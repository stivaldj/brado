import type { Expense } from "@/lib/data/types";

const categories = ["CEAP", "Gabinete", "Transporte", "Comunicação", "Consultoria"];
const vendors = ["Alpha Consultoria", "Via Cidadã", "Norte Serviços", "Delta Log", "Imprensa Cívica"];

export function buildExpensesForParlamentar(parlamentarId: string, count = 42): Expense[] {
  return Array.from({ length: count }).map((_, i) => {
    const n = i + 1;
    const value = Math.round((1200 + (n * 173) % 9100) * 100) / 100;
    return {
      id: `${parlamentarId}-expense-${n}`,
      parlamentarId,
      date: new Date(Date.now() - n * 3 * 86_400_000).toISOString(),
      category: categories[n % categories.length],
      vendor: vendors[n % vendors.length],
      value,
      outlier: value > 7800,
    };
  });
}
