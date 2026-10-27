import { useState, useEffect } from 'react'
import { shortlistingApi, auditApi } from '../services/api'

const initialProjects = [
  { id: 'p1', name: 'Hackathon 2026 — Final Round', count: 84, status: 'In progress', color: 'purple', rubric: 'Engineering & Architecture Rubric v2' },
  { id: 'p2', name: 'Engineering Hiring Q4', count: 231, status: 'Reviewing', color: 'cyan', rubric: 'Senior Systems Engineering Rubric' },
  { id: 'p3', name: 'University Essay Competition', count: 1204, status: 'Complete', color: 'green', rubric: 'Academic Analytical Essay Rubric v1.4' },
  { id: 'p4', name: 'Media Grant Applications', count: 47, status: 'Draft', color: 'orange', rubric: 'Investigative Media Rubric' },
]

const initialSubmissions = [
  {
    id: 'sub_0041',
    rank: '#1',
    name: 'Team Nexus',
    author: 'Elena Rostova & Dev Team',
    relevance: 9.2,
    reasoning: 8.8,
    originality: 9.5,
    total: 91.7,
    aiSignal: 'Low',
    aiScore: 18,
    status: 'shortlisted',
    summary: 'Proposes multi-agent consensus verification with verifiable cryptographic watermarking. Outstanding technical depth and empirical validation.',
    highlight: 'Sentence offsets [120–184]: High lexical diversity, low burstiness uniformity.',
  },
  {
    id: 'sub_0027',
    rank: '#2',
    name: 'DataForge AI',
    author: 'Kavita Iyer & Team',
    relevance: 8.5,
    reasoning: 9.0,
    originality: 7.8,
    total: 84.4,
    aiSignal: 'Medium',
    aiScore: 54,
    status: 'pending',
    summary: 'Analyzes statistical burstiness and semantic perplexity distributions across edge devices with robust benchmarks.',
    highlight: 'Decoupled policy: High technical rigor justifies human approval despite 54% synthetic phrasing signal.',
  },
  {
    id: 'sub_0012',
    rank: '#3',
    name: 'AISolve Co.',
    author: 'Marcus Vance',
    relevance: 8.8,
    reasoning: 7.5,
    originality: 6.2,
    total: 74.2,
    aiSignal: 'High',
    aiScore: 82,
    status: 'flagged',
    summary: 'Generic architectural boilerplate with high AI sentence repetition cues. Quality is moderate but flagged for manual reviewer audit.',
    highlight: 'Flagged for secondary human review: Boilerplate repetition exceeding 0.70 confidence threshold.',
  },
  {
    id: 'sub_0089',
    rank: '#4',
    name: 'Quantum Leap Labs',
    author: 'Dr. Aris Thorne',
    relevance: 7.9,
    reasoning: 8.2,
    originality: 8.4,
    total: 81.7,
    aiSignal: 'Low',
    aiScore: 24,
    status: 'shortlisted',
    summary: 'Empirical benchmark analyzing multimodal vision transformer artifacts and temporal video deepfake boundaries.',
    highlight: 'Verified human origin: Natural variance across all four linguistic markers.',
  },
  {
    id: 'sub_0063',
    rank: '#5',
    name: 'BuildRight Infrastructure',
    author: 'Siddharth Nair',
    relevance: 7.2,
    reasoning: 6.8,
    originality: 7.7,
    total: 71.9,
    aiSignal: 'Low',
    aiScore: 31,
    status: 'pending',
    summary: 'Practical enterprise deployment case study. Good structure, moderate reasoning rigor and clear architectural blueprints.',
    highlight: 'Low synthetic signal: Within calibrated authentic baseline.',
  },
  {
    id: 'sub_0078',
    rank: '#6',
    name: 'Sovereign Edge Labs',
    author: 'Ananya Roy',
    relevance: 8.1,
    reasoning: 8.4,
    originality: 8.6,
    total: 83.2,
    aiSignal: 'Low',
    aiScore: 21,
    status: 'shortlisted',
    summary: 'Decentralized local face localization using MTCNN PyTorch pipelines for tamper-evident biometric auditing.',
    highlight: 'Verified original work: Strong architectural novelty and zero boilerplate repetition.',
  },
]

