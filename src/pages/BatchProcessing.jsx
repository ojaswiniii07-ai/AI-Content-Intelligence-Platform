import { useState } from 'react'

const initialBatches = [
  {
    id: 'b1',
    name: 'hackathon-2026-final',
    items: 84,
    source: 'CSV Upload',
    time: '2 hours ago',
    progress: 100,
    status: 'done',
    flagged: 18,
    meanConfidence: 68
  },
  {
    id: 'b2',
    name: 'eng-hiring-q4-batch',
    items: 231,
    source: 'Greenhouse API',
    time: '4 hours ago',
    progress: 78,
    status: 'running',
    flagged: 32,
    meanConfidence: 74
  },
  {
    id: 'b3',
    name: 'university-term-essays-cohort-c',
    items: 1204,
    source: 'Canvas LMS Sync',
    time: '1 day ago',
    progress: 100,
    status: 'done',
    flagged: 242,
    meanConfidence: 81
  },
  {
    id: 'b4',
    name: 'media-grant-proposals-2026',
    items: 47,
    source: 'S3 Bucket Ingest',
    time: 'Just now',
    progress: 0,
    status: 'queued',
    flagged: 0,
    meanConfidence: 0
  }
]

export default function BatchProcessing({ showToast }) {
  const [batches, setBatches] = useState(initialBatches)
  const [selectedBatch, setSelectedBatch] = useState(initialBatches[0])
  const [showModal, setShowModal] = useState(false)
  const [newBatchName, setNewBatchName] = useState('')

  const handleCreateBatch = (e) => {
    e.preventDefault()
    if (!newBatchName.trim()) {
      showToast('Please provide a cohort batch name', 'warning')
      return
    }
    const newBatch = {
      id: `b${Date.now()}`,
      name: newBatchName.trim().toLowerCase().replace(/\s+/g, '-'),
      items: 120,
      source: 'Direct Upload',
      time: 'Just now',
      progress: 5,
      status: 'running',
      flagged: 12,
      meanConfidence: 72
    }
    setBatches([newBatch, ...batches])
    setSelectedBatch(newBatch)
    setShowModal(false)
    setNewBatchName('')
    showToast(`Batch "${newBatch.name}" queued for async processing`, 'success')
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Batch Processing & Cohort Analysis</h1>
          <p className="page-subtitle">Submit, orchestrate, and audit cohort-scale submissions with aggregate distribution reports</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          + New Batch
        </button>
      </div>

      <div className="batch-layout">
        {/* Processing Queue */}
        <div className="card batch-queue-card">
          <div className="card-header">
            <h3 className="card-title">Orchestration Queue</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{batches.length} cohorts tracked</span>
          </div>

          <div className="batch-list">
            {batches.map(batch => (
              <div
                key={batch.id}
                className={`batch-item ${selectedBatch.id === batch.id ? 'active' : ''}`}
                style={{
                  cursor: 'pointer',
                  borderColor: selectedBatch.id === batch.id ? 'var(--purple)' : undefined
                }}
                onClick={() => {
                  setSelectedBatch(batch)
                  showToast(`Selected cohort report: ${batch.name}`, 'info')
                }}
              >
                <div className="batch-info">
                  <span className="batch-name">{batch.name}</span>
                  <span className="batch-meta">{batch.items} items &middot; {batch.source} &middot; {batch.time}</span>
                </div>

                <div className="batch-progress-wrap">
                  <div className="batch-progress-bar">
                    <div
                      className={`batch-fill ${batch.status}`}
                      style={{ width: `${batch.progress}%` }}
                    />
                  </div>
                  <span className="batch-pct">{batch.progress}%</span>
                </div>

                <span className={`batch-status ${batch.status}`}>
                  {batch.status === 'done' ? 'Done' : batch.status === 'running' ? 'Running' : 'Queued'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Cohort Integrity Report */}
        <div className="card batch-report-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Cohort Integrity: {selectedBatch.name}</h3>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                {selectedBatch.items} submissions analyzed
              </span>
            </div>
            <button
              className="btn-secondary small"
              onClick={() => showToast(`Exporting comprehensive cohort report for ${selectedBatch.name}`, 'success')}
            >
              Export Cohort PDF
            </button>
          </div>

          <div className="cohort-stats-row">
            <div className="cohort-stat">
              <span className="cs-val red">
                {selectedBatch.status === 'queued' ? '—' : `${((selectedBatch.flagged / selectedBatch.items) * 100).toFixed(1)}%`}
              </span>
              <span className="cs-label">Prevalence of AI Flags</span>
            </div>
            <div className="cohort-stat">
              <span className="cs-val orange">
                {selectedBatch.status === 'queued' ? '—' : selectedBatch.flagged}
              </span>
              <span className="cs-label">Flagged for Escalation</span>
            </div>
            <div className="cohort-stat">
              <span className="cs-val green">
                {selectedBatch.status === 'queued' ? '—' : `${selectedBatch.meanConfidence}%`}
              </span>
              <span className="cs-label">Mean Confidence</span>
            </div>
          </div>

          <div className="cohort-chart-area">
            <h4 className="section-label">Cohort AI Score Distribution (Histogram)</h4>
            <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', padding: '16px' }}>
              <svg viewBox="0 0 500 120" style={{ width: '100%', height: '120px' }}>
                {/* Axes */}
                <line x1="40" y1="100" x2="480" y2="100" stroke="#334155" strokeWidth="1" />
                <line x1="40" y1="20" x2="40" y2="100" stroke="#334155" strokeWidth="1" />

                {/* Histogram Bars */}
                {/* 0-20% bucket (human) */}
                <rect x="60" y="30" width="60" height="70" rx="3" fill="#10b981" fillOpacity="0.75" />
                <text x="90" y="24" fill="#10b981" fontSize="9" textAnchor="middle" fontWeight="bold">42%</text>

                {/* 20-40% bucket */}
                <rect x="140" y="55" width="60" height="45" rx="3" fill="#06b6d4" fillOpacity="0.75" />
                <text x="170" y="49" fill="#06b6d4" fontSize="9" textAnchor="middle" fontWeight="bold">26%</text>

                {/* 40-60% bucket (inconclusive) */}
                <rect x="220" y="75" width="60" height="25" rx="3" fill="#64748b" fillOpacity="0.75" />
                <text x="250" y="69" fill="#94a3b8" fontSize="9" textAnchor="middle" fontWeight="bold">12%</text>

                {/* 60-80% bucket (high signal) */}
                <rect x="300" y="70" width="60" height="30" rx="3" fill="#f97316" fillOpacity="0.75" />
                <text x="330" y="64" fill="#f97316" fontSize="9" textAnchor="middle" fontWeight="bold">13%</text>

                {/* 80-100% bucket (very high signal) */}
                <rect x="380" y="86" width="60" height="14" rx="3" fill="#ef4444" fillOpacity="0.75" />
                <text x="410" y="80" fill="#ef4444" fontSize="9" textAnchor="middle" fontWeight="bold">7%</text>

                {/* X labels */}
                <text x="90" y="112" fill="#64748b" fontSize="8" textAnchor="middle">0–20%</text>
                <text x="170" y="112" fill="#64748b" fontSize="8" textAnchor="middle">20–40%</text>
                <text x="250" y="112" fill="#64748b" fontSize="8" textAnchor="middle">40–60%</text>
                <text x="330" y="112" fill="#64748b" fontSize="8" textAnchor="middle">60–80%</text>
                <text x="410" y="112" fill="#64748b" fontSize="8" textAnchor="middle">80–100%</text>
              </svg>
              <p className="chart-caption">Bimodal distribution indicates healthy separation between authentic and AI-synthesized entries.</p>
            </div>
          </div>

          <div style={{ marginTop: '16px' }}>
            <div className="caveat-box">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <p>
                <strong>Cohort-Level Warning:</strong> Distribution spikes near 50% often suggest topic-prompt alignment or templated assignments rather than malicious fabrication. Investigate template structure prior to cohort-wide decisions.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Modal for New Batch */}
      {showModal && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="card" style={{ width: '440px', maxWidth: '90%' }}>
            <div className="card-header">
              <h3 className="card-title">Create New Batch</h3>
              <button
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}
                onClick={() => setShowModal(false)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateBatch}>
              <div className="form-group">
                <label className="form-label">Cohort Batch Name</label>
                <input
                  type="text"
                  className="filter-input full"
                  placeholder="e.g. hackathon-cohort-2026-eval"
                  value={newBatchName}
                  onChange={(e) => setNewBatchName(e.target.value)}
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label className="form-label">Source Upload</label>
                <div className="upload-zone" style={{ padding: '20px' }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17,8 12,3 7,8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  <p style={{ fontSize: '0.8rem' }}>Upload ZIP / CSV with submissions</p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '16px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Start Ingestion
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
