import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Inventory Manager',
  description: 'A simple inventory management application',
  viewport: "width=device-width, initial-scale=1",
  authors: [{ name: "Posey.ai", url: "https://posey.ai" }],
  generator: "Next.js",
  applicationName: "Posey Inventory",
  keywords: ["inventory", "management", "qr code", "storage", "organization", "posey"],
  colorScheme: "dark light",
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
    { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
  ],
}; 