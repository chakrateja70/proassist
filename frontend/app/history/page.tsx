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

  function statusBadge(status: string | null) {
    if (!status) return <span className="badge badge-muted">—</span>;
    const s = status.toLowerCase();
    if (s === "sent") return <span className="badge badge-success">{status}</span>;
    if (s === "approved") return <span className="badge badge-info">{status}</span>;
    if (s === "failed" || s === "error") return <span className="badge badge-error">{status}</span>;
    if (s === "scheduled") return <span className="badge badge-purple">{status}</span>;
    return <span className="badge badge-muted">{status}</span>;
  }

  return (
    <>
      <div style={{ marginBottom: 28 }}>
        <p className="page-title">History</p>
        <p className="page-subtitle">All your draft and send activity in one place.</p>
      </div>

      <section>
        {error ? <div className="alert alert-error">{error}</div> : null}
        {!error && items.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <div style={{ fontWeight: 600, fontSize: 15, color: "var(--text-muted)" }}>No history yet</div>
            <div style={{ fontSize: 13 }}>Generate your first outreach from the App page.</div>
          </div>
        ) : null}
        {items.map((item) => (
          <div key={item.draft_id} className="history-card">
            <div className="history-card-header">
              <div>
                <p className="history-card-title">{item.role_title || "Unknown Role"}</p>
                <p className="history-card-company">{item.company_name || "Unknown Company"}</p>
              </div>
              <div style={{ display: "flex", gap: 6, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
                {statusBadge(item.draft_status)}
                {statusBadge(item.send_status)}
              </div>
            </div>
            <div className="history-card-meta">
              {item.to_email && (
                <span className="meta-item">
                  <span>✉</span> {item.to_email}
                </span>
              )}
              <span className="meta-item">
                <span>🕐</span> {new Date(item.created_at).toLocaleString()}
              </span>
              {item.scheduled_at && (
                <span className="meta-item">
                  <span>📅</span> Scheduled: {new Date(item.scheduled_at).toLocaleString()}
                </span>
              )}
              {item.sent_at && (
                <span className="meta-item">
                  <span>✅</span> Sent: {new Date(item.sent_at).toLocaleString()}
                </span>
              )}
            </div>
          </div>
        ))}
      </section>
    </>
  );
}
