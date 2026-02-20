"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { LayoutDashboard, Menu, RefreshCw } from "lucide-react";

import { apiClient } from "@/lib/api/client";
import { useSessionStore } from "@/lib/state/session.store";
import { cn } from "@/lib/utils";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useToast } from "@/components/ui/use-toast";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/interview", label: "Entrevista" },
  { href: "/results", label: "Resultados" },
  { href: "/budget", label: "Simulador de Orçamento" },
  { href: "/propositions", label: "Proposições" },
];

function NavLinks({ mobile = false }: { mobile?: boolean }) {
  const pathname = usePathname();

  return (
    <nav className={cn("flex flex-col gap-1", mobile ? "mt-4" : "mt-6")}> 
      {navItems.map((item) => {
        const active = pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-md px-3 py-2 text-sm transition-colors",
              active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

function MobileNav() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="md:hidden" aria-label="Abrir menu">
          <Menu className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left">
        <SheetHeader>
          <SheetTitle>Brado</SheetTitle>
        </SheetHeader>
        <NavLinks mobile />
      </SheetContent>
    </Sheet>
  );
}

function Topbar() {
  const { toast } = useToast();
  const router = useRouter();
  const sessionId = useSessionStore((state) => state.sessionId);
  const authMe = useSessionStore((state) => state.authMe);
  const clearSessionOnly = useSessionStore((state) => state.clearSessionOnly);
  const resetAll = useSessionStore((state) => state.resetAll);

  const authQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: apiClient.authMe,
    refetchInterval: 120_000,
  });

  const currentAuth = authQuery.data ?? authMe;

  return (
    <header className="sticky top-0 z-20 border-b bg-background/95 backdrop-blur">
      <div className="flex h-14 items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <MobileNav />
          <div className="flex items-center gap-2">
            <LayoutDashboard className="h-4 w-4 text-primary" />
            <span className="font-semibold">Brado</span>
          </div>
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant="secondary">{currentAuth ? `auth: ${currentAuth.subject}` : "auth: pendente"}</Badge>
            </TooltipTrigger>
            <TooltipContent>
              <span>TTL: {typeof currentAuth?.ttl === "number" ? `${currentAuth.ttl}s` : "n/d"}</span>
            </TooltipContent>
          </Tooltip>
          <Separator orientation="vertical" className="h-5" />
          <Badge variant="outline">sessão: {sessionId ?? "nenhuma"}</Badge>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => {
              clearSessionOnly();
              toast({ title: "Sessão local resetada" });
              router.push("/dashboard");
            }}
          >
            Reset sessão
          </Button>
          <DropdownMenu>
            <div className="relative">
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">Ações</Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuLabel>Sessão</DropdownMenuLabel>
                <DropdownMenuItem
                  onSelect={() => {
                    clearSessionOnly();
                    toast({ title: "Sessão local resetada" });
                    router.push("/dashboard");
                  }}
                >
                  Reset sessão
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onSelect={() => {
                    resetAll();
                    toast({ title: "Autenticação e sessão limpas" });
                    router.push("/dashboard");
                  }}
                >
                  Limpar tudo
                </DropdownMenuItem>
              </DropdownMenuContent>
            </div>
          </DropdownMenu>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Atualizar autenticação"
            onClick={() => authQuery.refetch()}
          >
            <RefreshCw className={cn("h-4 w-4", authQuery.isFetching && "animate-spin")} />
          </Button>
        </div>
      </div>
    </header>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-stone-100">
      <Topbar />
      <div className="mx-auto flex max-w-[1400px]">
        <aside className="sticky top-14 hidden h-[calc(100vh-56px)] w-72 border-r bg-background/80 px-4 py-5 md:block">
          <p className="text-xs font-semibold uppercase text-muted-foreground">Navegação</p>
          <NavLinks />
        </aside>
        <main className="flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
