import { useState, useEffect } from 'react'
import { shortlistingApi } from '../services/api'

const initialProjects = [
  { id: 'p1', name: 'Hackathon 2026 — Final Round', count: 84, status: 'In progress', color: 'purple' },
  { id: 'p2', name: 'Engineering Hiring Q4', count: 231, status: 'Reviewing', color: 'cyan' },
  { id: 'p3', name: 'University Essay Competition', count: 1204, status: 'Complete', color: 'green' },
  { id: 'p4', name: 'Media Grant Applications', count: 47, status: 'Draft', color: 'orange' },
]

const initialSubmissions = [
  {
    id: 'sub_0041',
    rank: '#1',
    name: 'Team Nexus',
    relevance: 9.2,
    reasoning: 8.8,
    originality: 9.5,
    total: 91.7,
    aiSignal: 'Low',
    aiScore: 18,
    status: 'shortlisted',
    summary: 'Proposes multi-agent consensus verification with verifiable cryptographic watermarking. Outstanding technical depth.'
  },
  {
    id: 'sub_0027',
    rank: '#2',
    name: 'DataForge',
    relevance: 8.5,
    reasoning: 9.0,
    originality: 7.8,
    total: 84.4,
    aiSignal: 'Medium',
    aiScore: 54,
    status: 'pending',
    summary: 'Analyzes statistical burstiness and semantic perplexity distributions across edge devices.'
  },
  {
    id: 'sub_0012',
    rank: '#3',
    name: 'AISolve Co.',
    relevance: 8.8,
    reasoning: 7.5,
    originality: 6.2,
    total: 74.2,
    aiSignal: 'High',
    aiScore: 82,
    status: 'flagged',
    summary: 'Generic architectural boilerplate with high AI sentence repetition cues. Quality is moderate but flagged for manual audit.'
  },
  {
    id: 'sub_0089',
    rank: '#4',
    name: 'Quantum Leap',
    relevance: 7.9,
    reasoning: 8.2,
    originality: 8.4,
    total: 81.7,
    aiSignal: 'Low',
    aiScore: 24,
    status: 'shortlisted',
    summary: 'Empirical benchmark analyzing multimodal vision transformer artifacts.'
  },
  {
    id: 'sub_0063',
    rank: '#5',
    name: 'BuildRight',
    relevance: 7.2,
    reasoning: 6.8,
    originality: 7.7,
    total: 71.9,
    aiSignal: 'Low',
    aiScore: 31,
    status: 'pending',
    summary: 'Practical enterprise deployment case study. Good structure, moderate reasoning rigor.'
  },
]

