"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bot,
  CircleDollarSign,
  FileSpreadsheet,
  Gauge,
  LayoutList,
  Radar,
  Users2,
  Vote,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import { useUiStore } from "@/lib/state/ui.store";

interface SidebarProps {
  mobile?: boolean;
  onNavigate?: () => void;
}

export function Sidebar({ mobile = false, onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const sidebarCollapsed = useUiStore((state) => state.shell.sidebarCollapsed);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);
  const selectedParlamentarId = useUiStore((state) => state.selectedParlamentarId);

  const dossieId = selectedParlamentarId ?? "mendes";
  const dossieVotesHref = `/dossie/${dossieId}/votos`;
  const dossieProjectsHref = `/dossie/${dossieId}/projetos`;
  const dossieExpensesHref = `/dossie/${dossieId}/gastos`;

  const groups = [
    {
      title: "Painel",
      items: [
        { label: "Dashboard", href: "/dashboard", icon: Gauge, active: pathname.startsWith("/dashboard") },
        { label: "Parlamentares", href: "/parlamentares", icon: Users2, active: pathname.startsWith("/parlamentares") },
        { label: "Proposições", href: "/propositions", icon: LayoutList, active: pathname.startsWith("/propositions") },
        { label: "Resultados", href: "/results", icon: Radar, active: pathname.startsWith("/results") },
        { label: "Orçamento", href: "/budget", icon: CircleDollarSign, active: pathname.startsWith("/budget") },
        { label: "Entrevista", href: "/interview", icon: Bot, active: pathname.startsWith("/interview") },
      ],
    },
    {
      title: "Dossiê",
      items: [
        { label: "Votos", href: dossieVotesHref, icon: Vote, active: pathname.startsWith("/dossie/") && pathname.endsWith("/votos") },
        { label: "Projetos", href: dossieProjectsHref, icon: FileSpreadsheet, active: pathname.startsWith("/dossie/") && pathname.endsWith("/projetos") },
        { label: "Gastos", href: dossieExpensesHref, icon: BarChart3, active: pathname.startsWith("/dossie/") && pathname.endsWith("/gastos") },
      ],
    },
  ];

  const desktopClass = sidebarCollapsed ? "v2-sidebar v2-sidebar--desktop v2-sidebar--collapsed" : "v2-sidebar v2-sidebar--desktop";

  return (
    <aside className={mobile ? "v2-sidebar v2-sidebar--mobile" : desktopClass} aria-label="Sidebar">
      <Link href="/parlamentares" className="v2-sidebar-logo" onClick={onNavigate}>
        M_BR
      </Link>

      <div className="v2-sidebar-nav">
        {groups.map((group) => (
          <section key={group.title} className="v2-sidebar-group">
            <p className="v2-sidebar-group-title">{group.title}</p>
            <div className="space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={`${item.href}-${item.label}`}
                    aria-label={item.label}
                    href={item.href}
                    onClick={onNavigate}
                    className={item.active ? "v2-sidebar-link active" : "v2-sidebar-link"}
                  >
                    <span className="v2-sidebar-dot" />
                    <Icon className="h-3.5 w-3.5 shrink-0" />
                    <span className="v2-sidebar-link-label">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      {!mobile ? (
        <button type="button" onClick={toggleSidebar} className="v2-sidebar-collapse" aria-label="Alternar menu lateral">
          {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          <span>{sidebarCollapsed ? "Expandir" : "Recolher"}</span>
        </button>
      ) : null}
    </aside>
  );
}
