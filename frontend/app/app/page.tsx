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
      <form onSubmit={createJob}>
        <h2>1) Paste Job Description</h2>
        <textarea rows={10} value={jdText} onChange={(e) => setJdText(e.target.value)} required />
        <label>Job URL (optional)</label>
        <input value={jdUrl} onChange={(e) => setJdUrl(e.target.value)} />
        <label>Language</label>
        <select value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
        </select>
        <button type="submit" disabled={busy}>
          Save Job Input
        </button>
      </form>

      {job ? (
        <section>
          <h2>2) Confirm HR Email</h2>
          <p>
            Role: <strong>{job.role_title || "Not detected"}</strong> | Company:{" "}
            <strong>{job.company_name || "Not detected"}</strong>
          </p>
          <label>Extracted emails</label>
          <select value={selectedEmail} onChange={(e) => setSelectedEmail(e.target.value)}>
            <option value="">Select email</option>
            {job.extracted_contacts.map((contact) => (
              <option key={contact.email} value={contact.email}>
                {contact.email} ({Math.round(contact.confidence * 100)}%)
              </option>
            ))}
          </select>
          <label>Or type email manually</label>
          <input value={selectedEmail} onChange={(e) => setSelectedEmail(e.target.value)} />
          <button onClick={generateDraft} disabled={busy}>
            Generate Gmail + LinkedIn Draft
          </button>
        </section>
      ) : null}

      {draft ? (
        <section>
          <h2>3) Review and Approve</h2>
          <label>Gmail Subject</label>
          <input
            value={draft.gmail_subject}
            onChange={(e) => setDraft({ ...draft, gmail_subject: e.target.value })}
          />
          <label>Gmail Body</label>
          <textarea
            rows={12}
            value={draft.gmail_body}
            onChange={(e) => setDraft({ ...draft, gmail_body: e.target.value })}
          />
          <label>LinkedIn Message</label>
          <textarea
            rows={5}
            value={draft.linkedin_message}
            onChange={(e) => setDraft({ ...draft, linkedin_message: e.target.value })}
          />
          <p>Rationale: {draft.personalization_rationale}</p>
          <button onClick={approveDraft} disabled={busy || !selectedEmail}>
            Approve Draft
          </button>

          <h3>4) Send</h3>
          <button onClick={() => send("immediate")} disabled={busy || !selectedEmail}>
            Send Now
          </button>
          <div className="row">
            <div>
              <label>Schedule Time</label>
              <input type="datetime-local" value={scheduleAt} onChange={(e) => setScheduleAt(e.target.value)} />
            </div>
            <div style={{ alignSelf: "end" }}>
              <button
                className="secondary"
                onClick={() => send("scheduled")}
                disabled={busy || !selectedEmail || !scheduleAt}
              >
                Schedule Send
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {statusMessage ? <section>{statusMessage}</section> : null}
    </>
  );
}
