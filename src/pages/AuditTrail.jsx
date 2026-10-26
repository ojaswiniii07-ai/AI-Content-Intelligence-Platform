import { useState } from 'react'

const initialEvents = [
  {
    id: 'evt_9041',
    type: 'Submission Analyzed',
    time: '2026-10-26 21:02:14 UTC',
    dot: 'green',
    desc: 'sub_0041 · Model: text-detector-v2.4 · Result: High AI Signal (74%)',
    user: 'System Automated Pipeline',
    details: {
      submissionId: 'sub_0041',
      modelVersion: 'text-detector-v2.4 (SHA: 8f3a9e2d)',
      hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      decisionRationale: 'Confidence threshold 0.70 reached. Flagged for reviewer review.',
      tamperStatus: 'Verified (Immutable hash chain intact)'
    }
  },
  {
    id: 'evt_9038',
    type: 'Reviewer Decision',
    time: '2026-10-26 20:41:09 UTC',
    dot: 'purple',
    desc: 'sub_0027 · Accepted: "Strong reasoning despite AI signal"',
    user: 'ojaswini@org.com · Override: Yes',
    details: {
      submissionId: 'sub_0027',
      modelVersion: 'text-detector-v2.4',
      hash: '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945',
      decisionRationale: 'Human reviewer determined analytical depth met top tier standard regardless of AI assistance flag.',
      tamperStatus: 'Verified'
    }
  },
  {
    id: 'evt_9032',
    type: 'Override Recorded',
    time: '2026-10-26 20:38:45 UTC',
    dot: 'orange',
    desc: 'sub_0012 · Reject → Second Review · Reason: "Inconclusive boundary signal"',
    user: 'review-lead@org.com',
    details: {
      submissionId: 'sub_0012',
      modelVersion: 'vision-engine-v3.1',
      hash: 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd309963b89b4c0ab060411a7c3',
      decisionRationale: 'Escalated to secondary senior committee due to technical complexity.',
      tamperStatus: 'Verified'
    }
  },
  {
    id: 'evt_9025',
    type: 'Model Updated',
    time: '2026-10-25 18:00:00 UTC',
    dot: 'cyan',
    desc: 'text-detector v2.3 → v2.4 · Calibration FP rate: 4.1% → 3.8%',
    user: 'System Admin · ojaswini@org.com',
    details: {
      submissionId: 'N/A (Global Model Deploy)',
      modelVersion: 'text-detector-v2.4',
      hash: 'b10a8db164e0754105b7a99be72e3fe5ec437c3523f6687a412ea0bb579c0ee9',
      decisionRationale: 'Model fine-tuned on academic writing benchmark. Decreased false positives by 0.3%.',
      tamperStatus: 'Verified'
    }
  },
  {
    id: 'evt_9018',
    type: 'Batch Export',
    time: '2026-10-25 14:22:31 UTC',
    dot: 'green',
    desc: 'Cohort: edu-2026 · Format: CSV · 1,204 records · Authorized signature',
    user: 'ojaswini@org.com',
    details: {
      submissionId: 'Cohort edu-2026',
      modelVersion: 'N/A',
      hash: 'c8f49f45d8b2e1e07354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945',
      decisionRationale: 'End-of-term grading audit dump with cryptographically signed timestamp.',
      tamperStatus: 'Verified'
    }
  },
  {
    id: 'evt_8999',
    type: 'Security Tamper Alert',
    time: '2026-10-24 09:15:10 UTC',
    dot: 'red',
    desc: 'Unauthorized query to sub_0089 encrypted score record · Blocked & Logged',
    user: 'Unknown Actor · IP: 203.0.113.42',
    details: {
      submissionId: 'sub_0089',
      modelVersion: 'N/A',
      hash: '7d793037a0760186574b0282f2f435e7b1e7a6acc941e0740006471e0849cdfe',
      decisionRationale: 'Failed API signature token validation. Request terminated immediately.',
      tamperStatus: 'Flagged Incident (Zero Data Compromise)'
    }
  }
]

