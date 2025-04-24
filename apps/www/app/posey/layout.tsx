'use client';

import { Inter } from "next/font/google";
import { SuperTokensProvider } from '@/providers/supertokens';
import { createSupertokensFrontendConfig } from '@posey.ai/core';
import { DrawerContent, Navbar, AdminNavbar, ContentWrapper } from '@posey.ai/ui';

import "@posey.ai/ui/style.css";
import "@/app/style/globals.css";

import Link from "next/link";

const inter = Inter({ subsets: ["latin"], variable: "--font-geist-sans" });

const supertokensConfig = createSupertokensFrontendConfig({
  appName: `Posey`
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  const adminLinks: any = [
    {
      label: 'Admin Tools',
      href: '/admin',
      isActive: false
    },
    {
      label: 'Models',
      href: '/admin/models',
      isActive: false
    },
    {
      label: 'Providers',
      href: '/admin/providers',
      isActive: false
    },
    {
      label: 'Minions',
      href: '/admin/minions',
      isActive: false
    },
    {
      label: 'Invites',
      href: '/admin/invites',
      isActive: false
    }
  ]

  return (
    <DrawerContent>
      <div>
        <Navbar withStartChat={true} />
        <AdminNavbar
          links={adminLinks}
          LinkComponent={Link}
        />
      </div>
      <ContentWrapper className="flex-1">{children}</ContentWrapper>
    </DrawerContent>
  );
}