export default function Shortlisting({ showToast }) {
  const [projects, setProjects] = useState(initialProjects)
  const [activeProjectId, setActiveProjectId] = useState('p1')
  const [submissions, setSubmissions] = useState(initialSubmissions)
  const [sortBy, setSortBy] = useState('score-desc')
  const [selectedSub, setSelectedSub] = useState(initialSubmissions[0])
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [overrideReason, setOverrideReason] = useState('')

  // Interactive Rubric Weight Customizer
  const [weights, setWeights] = useState({
    relevance: 35,
    reasoning: 35,
    originality: 30,
  })
  const [isRubricTunerOpen, setIsRubricTunerOpen] = useState(false)

  // Side-by-Side Comparison Modal
  const [comparedSubIds, setComparedSubIds] = useState([])
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false)

  // Batch Selection
  const [selectedSubIds, setSelectedSubIds] = useState([])

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
          const normalized = sRes.data.map((s, idx) => ({
            id: s.id || `sub_${idx + 1}`,
            rank: s.rank || `#${idx + 1}`,
            name: s.name || s.submission_title || `Candidate ${idx + 1}`,
            author: s.author || s.submitter || `Author ${idx + 1}`,
            relevance: Number(s.relevance ?? 8.0),
            reasoning: Number(s.reasoning ?? 8.0),
            originality: Number(s.originality ?? 8.0),
            total: Number(s.total ?? s.total_score ?? 80),
            aiSignal: s.aiSignal || s.ai_signal || 'Low',
            aiScore: Number(s.aiScore ?? s.ai_score ?? 20),
            status: s.status || 'pending',
            summary: s.summary || s.decision_rationale || 'Candidate submission evaluated against weighted rubric.',
            highlight: s.highlight || 'Decoupled evaluation active: evaluated on qualitative rubric criteria.',
          }))
          setSubmissions(normalized)
          if (normalized.length > 0) {
            setSelectedSub(normalized[0])
          }
        }
      } catch {}
    }
    fetchCohortData()
    return () => {
      mounted = false
    }
  }, [activeProjectId])

  const currentProject = projects.find((p) => p.id === activeProjectId) || projects[0]

  // Re-calculate scores dynamically based on weights
  const computeWeightedScore = (s, w) => {
    const totalW = (w.relevance + w.reasoning + w.originality) || 100
    const score = (
      (s.relevance * w.relevance + s.reasoning * w.reasoning + s.originality * w.originality) / totalW * 10
    )
    return parseFloat(score.toFixed(1))
  }

  // Handle Weight Change
  const handleWeightChange = (key, val) => {
    const num = Math.max(5, Math.min(80, parseInt(val) || 0))
    const updatedWeights = { ...weights, [key]: num }
    setWeights(updatedWeights)

    const updated = submissions.map((s) => ({
      ...s,
      total: computeWeightedScore(s, updatedWeights),
    }))

    // Sort by new scores descending
    updated.sort((a, b) => b.total - a.total)
    const reRanked = updated.map((s, idx) => ({ ...s, rank: `#${idx + 1}` }))
    setSubmissions(reRanked)
    if (selectedSub) {
      const active = reRanked.find((x) => x.id === selectedSub.id)
      if (active) setSelectedSub(active)
    }
    showToast(`Rubric weights adjusted. Cohort re-ranked dynamically.`, 'info')
  }

  const handleSort = (type) => {
    setSortBy(type)
    const sorted = [...submissions]
    if (type === 'score-desc') {
      sorted.sort((a, b) => (b.total ?? 0) - (a.total ?? 0))
    } else if (type === 'score-asc') {
      sorted.sort((a, b) => (a.total ?? 0) - (b.total ?? 0))
    } else if (type === 'ai-desc') {
      sorted.sort((a, b) => (b.aiScore ?? 0) - (a.aiScore ?? 0))
    } else if (type === 'ai-asc') {
      sorted.sort((a, b) => (a.aiScore ?? 0) - (b.aiScore ?? 0))
    } else if (type === 'orig-desc') {
      sorted.sort((a, b) => (b.originality ?? 0) - (a.originality ?? 0))
    }
    setSubmissions(sorted)
  }

  const updateStatus = async (id, newStatus) => {
    const reasonText = overrideReason.trim() || `Reviewer changed status to ${newStatus}`

    setSubmissions(
      submissions.map((s) => (s.id === id ? { ...s, status: newStatus } : s))
    )
    if (selectedSub && selectedSub.id === id) {
      setSelectedSub({ ...selectedSub, status: newStatus })
    }

    try {
      await shortlistingApi.updateSubmissionStatus(id, newStatus)
      await auditApi.recordEvent({
        action: 'SHORTLIST_STATUS_OVERRIDE',
        submission_id: id,
        decision_rationale: reasonText,
        details: { status: newStatus, reason: reasonText },
      })
    } catch {}

    setOverrideReason('')
    showToast(`Status updated to "${newStatus}" & signed into audit ledger`, 'success')
  }

  // Batch action handlers
  const handleToggleSelectSub = (id) => {
    if (selectedSubIds.includes(id)) {
      setSelectedSubIds(selectedSubIds.filter((x) => x !== id))
    } else {
      setSelectedSubIds([...selectedSubIds, id])
    }
  }

  const handleBatchStatus = async (newStatus) => {
    if (selectedSubIds.length === 0) return
    const updated = submissions.map((s) =>
      selectedSubIds.includes(s.id) ? { ...s, status: newStatus } : s
    )
    setSubmissions(updated)
    try {
      for (const id of selectedSubIds) {
        await shortlistingApi.updateSubmissionStatus(id, newStatus)
      }
      await auditApi.recordEvent({
        action: 'BATCH_SHORTLIST_STATUS_OVERRIDE',
        submission_id: selectedSubIds.join(','),
        decision_rationale: `Batch update: ${selectedSubIds.length} submissions set to ${newStatus}`,
      })
    } catch {}
    showToast(`Updated ${selectedSubIds.length} submissions to "${newStatus}"`, 'success')
    setSelectedSubIds([])
  }

  // Compare candidates toggle
  const handleToggleCompare = (id) => {
    if (comparedSubIds.includes(id)) {
      setComparedSubIds(comparedSubIds.filter((x) => x !== id))
    } else {
      if (comparedSubIds.length >= 2) {
        setComparedSubIds([comparedSubIds[1], id])
      } else {
        setComparedSubIds([...comparedSubIds, id])
      }
    }
  }

  const openCompareModal = () => {
    if (comparedSubIds.length !== 2) {
      showToast('Select 2 candidates to compare side-by-side.', 'warning')
      return
    }
    setIsCompareModalOpen(true)
  }

  // Filtered submissions
  const filteredSubmissions = submissions.filter((s) => {
    if (statusFilter !== 'all' && s.status !== statusFilter) return false
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      return (
        s.name.toLowerCase().includes(q) ||
        (s.author || '').toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q) ||
        s.summary.toLowerCase().includes(q)
      )
    }
    return true
  })

  const sub1 = submissions.find((s) => s.id === comparedSubIds[0])
  const sub2 = submissions.find((s) => s.id === comparedSubIds[1])

  return (
    <div className="shortlist-page">
      {/* ── Page Header ── */}
      <div className="page-header" style={{ marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="sarvam-eyebrow-pill" style={{ padding: '2px 8px', fontSize: '0.68rem' }}>
              DECOUPLED COHORT EVALUATION
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>· Merit-First Ranking</span>
          </div>
          <h1 className="page-title">Candidate Evaluation &amp; Shortlisting Studio</h1>
          <p className="page-subtitle">
            Merit-based rubric scoring decoupled from AI detection flags. Submissions evaluated strictly on substance.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          {comparedSubIds.length === 2 && (
            <button
              className="sarvam-btn-primary"
              onClick={openCompareModal}
              style={{ padding: '8px 14px', fontSize: '0.78rem' }}
            >
              Compare 2 Candidates (Side-by-Side)
            </button>
          )}

          <button
            className={`sarvam-btn-outline ${isRubricTunerOpen ? 'active' : ''}`}
            onClick={() => setIsRubricTunerOpen(!isRubricTunerOpen)}
            style={{ padding: '8px 14px' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="4" y1="21" x2="4" y2="14" />
              <line x1="4" y1="10" x2="4" y2="3" />
              <line x1="12" y1="21" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12" y2="3" />
              <line x1="20" y1="21" x2="20" y2="16" />
              <line x1="20" y1="12" x2="20" y2="3" />
              <line x1="1" y1="14" x2="7" y2="14" />
              <line x1="9" y1="8" x2="15" y2="8" />
              <line x1="17" y1="16" x2="23" y2="16" />
            </svg>
            <span>{isRubricTunerOpen ? 'Hide Rubric Tuner' : 'Tune Rubric Weights'}</span>
          </button>
        </div>
      </div>

      {/* ── Decoupled Policy Banner ── */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-strong)',
          borderRadius: 'var(--radius)',
          padding: '12px 18px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '1.2rem' }}>⚖️</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.82rem', color: 'var(--text-primary)' }}>
              Decoupled Assessment Policy Enforced
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              Quality scores evaluate intellectual merit, reasoning rigor, and novelty. AI involvement is tracked as an advisory signal for reviewer oversight, not an automatic disqualifier.
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="merkle-valid-pill" style={{ fontSize: '0.68rem' }}>
            <span className="pulse-dot green" />
            Human Review Required for &gt;70% AI Signal
          </span>
        </div>
      </div>

      {/* ── Interactive Rubric Tuner Drawer/Box ── */}
      {isRubricTunerOpen && (
        <div
          className="card"
          style={{
            padding: '18px 24px',
            marginBottom: '20px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--indigo)',
            animation: 'fadeIn 0.2s ease',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Live Weighted Rubric Calibrator
              </h3>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Adjusting weights immediately updates and re-ranks all {submissions.length} candidates in real-time
              </span>
            </div>
            <div style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--indigo)' }}>
              Total Weight: {weights.relevance + weights.reasoning + weights.originality}%
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '6px' }}>
                <span style={{ fontWeight: 600 }}>1. Relevance &amp; Alignment</span>
                <span style={{ fontWeight: 700, color: 'var(--indigo)' }}>{weights.relevance}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                value={weights.relevance}
                onChange={(e) => handleWeightChange('relevance', e.target.value)}
                style={{ width: '100%', accentColor: 'var(--indigo)', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Prompt fidelity &amp; scope execution</span>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '6px' }}>
                <span style={{ fontWeight: 600 }}>2. Reasoning Rigor</span>
                <span style={{ fontWeight: 700, color: 'var(--indigo)' }}>{weights.reasoning}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                value={weights.reasoning}
                onChange={(e) => handleWeightChange('reasoning', e.target.value)}
                style={{ width: '100%', accentColor: 'var(--indigo)', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Analytical depth &amp; technical validation</span>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '6px' }}>
                <span style={{ fontWeight: 600 }}>3. Originality &amp; Novelty</span>
                <span style={{ fontWeight: 700, color: 'var(--indigo)' }}>{weights.originality}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                value={weights.originality}
                onChange={(e) => handleWeightChange('originality', e.target.value)}
                style={{ width: '100%', accentColor: 'var(--indigo)', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Uniqueness &amp; anti-boilerplate cadence</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Cohort Tabs Bar ── */}
      <div className="rubric-tabs-bar" style={{ display: 'flex', gap: '8px', marginBottom: '18px', overflowX: 'auto', paddingBottom: '4px' }}>
        {projects.map((p) => (
          <button
            key={p.id}
            className={`rubric-tab-btn ${activeProjectId === p.id ? 'active' : ''}`}
            onClick={() => setActiveProjectId(p.id)}
            style={{
              padding: '10px 16px',
              borderRadius: 'var(--radius)',
              border: activeProjectId === p.id ? '1px solid var(--indigo)' : '1px solid var(--border)',
              background: activeProjectId === p.id ? 'var(--indigo-dim)' : 'var(--bg-card)',
              color: activeProjectId === p.id ? 'var(--text-primary)' : 'var(--text-secondary)',
              fontWeight: activeProjectId === p.id ? 700 : 500,
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'var(--transition)',
            }}
          >
            <span>{p.name}</span>
            <span
              style={{
                fontSize: '0.68rem',
                background: 'var(--bg-surface)',
                padding: '2px 7px',
                borderRadius: '9999px',
                border: '1px solid var(--border)',
                fontWeight: 600,
              }}
            >
              {p.count}
            </span>
          </button>
        ))}
      </div>

      {/* ── Sticky Batch Actions Bar (when items selected) ── */}
      {selectedSubIds.length > 0 && (
        <div
          style={{
            background: 'var(--text-primary)',
            color: 'var(--bg-base)',
            borderRadius: 'var(--radius)',
            padding: '10px 18px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
            boxShadow: 'var(--shadow-lg)',
            animation: 'fadeIn 0.2s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>✓ {selectedSubIds.length} candidate(s) selected</span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              style={{
                background: 'var(--emerald)',
                color: 'white',
                border: 'none',
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.74rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
              onClick={() => handleBatchStatus('shortlisted')}
            >
              Batch Shortlist
            </button>
            <button
              style={{
                background: 'var(--amber)',
                color: 'var(--bg-base)',
                border: 'none',
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.74rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
              onClick={() => handleBatchStatus('flagged')}
            >
              Batch Escalate to Oral Defense
            </button>
            <button
              style={{
                background: 'transparent',
                color: 'var(--bg-base)',
                border: '1px solid currentColor',
                padding: '6px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.74rem',
                cursor: 'pointer',
              }}
              onClick={() => setSelectedSubIds([])}
            >
              Deselect All
            </button>
          </div>
        </div>
      )}

      {/* ── Filter & Search Toolbar ── */}
      <div
        className="card"
        style={{
          padding: '12px 18px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '14px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {['all', 'shortlisted', 'pending', 'flagged'].map((st) => (
            <button
              key={st}
              className={`sample-pill ${statusFilter === st ? 'active' : ''}`}
              onClick={() => setStatusFilter(st)}
              style={{ textTransform: 'capitalize' }}
            >
              {st}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flex: 1, maxWidth: '420px' }}>
          <input
            type="text"
            className="filter-input"
            placeholder="Search candidate name, author, or summary..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: '100%', fontSize: '0.8rem' }}
          />

          <select
            className="filter-input"
            value={sortBy}
            onChange={(e) => handleSort(e.target.value)}
            style={{ fontSize: '0.78rem', minWidth: '140px' }}
          >
            <option value="score-desc">Score: High → Low</option>
            <option value="score-asc">Score: Low → High</option>
            <option value="orig-desc">Originality: Highest</option>
            <option value="ai-desc">AI Signal: Highest</option>
            <option value="ai-asc">AI Signal: Lowest</option>
          </select>
        </div>
      </div>

      {/* ── Main Layout: Table (Left) + Evaluation Drawer (Right) ── */}
      <div className="shortlist-layout" style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '22px' }}>
        {/* Table Card */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Candidate Rankings</h3>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {filteredSubmissions.length} evaluated submissions under {currentProject.rubric}
              </span>
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Select 2 to Compare
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="shortlist-table" style={{ width: '100%', fontSize: '0.8rem' }}>
              <thead>
                <tr>
                  <th style={{ width: '30px' }}>
                    <input
                      type="checkbox"
                      checked={selectedSubIds.length === filteredSubmissions.length && filteredSubmissions.length > 0}
                      onChange={(e) => {
                        if (e.target.checked) setSelectedSubIds(filteredSubmissions.map((s) => s.id))
                        else setSelectedSubIds([])
                      }}
                    />
                  </th>
                  <th>Rank &amp; Candidate</th>
                  <th>Weighted Score</th>
                  <th>AI Signal</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'center' }}>Compare</th>
                </tr>
              </thead>
              <tbody>
                {filteredSubmissions.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                      No submissions match your filter criteria.
                    </td>
                  </tr>
                ) : (
                  filteredSubmissions.map((s) => {
                    const isSelected = selectedSub?.id === s.id
                    const isChecked = selectedSubIds.includes(s.id)
                    const isCompared = comparedSubIds.includes(s.id)

                    return (
                      <tr
                        key={s.id}
                        onClick={() => setSelectedSub(s)}
                        style={{
                          cursor: 'pointer',
                          background: isSelected ? 'var(--indigo-dim)' : 'transparent',
                        }}
                      >
                        <td onClick={(e) => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleToggleSelectSub(s.id)}
                          />
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span
                              style={{
                                fontWeight: 700,
                                fontSize: '0.74rem',
                                color: 'var(--indigo)',
                                background: 'var(--bg-elevated)',
                                padding: '2px 6px',
                                borderRadius: 'var(--radius-sm)',
                              }}
                            >
                              {s.rank}
                            </span>
                            <div>
                              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.name}</div>
                              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{s.author} · {s.id}</div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontWeight: 700, fontFamily: "'Space Grotesk', sans-serif" }}>
                              {s.total}%
                            </span>
                            <div className="mini-bar" style={{ width: '60px' }}>
                              <div style={{ width: `${s.total}%` }} />
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className={`ai-badge ${s.aiScore > 70 ? 'high' : s.aiScore > 35 ? 'medium' : 'low'}`}>
                            {s.aiSignal} ({s.aiScore}%)
                          </span>
                        </td>
                        <td>
                          <span className={`status-badge ${s.status}`}>
                            {s.status}
                          </span>
                        </td>
                        <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                          <button
                            className={`btn-secondary small ${isCompared ? 'active' : ''}`}
                            style={{
                              fontSize: '0.68rem',
                              padding: '2px 8px',
                              border: isCompared ? '1px solid var(--indigo)' : '1px solid var(--border)',
                              background: isCompared ? 'var(--indigo-dim)' : 'transparent',
                            }}
                            onClick={() => handleToggleCompare(s.id)}
                            title="Compare this candidate side-by-side"
                          >
                            {isCompared ? '✓ Added' : '+ Compare'}
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Evaluation Drawer (Right Panel) */}
        <div className="card" style={{ height: 'fit-content', position: 'sticky', top: '90px' }}>
          {selectedSub ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div className="card-header" style={{ padding: 0, borderBottom: 'none' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="rubric-badge">{selectedSub.rank} Ranked</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {selectedSub.id}
                    </span>
                  </div>
                  <h3 style={{ margin: '4px 0 0', fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {selectedSub.name}
                  </h3>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    Lead: {selectedSub.author}
                  </span>
                </div>

                <span className={`status-badge ${selectedSub.status}`}>
                  {selectedSub.status}
                </span>
              </div>

              {/* Score Highlights */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div className="stat-card" style={{ padding: '12px' }}>
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Weighted Merit Score</span>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {selectedSub.total}%
                  </div>
                </div>

                <div className="stat-card" style={{ padding: '12px' }}>
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>AI Detection Signal</span>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, marginTop: '4px' }}>
                    <span className={`ai-badge ${selectedSub.aiScore > 70 ? 'high' : selectedSub.aiScore > 35 ? 'medium' : 'low'}`}>
                      {selectedSub.aiSignal} ({selectedSub.aiScore}%)
                    </span>
                  </div>
                </div>
              </div>

              {/* Rubric Criteria Breakdown */}
              <div style={{ padding: '14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>
                  Rubric Criteria Weights &amp; Scores
                </span>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', marginBottom: '3px' }}>
                      <span>Relevance ({weights.relevance}%)</span>
                      <span style={{ fontWeight: 700 }}>{selectedSub.relevance}/10</span>
                    </div>
                    <div className="mini-bar"><div style={{ width: `${selectedSub.relevance * 10}%` }} /></div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', marginBottom: '3px' }}>
                      <span>Reasoning Rigor ({weights.reasoning}%)</span>
                      <span style={{ fontWeight: 700 }}>{selectedSub.reasoning}/10</span>
                    </div>
                    <div className="mini-bar"><div style={{ width: `${selectedSub.reasoning * 10}%` }} /></div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', marginBottom: '3px' }}>
                      <span>Originality &amp; Novelty ({weights.originality}%)</span>
                      <span style={{ fontWeight: 700 }}>{selectedSub.originality}/10</span>
                    </div>
                    <div className="mini-bar"><div style={{ width: `${selectedSub.originality * 10}%` }} /></div>
                  </div>
                </div>
              </div>

              {/* Qualitative Summary */}
              <div>
                <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Executive Evaluation Summary
                </span>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.55, marginTop: '4px' }}>
                  {selectedSub.summary}
                </p>
              </div>

              {/* Reviewer Override / Action Box */}
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '14px' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>
                  Record Official Reviewer Decision:
                </span>

                <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                  <button
                    className="sarvam-btn-primary"
                    style={{ flex: 1, padding: '8px 10px', fontSize: '0.74rem', justifyContent: 'center' }}
                    onClick={() => updateStatus(selectedSub.id, 'shortlisted')}
                  >
                    ✓ Shortlist
                  </button>
                  <button
                    className="sarvam-btn-outline"
                    style={{ flex: 1, padding: '8px 10px', fontSize: '0.74rem', justifyContent: 'center' }}
                    onClick={() => updateStatus(selectedSub.id, 'flagged')}
                  >
                    ⚠ Flag for Review
                  </button>
                  <button
                    className="btn-secondary"
                    style={{ flex: 1, padding: '8px 10px', fontSize: '0.74rem', justifyContent: 'center', color: 'var(--rose)' }}
                    onClick={() => updateStatus(selectedSub.id, 'rejected')}
                  >
                    ✕ Reject
                  </button>
                </div>

                <input
                  type="text"
                  className="filter-input"
                  placeholder="Optional rationale signed to SHA-256 ledger..."
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  style={{ width: '100%', fontSize: '0.76rem', marginBottom: '6px' }}
                />

                {/* Quick rationale templates */}
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  {[
                    'Exceptional technical novelty verified.',
                    'AI tool usage verified as auxiliary research.',
                    'Flagged for 10-minute technical oral defense.',
                  ].map((tmpl, idx) => (
                    <button
                      key={idx}
                      className="sample-pill"
                      style={{ fontSize: '0.64rem', padding: '2px 6px' }}
                      onClick={() => setOverrideReason(tmpl)}
                    >
                      + {tmpl}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              Select a candidate from the table to view detailed rubric metrics.
            </div>
          )}
        </div>
      </div>

      {/* ── Side-by-Side Comparison Modal ── */}
      {isCompareModalOpen && sub1 && sub2 && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.45)',
            backdropFilter: 'blur(5px)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
          }}
          onClick={() => setIsCompareModalOpen(false)}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '820px',
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-xl)',
              border: '1px solid var(--border-strong)',
              boxShadow: 'var(--shadow-xl)',
              padding: '28px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Side-by-Side Candidate Rubric Comparison
                </h3>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Direct empirical comparison evaluated under {currentProject.rubric}
                </span>
              </div>
              <button
                className="btn-secondary small"
                onClick={() => setIsCompareModalOpen(false)}
                style={{ borderRadius: '50%', width: '28px', height: '28px', padding: 0 }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              {/* Candidate 1 */}
              <div style={{ padding: '18px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <span className="rubric-badge" style={{ marginBottom: '6px', display: 'inline-block' }}>
                  {sub1.rank} Ranked
                </span>
                <h4 style={{ margin: '0 0 2px', fontSize: '1.05rem', color: 'var(--text-primary)' }}>{sub1.name}</h4>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{sub1.author}</span>

                <div style={{ margin: '14px 0', fontSize: '1.6rem', fontWeight: 700, color: 'var(--indigo)' }}>
                  {sub1.total}% <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Merit Score</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.75rem' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Relevance:</span>
                      <span style={{ fontWeight: 600 }}>{sub1.relevance}/10</span>
                    </div>
                    <div className="mini-bar"><div style={{ width: `${sub1.relevance * 10}%` }} /></div>
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Reasoning:</span>
                      <span style={{ fontWeight: 600 }}>{sub1.reasoning}/10</span>
                    </div>
                    <div className="mini-bar"><div style={{ width: `${sub1.reasoning * 10}%` }} /></div>
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Originality:</span>
                      <span style={{ fontWeight: 600 }}>{sub1.originality}/10</span>
                    </div>
                    <div className="mini-bar"><div style={{ width: `${sub1.originality * 10}%` }} /></div>
                  </div>
                </div>

                <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>AI Involvement:</span>
                  <div style={{ marginTop: '4px' }}>
                    <span className={`ai-badge ${sub1.aiScore > 70 ? 'high' : 'low'}`}>
                      {sub1.aiSignal} ({sub1.aiScore}%)
                    </span>
                  </div>
                </div>
              </div>

              {/* Candidate 2 */}
              <div style={{ padding: '18px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <span className="rubric-badge" style={{ marginBottom: '6px', display: 'inline-block' }}>
                  {sub2.rank} Ranked
                </span>
                <h4 style={{ margin: '0 0 2px', fontSize: '1.05rem', color: 'var(--text-primary)' }}>{sub2.name}</h4>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{sub2.author}</span>

                <div style={{ margin: '14px 0', fontSize: '1.6rem', fontWeight: 700, color: 'var(--indigo)' }}>
                  {sub2.total}% <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Merit Score</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.75rem' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Relevance:</span>
                      <span style={{ fontWeight: 600 }}>{sub2.relevance}/10</span>
                    </div>
                    <div className="mini-bar"><div style={{ width: `${sub2.relevance * 10}%` }} /></div>
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Reasoning:</span>
                      <span style={{ fontWeight: 600 }}>{sub2.reasoning}/10</span>
                    </div>
                    <div className="mini-bar"><div style={{ width: `${sub2.reasoning * 10}%` }} /></div>
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Originality:</span>
                      <span style={{ fontWeight: 600 }}>{sub2.originality}/10</span>
                    </div>
                    <div className="mini-bar"><div style={{ width: `${sub2.originality * 10}%` }} /></div>
                  </div>
                </div>

                <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>AI Involvement:</span>
                  <div style={{ marginTop: '4px' }}>
                    <span className={`ai-badge ${sub2.aiScore > 70 ? 'high' : 'low'}`}>
                      {sub2.aiSignal} ({sub2.aiScore}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Delta Analysis */}
            <div
              style={{
                marginTop: '20px',
                padding: '12px 16px',
                background: 'var(--bg-surface)',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border)',
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.76rem',
              }}
            >
              <span>
                <strong>Score Delta:</strong> {Math.abs(sub1.total - sub2.total).toFixed(1)}% advantage to{' '}
                <strong>{sub1.total >= sub2.total ? sub1.name : sub2.name}</strong>
              </span>
              <span>
                <strong>Originality Leader:</strong>{' '}
                {sub1.originality >= sub2.originality ? `${sub1.name} (${sub1.originality}/10)` : `${sub2.name} (${sub2.originality}/10)`}
              </span>
            </div>

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="sarvam-btn-primary"
                onClick={() => setIsCompareModalOpen(false)}
              >
                Done Reviewing
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
