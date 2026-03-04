"use client";

import { useState } from "react";

import { apiBase } from "../lib/api";

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function startGoogleSignup() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiBase}/auth/google/start`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const data = (await response.json()) as { auth_url: string };
      window.location.href = data.auth_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start Google signup");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "70vh", textAlign: "center" }}>
      <div style={{ marginBottom: 32 }}>
        <div style={{ width: 64, height: 64, borderRadius: 20, background: "linear-gradient(135deg, var(--accent), var(--accent2))", margin: "0 auto 20px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, boxShadow: "0 8px 32px rgba(79,142,247,0.4)" }}>
          ✦
        </div>
        <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-0.8px", marginBottom: 8, background: "linear-gradient(135deg, #e8edf5 0%, #7a8faa 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          Welcome to Proassist
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: 15, maxWidth: 440, margin: "0 auto 32px", lineHeight: 1.7 }}>
          Your AI-powered job outreach assistant. Generate personalized emails and LinkedIn messages based on your resume and the job description.
        </p>
      </div>

      <section style={{ maxWidth: 420, width: "100%", padding: 32 }}>
        <h2 style={{ fontSize: 17, marginBottom: 8 }}>Get started</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 13.5, marginBottom: 24 }}>
          Sign in with Google to grant Gmail &amp; Drive access for profile upload, draft generation, and email sending.
        </p>
        <button className="btn-google" onClick={startGoogleSignup} disabled={loading} style={{ width: "100%" }}>
          {loading ? (
            <><span className="spinner" style={{ borderColor: "rgba(0,0,0,0.15)", borderTopColor: "#374151" }} /> Redirecting...</>
          ) : (
            <>
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
                <path d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </>
          )}
        </button>
        {error ? <div className="alert alert-error" style={{ marginTop: 16 }}>{error}</div> : null}
      </section>

      <div style={{ display: "flex", gap: 32, marginTop: 48, color: "var(--text-dim)", fontSize: 13 }}>
        {["📄 Resume parsing", "✉️ AI email drafts", "📅 Scheduled sends"].map((f) => (
          <span key={f}>{f}</span>
        ))}
      </div>
    </div>
  );
}
