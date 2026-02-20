"use client";

import { useState } from "react";
import { Menu } from "lucide-react";

import { Sidebar } from "@/components/layout/sidebar";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="v2-shell">
      <Sidebar />
      <main className="v2-main">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <div className="v2-mobile-sidebar-trigger">
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" aria-label="Abrir navegacao">
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
          </div>
          <SheetContent side="left" className="w-[288px] p-0">
            <Sidebar mobile onNavigate={() => setMobileOpen(false)} />
          </SheetContent>
        </Sheet>
        {children}
      </main>
    </div>
  );
}
