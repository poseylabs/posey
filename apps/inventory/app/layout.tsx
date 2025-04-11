'use client';

import { Inter } from "next/font/google";
import Link from "next/link";
import { ClientProviders } from './providers/client-providers';
import React from 'react';
import { DrawerContent, Navbar } from '@posey.ai/ui';

// Import styles
import "./globals.css";
import "@posey.ai/ui/style.css";
import Sidebar from "@/components/sidebar";

// Initialize font
const inter = Inter({ subsets: ["latin"], variable: "--font-geist-sans" });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const closeDrawer = () => {
    const drawerCheckbox = document.getElementById('menu-drawer') as HTMLInputElement | null;
    if (drawerCheckbox) {
      drawerCheckbox.checked = false;
    }
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLUListElement>) => {
    if ((event.target as HTMLElement).closest('a')) {
      closeDrawer();
    }
  };

  return (
    <html lang="en" data-theme="dark" className="bg-background">
      <body className={`${inter.className} antialiased`}>
        <ClientProviders>
          <DrawerContent sidebar={<Sidebar />}>
            <Navbar withStartChat={false} content={false} />
            <div className="drawer-content flex flex-col">
              <main className="flex-1 p-10">{children}</main>
            </div>
          </DrawerContent>
          {/* <div className="drawer">

            <input id="menu-drawer" type="checkbox" className="drawer-toggle" />


            <div className="drawer-content flex flex-col">

              <div className="sticky top-0 z-30 bg-base-100 border-b border-base-300">
                <div className="flex items-center px-4 h-16">

                  <label htmlFor="menu-drawer" className="btn btn-square btn-ghost">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="inline-block w-6 h-6 stroke-current">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                  </label>
                  <div className="flex-1 px-2 mx-2 text-2xl font-bold">Inventory Manager</div>
                </div>
              </div>


              <main className="flex-1 p-10">{children}</main>
            </div> */}

          {/* Sidebar - Added w-80 */}
          {/* <Sidebar /> */}

          {/* </div> */}
        </ClientProviders>
      </body>
    </html>
  );
}
