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
    <section>
      <h2>Google Signup Required</h2>
      <p>
        Sign in with Google and grant Gmail + Drive scopes to use profile upload, draft generation, and email sending.
      </p>
      <button onClick={startGoogleSignup} disabled={loading}>
        {loading ? "Redirecting..." : "Continue with Google"}
      </button>
      {error ? <p>{error}</p> : null}
    </section>
  );
}
