import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Proassist",
  description: "Personalized job outreach assistant",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main>
          <h1>Proassist</h1>
          <nav>
            <Link href="/">Home</Link>
            <Link href="/app">App</Link>
            <Link href="/profile">Profile</Link>
            <Link href="/history">History</Link>
          </nav>
          {children}
        </main>
      </body>
    </html>
  );
}
