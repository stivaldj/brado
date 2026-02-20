import "./globals.css";
import type { Metadata } from "next";

import { AppProviders } from "@/components/providers/app-providers";

export const metadata: Metadata = {
  title: "Brado Manifest App",
  description: "Frontend analítico para entrevistas e simulações do Brado",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="font-sans antialiased">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
