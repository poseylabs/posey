'use client';

import { Inter } from "next/font/google";
import { SuperTokensProvider } from '@/providers/supertokens';
import { createSupertokensFrontendConfig } from '@posey.ai/core';
import { DrawerContent, Navbar, AdminNavbar, ContentWrapper } from '@posey.ai/ui';

import "@posey.ai/ui/style.css";
import "@/app/style/globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-geist-sans" });

const supertokensConfig = createSupertokensFrontendConfig({
  appName: `Posey`
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (
    <html lang="en">
      <head>
        <title>Posey</title>
      </head>
      <body className={`${inter.className} antialiased`}>
        <SuperTokensProvider
          publicPaths={[
            `/auth`
          ]}
          supertokensConfig={supertokensConfig}>
          <div className="layout-wrapper">{children}</div>
        </SuperTokensProvider>
      </body>
    </html>
  );
}
