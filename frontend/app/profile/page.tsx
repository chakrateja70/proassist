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
      <form onSubmit={saveProfile}>
        <h2>Profile</h2>
        <label>Headline</label>
        <input value={profile.headline || ""} onChange={(e) => setProfile({ ...profile, headline: e.target.value })} />
        <label>Years of Experience</label>
        <input
          type="number"
          value={profile.years_experience || 0}
          onChange={(e) => setProfile({ ...profile, years_experience: Number(e.target.value) })}
        />
        <label>LinkedIn URL</label>
        <input
          value={profile.linkedin_url || ""}
          onChange={(e) => setProfile({ ...profile, linkedin_url: e.target.value })}
        />
        <label>GitHub URL</label>
        <input value={profile.github_url || ""} onChange={(e) => setProfile({ ...profile, github_url: e.target.value })} />
        <label>Portfolio URL</label>
        <input
          value={profile.portfolio_url || ""}
          onChange={(e) => setProfile({ ...profile, portfolio_url: e.target.value })}
        />
        <label>Summary</label>
        <textarea value={profile.summary || ""} onChange={(e) => setProfile({ ...profile, summary: e.target.value })} />
        <label>Skills</label>
        <textarea value={profile.skills || ""} onChange={(e) => setProfile({ ...profile, skills: e.target.value })} />
        <label>Location</label>
        <input value={profile.location || ""} onChange={(e) => setProfile({ ...profile, location: e.target.value })} />
        <label>Phone</label>
        <input value={profile.phone || ""} onChange={(e) => setProfile({ ...profile, phone: e.target.value })} />
        <button type="submit" disabled={busy}>
          Save Profile
        </button>
      </form>

      <section>
        <h2>Resume Upload</h2>
        <input type="file" accept=".pdf,.docx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button onClick={uploadResume} disabled={busy || !file}>
          Upload to Google Drive
        </button>
      </section>

      {message ? <section>{message}</section> : null}
    </>
  );
}
