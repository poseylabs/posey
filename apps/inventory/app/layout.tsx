'use client';

import { Inter } from "next/font/google";
import Link from "next/link";
import { ClientProviders } from './providers/client-providers';

// Import styles
import "@posey.ai/ui/style/posey.ui.css";
import "./globals.css";

// Initialize font
const inter = Inter({ subsets: ["latin"], variable: "--font-geist-sans" });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" data-theme="dark" className="bg-background">
      <body className={`${inter.className} antialiased`}>
        <ClientProviders>
          <div className="drawer lg:drawer-open">
            {/* Hidden drawer toggle */}
            <input id="menu-drawer" type="checkbox" className="drawer-toggle" />

            {/* Main content */}
            <div className="drawer-content flex flex-col">
              {/* Mobile menu */}
              <div className="sticky top-0 z-30 lg:hidden bg-base-100 border-b border-base-300">
                <div className="flex items-center px-4 h-16">
                  <label htmlFor="menu-drawer" className="btn btn-square btn-ghost">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="inline-block w-6 h-6 stroke-current">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                  </label>
                  <div className="flex-1 px-2 mx-2 text-2xl font-bold">Inventory Manager</div>
                </div>
              </div>

              {/* Page content */}
              <main className="flex-1 p-10">{children}</main>
            </div>

            {/* Sidebar */}
            <aside className="drawer-side">
              <label htmlFor="menu-drawer" aria-label="close sidebar" className="drawer-overlay"></label>
              <ul className="menu p-4 w-64 min-h-full bg-base-200 text-base-content">
                <li className="mb-4">
                  <h2 className="menu-title text-lg font-bold">Inventory Manager</h2>
                </li>
                <li>
                  <Link href="/dashboard" className="py-3">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h2a1 1 0 001-1v-4a1 1 0 00-1-1h-4a1 1 0 00-1 1v4a1 1 0 01-1 1H7a1 1 0 01-1-1v-7" />
                    </svg>
                    Dashboard
                  </Link>
                </li>
                <li>
                  <Link href="/pods" className="py-3">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8M10 14a2 2 0 100-4 2 2 0 000 4z" />
                    </svg>
                    Storage Pods
                  </Link>
                </li>
                <li>
                  <Link href="/items" className="py-3">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                    </svg>
                    Items
                  </Link>
                </li>
                <li>
                  <Link href="/search" className="py-3">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    Search
                  </Link>
                </li>
                <div className="divider"></div>
                <li>
                  <Link href="/settings" className="py-3">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Database Settings
                  </Link>
                </li>
                <div className="mt-auto text-center text-xs text-gray-500 py-2">
                  <div>Inventory Manager v0.1.0</div>
                  <div>© 2023 Posey.ai</div>
                </div>
              </ul>
            </aside>
          </div>
        </ClientProviders>
      </body>
    </html>
  );
}
