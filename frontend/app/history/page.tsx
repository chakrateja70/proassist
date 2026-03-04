"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "../../lib/api";

type HistoryItem = {
  draft_id: string;
  send_id: string | null;
  company_name: string | null;
  role_title: string | null;
  to_email: string | null;
  draft_status: string;
  send_status: string | null;
  created_at: string;
  sent_at: string | null;
  scheduled_at: string | null;
};

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<HistoryItem[]>("/history")
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to fetch history"));
  }, []);

  return (
    <section>
      <h2>Draft and Send History</h2>
      {error ? <p>{error}</p> : null}
      {items.length === 0 ? <p>No history yet.</p> : null}
      {items.map((item) => (
        <section key={item.draft_id}>
          <p>
            <strong>{item.role_title || "Role unknown"}</strong> at <strong>{item.company_name || "Unknown company"}</strong>
          </p>
          <p>Draft Status: {item.draft_status}</p>
          <p>Send Status: {item.send_status || "Not sent"}</p>
          <p>To: {item.to_email || "-"}</p>
          <p>Created: {new Date(item.created_at).toLocaleString()}</p>
          {item.scheduled_at ? <p>Scheduled: {new Date(item.scheduled_at).toLocaleString()}</p> : null}
          {item.sent_at ? <p>Sent: {new Date(item.sent_at).toLocaleString()}</p> : null}
        </section>
      ))}
    </section>
  );
}
