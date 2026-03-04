"use client";

import { FormEvent, useState } from "react";

import { apiFetch } from "../../lib/api";

type Contact = { email: string; source_span: string; confidence: number };
type JobResponse = {
  id: string;
  role_title: string | null;
  company_name: string | null;
  extracted_contacts: Contact[];
};
type DraftGenerateResponse = {
  draft_id: string;
  gmail_subject: string;
  gmail_body: string;
  linkedin_message: string;
  personalization_rationale: string;
};

export default function AppWorkflowPage() {
  const [jdText, setJdText] = useState("");
  const [jdUrl, setJdUrl] = useState("");
  const [language, setLanguage] = useState("en");
  const [job, setJob] = useState<JobResponse | null>(null);
  const [selectedEmail, setSelectedEmail] = useState("");
  const [draft, setDraft] = useState<DraftGenerateResponse | null>(null);
  const [scheduleAt, setScheduleAt] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function createJob(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setStatusMessage("");
    try {
      const data = await apiFetch<JobResponse>("/jobs", {
        method: "POST",
        body: JSON.stringify({ jd_text: jdText, jd_url: jdUrl || null, language }),
      });
      setJob(data);
      setSelectedEmail(data.extracted_contacts[0]?.email || "");
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Unable to create job");
    } finally {
      setBusy(false);
    }
  }

  async function generateDraft() {
    if (!job) return;
    setBusy(true);
    setStatusMessage("");
    try {
      const data = await apiFetch<DraftGenerateResponse>("/drafts/generate", {
        method: "POST",
        body: JSON.stringify({ job_id: job.id }),
      });
      setDraft(data);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Draft generation failed");
    } finally {
      setBusy(false);
    }
  }

  async function approveDraft() {
    if (!draft) return;
    setBusy(true);
    setStatusMessage("");
    try {
      await apiFetch(`/drafts/${draft.draft_id}`, {
        method: "PATCH",
        body: JSON.stringify({
          gmail_subject: draft.gmail_subject,
          gmail_body: draft.gmail_body,
          linkedin_message: draft.linkedin_message,
          selected_hr_email: selectedEmail,
          approve: true,
        }),
      });
      setStatusMessage("Draft approved.");
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setBusy(false);
    }
  }

  async function send(mode: "immediate" | "scheduled") {
    if (!draft) return;
    setBusy(true);
    setStatusMessage("");
    try {
      await apiFetch("/sends", {
        method: "POST",
        body: JSON.stringify({
          draft_id: draft.draft_id,
          to_email: selectedEmail,
          mode,
          scheduled_at: mode === "scheduled" ? new Date(scheduleAt).toISOString() : null,
        }),
      });
      setStatusMessage(mode === "immediate" ? "Email sent." : "Email scheduled.");
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Send failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div style={{ marginBottom: 28 }}>
        <p className="page-title">Generate Outreach</p>
        <p className="page-subtitle">Paste a job description and let AI craft a personalized email and LinkedIn message for you.</p>
      </div>

      {/* Step 1 */}
      <form onSubmit={createJob}>
        <div className="step-label"><span className="step-num">1</span>Paste Job Description</div>
        <h2 style={{ marginBottom: 16 }}>Job Details</h2>
        <label>Job Description *</label>
        <textarea
          rows={10}
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
          placeholder="Paste the full job description here..."
          required
          style={{ fontFamily: "inherit" }}
        />
        <div className="row">
          <div>
            <label>Job URL (optional)</label>
            <input value={jdUrl} onChange={(e) => setJdUrl(e.target.value)} placeholder="https://..." />
          </div>
          <div>
            <label>Language</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="en">🇬🇧 English</option>
              <option value="es">🇪🇸 Spanish</option>
              <option value="fr">🇫🇷 French</option>
              <option value="de">🇩🇪 German</option>
            </select>
          </div>
        </div>
        <button type="submit" disabled={busy} style={{ marginTop: 4 }}>
          {busy ? <><span className="spinner" />Processing...</> : "Analyse Job →"}
        </button>
      </form>

      {/* Step 2 */}
      {job ? (
        <section>
          <div className="step-label"><span className="step-num">2</span>Confirm Recipient</div>
          <h2 style={{ marginBottom: 16 }}>Job Detected</h2>
          <div className="row" style={{ marginBottom: 16 }}>
            <div style={{ background: "var(--bg2)", borderRadius: "var(--radius-sm)", padding: "12px 16px", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.6px", color: "var(--text-muted)", marginBottom: 4 }}>Role</div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>{job.role_title || <span style={{ color: "var(--text-dim)" }}>Not detected</span>}</div>
            </div>
            <div style={{ background: "var(--bg2)", borderRadius: "var(--radius-sm)", padding: "12px 16px", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.6px", color: "var(--text-muted)", marginBottom: 4 }}>Company</div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>{job.company_name || <span style={{ color: "var(--text-dim)" }}>Not detected</span>}</div>
            </div>
          </div>
          {job.extracted_contacts.length > 0 && (
            <>
              <label>Extracted contacts</label>
              <select value={selectedEmail} onChange={(e) => setSelectedEmail(e.target.value)}>
                <option value="">Select email</option>
                {job.extracted_contacts.map((c) => (
                  <option key={c.email} value={c.email}>
                    {c.email} — {Math.round(c.confidence * 100)}% confidence
                  </option>
                ))}
              </select>
            </>
          )}
          <label>Recipient email</label>
          <input
            value={selectedEmail}
            onChange={(e) => setSelectedEmail(e.target.value)}
            placeholder="recruiter@company.com"
          />
          <button onClick={generateDraft} disabled={busy}>
            {busy ? <><span className="spinner" />Generating...</> : "✨ Generate Draft"}
          </button>
        </section>
      ) : null}

      {/* Step 3 */}
      {draft ? (
        <section>
          <div className="step-label"><span className="step-num">3</span>Review &amp; Approve</div>
          <h2 style={{ marginBottom: 20 }}>Your Draft</h2>

          <label>Gmail Subject</label>
          <input
            value={draft.gmail_subject}
            onChange={(e) => setDraft({ ...draft, gmail_subject: e.target.value })}
            style={{ fontWeight: 500 }}
          />

          <label>Gmail Body</label>
          <textarea
            rows={12}
            value={draft.gmail_body}
            onChange={(e) => setDraft({ ...draft, gmail_body: e.target.value })}
          />

          <label>LinkedIn Message</label>
          <textarea
            rows={4}
            value={draft.linkedin_message}
            onChange={(e) => setDraft({ ...draft, linkedin_message: e.target.value })}
          />

          <label>AI Personalization Rationale</label>
          <div className="rationale-box">{draft.personalization_rationale}</div>

          <div className="divider" style={{ margin: "20px 0" }} />

          <button onClick={approveDraft} disabled={busy || !selectedEmail} style={{ marginBottom: 20, width: "100%" }}>
            {busy ? <><span className="spinner" />Saving...</> : "✓ Approve Draft"}
          </button>

          <div className="step-label" style={{ marginBottom: 12 }}><span className="step-num">4</span>Send</div>
          <div className="row" style={{ alignItems: "end" }}>
            <div>
              <label>Schedule Time (optional)</label>
              <input
                type="datetime-local"
                value={scheduleAt}
                onChange={(e) => setScheduleAt(e.target.value)}
                style={{ colorScheme: "dark" }}
              />
            </div>
            <div style={{ display: "flex", gap: 10, paddingBottom: 16 }}>
              <button
                onClick={() => send("immediate")}
                disabled={busy || !selectedEmail}
                style={{ flex: 1 }}
              >
                {busy ? <><span className="spinner" />Sending...</> : "⚡ Send Now"}
              </button>
              <button
                className="secondary"
                onClick={() => send("scheduled")}
                disabled={busy || !selectedEmail || !scheduleAt}
                style={{ flex: 1 }}
              >
                🕐 Schedule
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {statusMessage ? (
        <div className={`alert ${statusMessage.toLowerCase().includes("fail") || statusMessage.toLowerCase().includes("error") ? "alert-error" : "alert-success"}`}>
          {statusMessage}
        </div>
      ) : null}
    </>
  );
}
