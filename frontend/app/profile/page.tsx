"use client";

import { FormEvent, useEffect, useState } from "react";

import { apiBase, apiFetch } from "../../lib/api";

type Profile = {
  headline?: string | null;
  years_experience?: number | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  summary?: string | null;
  skills?: string | null;
  location?: string | null;
  phone?: string | null;
};

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile>({
    headline: "",
    years_experience: 0,
    linkedin_url: "",
    github_url: "",
    portfolio_url: "",
    summary: "",
    skills: "",
    location: "",
    phone: "",
  });
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiFetch<Profile | null>("/profile")
      .then((data) => {
        if (data) setProfile(data);
      })
      .catch(() => undefined);
  }, []);

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await apiFetch("/profile", {
        method: "PUT",
        body: JSON.stringify(profile),
      });
      setMessage("Profile saved.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function uploadResume() {
    if (!file) return;
    setBusy(true);
    setMessage("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${apiBase}/resumes/upload`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (!response.ok) throw new Error(await response.text());
      setMessage("Resume uploaded and parsed.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div style={{ marginBottom: 28 }}>
        <p className="page-title">Your Profile</p>
        <p className="page-subtitle">Keep your info up to date so AI can generate highly personalized outreach.</p>
      </div>

      <form onSubmit={saveProfile}>
        <h2 style={{ marginBottom: 20 }}>Professional Info</h2>
        <div className="row">
          <div>
            <label>Headline</label>
            <input
              value={profile.headline || ""}
              onChange={(e) => setProfile({ ...profile, headline: e.target.value })}
              placeholder="e.g. Senior React Developer"
            />
          </div>
          <div>
            <label>Years of Experience</label>
            <input
              type="number"
              value={profile.years_experience || 0}
              onChange={(e) => setProfile({ ...profile, years_experience: Number(e.target.value) })}
              min={0}
              max={50}
            />
          </div>
        </div>

        <div className="row">
          <div>
            <label>Location</label>
            <input
              value={profile.location || ""}
              onChange={(e) => setProfile({ ...profile, location: e.target.value })}
              placeholder="e.g. New York, NY"
            />
          </div>
          <div>
            <label>Phone</label>
            <input
              value={profile.phone || ""}
              onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
              placeholder="+1 555 000 0000"
            />
          </div>
        </div>

        <label>Summary</label>
        <textarea
          rows={4}
          value={profile.summary || ""}
          onChange={(e) => setProfile({ ...profile, summary: e.target.value })}
          placeholder="A brief professional summary..."
        />

        <label>Skills</label>
        <textarea
          rows={3}
          value={profile.skills || ""}
          onChange={(e) => setProfile({ ...profile, skills: e.target.value })}
          placeholder="React, TypeScript, Node.js, PostgreSQL..."
        />

        <div className="divider" />

        <h3 style={{ marginBottom: 16 }}>Links</h3>
        <div className="row-3">
          <div>
            <label>LinkedIn URL</label>
            <input
              value={profile.linkedin_url || ""}
              onChange={(e) => setProfile({ ...profile, linkedin_url: e.target.value })}
              placeholder="https://linkedin.com/in/..."
            />
          </div>
          <div>
            <label>GitHub URL</label>
            <input
              value={profile.github_url || ""}
              onChange={(e) => setProfile({ ...profile, github_url: e.target.value })}
              placeholder="https://github.com/..."
            />
          </div>
          <div>
            <label>Portfolio URL</label>
            <input
              value={profile.portfolio_url || ""}
              onChange={(e) => setProfile({ ...profile, portfolio_url: e.target.value })}
              placeholder="https://..."
            />
          </div>
        </div>

        <button type="submit" disabled={busy}>
          {busy ? <><span className="spinner" />Saving...</> : "Save Profile"}
        </button>
      </form>

      <section>
        <h2 style={{ marginBottom: 8 }}>Resume</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 13.5, marginBottom: 16 }}>Upload your resume to Google Drive so it can be parsed for AI personalization.</p>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <label
            htmlFor="resume-file"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 18px",
              background: "var(--bg2)",
              border: "1px dashed var(--border)",
              borderRadius: "var(--radius-sm)",
              cursor: "pointer",
              color: "var(--text-muted)",
              fontSize: 13.5,
              fontWeight: 500,
              transition: "all var(--transition)",
              marginBottom: 0,
              width: "auto",
            }}
          >
            📎 {file ? file.name : "Choose PDF or DOCX"}
          </label>
          <input
            id="resume-file"
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            style={{ display: "none" }}
          />
          <button onClick={uploadResume} disabled={busy || !file}>
            {busy ? <><span className="spinner" />Uploading...</> : "Upload to Drive"}
          </button>
        </div>
      </section>

      {message ? (
        <div className={`alert ${message.toLowerCase().includes("fail") || message.toLowerCase().includes("error") ? "alert-error" : "alert-success"}`}>
          {message}
        </div>
      ) : null}
    </>
  );
}