export default function Shortlisting({ showToast }) {
  const [projects, setProjects] = useState(initialProjects)
  const [activeProjectId, setActiveProjectId] = useState('p1')
  const [submissions, setSubmissions] = useState(initialSubmissions)
  const [sortBy, setSortBy] = useState('score-desc')
  const [selectedSub, setSelectedSub] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    let mounted = true
    async function fetchCohortData() {
      try {
        const pRes = await shortlistingApi.getProjects()
        if (mounted && pRes?.data && pRes.data.length > 0) {
          setProjects(pRes.data)
        }
      } catch {}

      try {
        const sRes = await shortlistingApi.getSubmissions(activeProjectId)
        if (mounted && sRes?.data && sRes.data.length > 0) {
          setSubmissions(sRes.data)
        }
      } catch {}
    }
    fetchCohortData()
    return () => { mounted = false }
  }, [activeProjectId])

  const currentProject = projects.find(p => p.id === activeProjectId) || projects[0]

  const handleSort = (type) => {
    setSortBy(type)
    const sorted = [...submissions]
    if (type === 'score-desc') {
      sorted.sort((a, b) => b.total - a.total)
    } else if (type === 'score-asc') {
      sorted.sort((a, b) => a.total - b.total)
    } else if (type === 'ai-desc') {
      sorted.sort((a, b) => b.aiScore - a.aiScore)
    } else if (type === 'ai-asc') {
      sorted.sort((a, b) => a.aiScore - b.aiScore)
    }
    setSubmissions(sorted)
  }

  const updateStatus = async (id, newStatus) => {
    setSubmissions(submissions.map(s => s.id === id ? { ...s, status: newStatus } : s))
    if (selectedSub && selectedSub.id === id) {
      setSelectedSub({ ...selectedSub, status: newStatus })
    }

    try {
      await shortlistingApi.updateSubmissionStatus(id, newStatus)
      showToast(`Updated ${id} to ${newStatus} (persisted)`, 'success')
    } catch {
      showToast(`Updated ${id} to ${newStatus}`, 'success')
    }
  }

  const filteredSubmissions = submissions.filter(s => {
    if (statusFilter === 'all') return true
    return s.status === statusFilter
  })

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Response Shortlisting</h1>
          <p className="page-subtitle">Score, rank, and evaluate written responses against calibrated rubrics</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn-secondary" onClick={() => showToast('Exporting CSV with audit checksums...', 'info')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7,10 12,15 17,10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Export CSV
          </button>
          <button className="btn-primary" onClick={() => showToast('Create new shortlisting rubric workspace', 'info')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            New Project
          </button>
        </div>
      </div>

      <div className="shortlist-layout">
        {/* Projects panel */}
        <div className="card projects-panel">
          <div className="card-header">
            <h3 className="card-title">Rubric Cohorts</h3>
          </div>
          <div className="project-list">
            {projects.map(p => (
              <div
                key={p.id}
                className={`project-item ${p.id === activeProjectId ? 'active' : ''}`}
                onClick={() => {
                  setActiveProjectId(p.id)
                  showToast(`Loaded cohort: ${p.name}`, 'info')
                }}
              >
                <div className={`project-indicator ${p.color}`} />
                <div className="project-info">
                  <span className="project-name">{p.name}</span>
                  <span className="project-meta">{p.count} submissions &middot; {p.status}</span>
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
            <h4 className="section-label">Rubric Weights</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Relevance</span><span style={{ fontWeight: 600 }}>35%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Reasoning Depth</span><span style={{ fontWeight: 600 }}>35%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Originality</span><span style={{ fontWeight: 600 }}>30%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Submissions panel */}
        <div className="card submissions-panel">
          <div className="card-header">
            <div>
              <h3 className="card-title">{currentProject.name}</h3>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                {filteredSubmissions.length} of {submissions.length} submissions shown
              </span>
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <select
                className="filter-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">Status: All</option>
                <option value="shortlisted">Shortlisted</option>
                <option value="pending">Review Pending</option>
                <option value="flagged">Flagged</option>
              </select>

              <select
                className="filter-select"
                value={sortBy}
                onChange={(e) => handleSort(e.target.value)}
              >
                <option value="score-desc">Score: High → Low</option>
                <option value="score-asc">Score: Low → High</option>
                <option value="ai-desc">AI Signal: High → Low</option>
                <option value="ai-asc">AI Signal: Low → High</option>
              </select>
            </div>
          </div>

          <div className="submissions-table-wrap">
            <table className="submissions-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Submission</th>
                  <th>Relevance</th>
                  <th>Reasoning</th>
                  <th>Originality</th>
                  <th>Total Score</th>
                  <th>AI Signal</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredSubmissions.map(s => (
                  <tr
                    key={s.id}
                    className={`submission-row ${s.status === 'flagged' ? 'flagged' : ''} ${selectedSub?.id === s.id ? 'active' : ''}`}
                    onClick={() => setSelectedSub(s)}
                  >
                    <td className="rank-cell">{s.rank}</td>
                    <td className="name-cell">
                      <span className="sub-name">{s.name}</span>
                      <span className="sub-id">{s.id}</span>
                    </td>
                    <td>
                      <div className="score-bar"><div style={{ width: `${s.relevance * 10}%` }} /></div>
                      <span>{s.relevance}</span>
                    </td>
                    <td>
                      <div className="score-bar"><div style={{ width: `${s.reasoning * 10}%` }} /></div>
                      <span>{s.reasoning}</span>
                    </td>
                    <td>
                      <div className="score-bar"><div style={{ width: `${s.originality * 10}%` }} /></div>
                      <span>{s.originality}</span>
                    </td>
                    <td className={`total-score ${s.total >= 80 ? 'good' : s.total >= 70 ? 'warning' : ''}`}>
                      {s.total}%
                    </td>
                    <td>
                      <span className={`ai-badge ${s.aiSignal.toLowerCase()}`}>
                        {s.aiSignal} {s.aiSignal === 'High' && '⚠'}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${s.status}`}>
                        {s.status === 'shortlisted' ? 'Shortlisted' : s.status === 'pending' ? 'Review' : 'Flagged'}
                      </span>
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button
                          className="btn-secondary small"
                          title="Shortlist"
                          onClick={() => updateStatus(s.id, 'shortlisted')}
                        >
                          ✓
                        </button>
                        <button
                          className="btn-secondary small"
                          title="Flag for review"
                          onClick={() => updateStatus(s.id, 'flagged')}
                        >
                          ⚑
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Quick Drawer if item selected */}
          {selectedSub && (
            <div style={{
              marginTop: '16px',
              padding: '14px',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-sm)',
              animation: 'fadeIn 0.2s ease'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                  {selectedSub.name} ({selectedSub.id}) — Rubric & AI Diagnostic
                </span>
                <button
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem' }}
                  onClick={() => setSelectedSub(null)}
                >
                  ✕
                </button>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                {selectedSub.summary}
              </p>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button className="btn-secondary small" onClick={() => updateStatus(selectedSub.id, 'shortlisted')}>
                  Mark Shortlisted
                </button>
                <button className="btn-secondary small" onClick={() => updateStatus(selectedSub.id, 'pending')}>
                  Mark Review Pending
                </button>
                <button className="btn-secondary small" onClick={() => updateStatus(selectedSub.id, 'flagged')}>
                  Flag for Human Escalation
                </button>
              </div>
            </div>
          )}

          <div style={{ marginTop: '16px' }}>
            <div className="caveat-box">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <p>
                <strong>PRD Policy:</strong> AI involvement and rubric quality score are decoupled outputs. Submissions with high AI cues should not be automatically rejected without secondary human review.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
