import type { ApiError } from "@/lib/api/types";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function getTechnical(error: unknown): string | null {
  const apiError = error as ApiError;
  if (!apiError?.technical) return null;

  try {
    return JSON.stringify(apiError.technical, null, 2);
  } catch {
    return String(apiError.technical);
  }
}

export function ApiErrorNotice({ error }: { error: Error | null }) {
  if (!error) return null;

  const technical = getTechnical(error);

  return (
    <Card className="border-destructive/40">
      <CardHeader>
        <CardTitle className="text-base text-destructive">Não foi possível concluir a ação</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm">{error.message || "Erro inesperado."}</p>
        {technical ? (
          <details className="mt-2">
            <summary className="cursor-pointer text-sm text-muted-foreground">Detalhe técnico</summary>
            <pre className="mt-2 max-h-48 overflow-auto rounded-md border bg-muted/20 p-2 text-xs">{technical}</pre>
          </details>
        ) : null}
      </CardContent>
    </Card>
  );
}