export default function AuditTrail({ showToast }) {
  const [events, setEvents] = useState(initialEvents)
  const [filterType, setFilterType] = useState('all')
  const [reviewerSearch, setReviewerSearch] = useState('')
  const [selectedEvent, setSelectedEvent] = useState(null)

  const filteredEvents = events.filter(e => {
    if (filterType !== 'all' && e.type !== filterType) return false
    if (reviewerSearch.trim()) {
      const q = reviewerSearch.toLowerCase()
      if (!e.user.toLowerCase().includes(q) && !e.desc.toLowerCase().includes(q)) {
        return false
      }
    }
    return true
  })

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Audit Trail & Compliance Log</h1>
          <p className="page-subtitle">Tamper-evident, cryptographically verifiable ledger of all decisions, overrides, and model events</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="btn-secondary"
            onClick={() => showToast('Exported audit ledger with cryptographic SHA-256 proofs', 'success')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7,10 12,15 17,10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Export Ledger
          </button>
        </div>
      </div>

      <div className="audit-layout">
        {/* Filter controls */}
        <div className="card audit-filters-card">
          <h4 className="section-label">Log Filters</h4>
          
          <div className="filter-group">
            <label className="filter-label">Event Type</label>
            <select
              className="filter-select full"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="all">All Events</option>
              <option value="Submission Analyzed">Submission Analyzed</option>
              <option value="Reviewer Decision">Reviewer Decision</option>
              <option value="Override Recorded">Override Recorded</option>
              <option value="Model Updated">Model Updated</option>
              <option value="Batch Export">Batch Export</option>
              <option value="Security Tamper Alert">Security Alert</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">Reviewer / Query</label>
            <input
              type="text"
              className="filter-input full"
              placeholder="Filter by email or ID..."
              value={reviewerSearch}
              onChange={(e) => setReviewerSearch(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label className="filter-label">Integrity Verification</label>
            <div style={{ padding: '8px', background: 'var(--green-dim)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 'var(--radius-sm)', fontSize: '0.72rem', color: 'var(--green)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="pulse-dot" style={{ background: 'var(--green)' }} />
              Merkle Root: Valid
            </div>
          </div>

          <button
            className="btn-primary full-width"
            style={{ marginTop: '14px' }}
            onClick={() => {
              setFilterType('all')
              setReviewerSearch('')
              showToast('Filters reset', 'info')
            }}
          >
            Reset Filters
          </button>
        </div>

        {/* Timeline Log */}
        <div className="card audit-log-card">
          <div className="card-header">
            <h3 className="card-title">Chronological Ledger</h3>
            <span className="record-count">Showing {filteredEvents.length} of {events.length} verifiable events</span>
          </div>

          <div className="audit-timeline">
            {filteredEvents.map(evt => (
              <div
                key={evt.id}
                className="audit-event"
                onClick={() => setSelectedEvent(evt)}
              >
                <div className={`event-dot ${evt.dot}`} />
                <div className="event-body" style={{ flex: 1 }}>
                  <div className="event-header-row">
                    <span className="event-type">{evt.type}</span>
                    <span className="event-time">{evt.time}</span>
                    <span style={{ marginLeft: 'auto', fontSize: '0.65rem', color: 'var(--purple)', fontFamily: 'monospace' }}>
                      {evt.id}
                    </span>
                  </div>
                  <span className="event-desc">{evt.desc}</span>
                  <span className="event-user">{evt.user}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Event Inspector Drawer */}
          {selectedEvent && (
            <div style={{
              marginTop: '16px',
              padding: '16px',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--purple)',
              borderRadius: 'var(--radius-sm)',
              animation: 'fadeIn 0.2s ease'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                  Event Details: {selectedEvent.id} — {selectedEvent.type}
                </span>
                <button
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem' }}
                  onClick={() => setSelectedEvent(null)}
                >
                  ✕
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '8px', fontSize: '0.74rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Timestamp:</span>
                <span style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>{selectedEvent.time}</span>

                <span style={{ color: 'var(--text-muted)' }}>Actor:</span>
                <span style={{ color: 'var(--text-primary)' }}>{selectedEvent.user}</span>

                <span style={{ color: 'var(--text-muted)' }}>Model / Target:</span>
                <span style={{ color: 'var(--text-primary)' }}>{selectedEvent.details.modelVersion}</span>

                <span style={{ color: 'var(--text-muted)' }}>Tamper Check:</span>
                <span style={{ color: 'var(--green)', fontWeight: 600 }}>{selectedEvent.details.tamperStatus}</span>

                <span style={{ color: 'var(--text-muted)' }}>SHA-256 Digest:</span>
                <span style={{ color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: '0.68rem', wordBreak: 'break-all' }}>
                  {selectedEvent.details.hash}
                </span>

                <span style={{ color: 'var(--text-muted)' }}>Rationale:</span>
                <span style={{ color: 'var(--text-secondary)' }}>{selectedEvent.details.decisionRationale}</span>
              </div>
            </div>
          )}

          <div style={{ marginTop: '16px' }}>
            <div className="caveat-box">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <p>
                <strong>Audit Compliance:</strong> Every human decision override requires a non-empty rationale string. All entries are hashed sequentially into an append-only verifiable ledger to satisfy accreditation & legal standards.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
