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
        <div className="page-wrapper">
          <header className="navbar">
            <Link href="/" className="navbar-brand">
              <span className="brand-dot" />
              Proassist
            </Link>
            <nav className="navbar-links">
              <Link href="/app">App</Link>
              <Link href="/profile">Profile</Link>
              <Link href="/history">History</Link>
            </nav>
          </header>
          <div className="page-content">{children}</div>
        </div>
      </body>
    </html>
  );
}
