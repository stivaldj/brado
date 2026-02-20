import { redirect } from "next/navigation";

export default async function DossieRootPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  redirect(`/dossie/${id}/votos`);
}
