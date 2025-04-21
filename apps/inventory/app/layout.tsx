'use client';
import { Inter } from "next/font/google";
import { SuperTokensProvider } from '@/app/providers/supertokens';
import { createSupertokensFrontendConfig } from '@posey.ai/core';
import Sidebar from "@/components/sidebar";
import { DrawerContent, Navbar } from '@posey.ai/ui';

import "./globals.css";
import "@posey.ai/ui/style.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-geist-sans" });

const supertokensConfig = createSupertokensFrontendConfig({
  appName: `Posey`
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" data-theme="dark" className="bg-background">
      <body className={`${inter.className} antialiased`}>
        <SuperTokensProvider
          publicPaths={[
            `/auth`
          ]}
          supertokensConfig={supertokensConfig}
        >
          <DrawerContent sidebar={<Sidebar />}>
            <Navbar withStartChat={false} />
            <div className="drawer-content flex flex-col">
              <main className="flex-1 p-10">{children}</main>
            </div>
          </DrawerContent>
        </SuperTokensProvider>
      </body>
    </html>
  );
}
