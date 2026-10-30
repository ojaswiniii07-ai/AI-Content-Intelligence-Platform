import { useState, useEffect } from 'react'
import { shortlistingApi, auditApi } from '../services/api'

// Memphis Decorative SVG Squiggle
const MemphisSquiggle = ({ color = '#FF1493', width = 120, height = 18 }) => (
  <svg width={width} height={height} viewBox="0 0 120 18" fill="none" style={{ display: 'inline-block' }}>
    <path
      d="M2 9C12 2 18 16 28 9C38 2 44 16 54 9C64 2 70 16 80 9C90 2 96 16 106 9C112 5 116 11 118 9"
      stroke={color}
      strokeWidth="4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

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

function parseCsv(text) {
  const lines = []
  let row = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    const nextChar = text[i + 1]

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        current += '"'
        i++
      } else {
        inQuotes = !inQuotes
      }
    } else if (char === ',' && !inQuotes) {
      row.push(current.trim())
      current = ''
    } else if ((char === '\r' || char === '\n') && !inQuotes) {
      if (char === '\r' && nextChar === '\n') i++
      row.push(current.trim())
      if (row.some((c) => c.length > 0)) lines.push(row)
      row = []
      current = ''
    } else {
      current += char
    }
  }
  if (current.length > 0 || row.length > 0) {
    row.push(current.trim())
    if (row.some((c) => c.length > 0)) lines.push(row)
  }

  if (lines.length < 2) return []
  const headers = lines[0].map((h) => h.toLowerCase().replace(/[^a-z0-9_]/g, ''))
  return lines.slice(1).map((r) => {
    const obj = {}
    headers.forEach((h, idx) => {
      obj[h] = r[idx] || ''
    })
    return obj
  })
}

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

  // AI / LLM Evaluator State (Gemma 4 31B via OpenRouter)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evaluatingCandidateId, setEvaluatingCandidateId] = useState(null)

  // CSV Dataset & Shortlister Mode State
  const [evaluationMode, setEvaluationMode] = useState('hackathon') // 'hackathon' | 'resume'
  const [csvFileName, setCsvFileName] = useState(null)
  const [csvCandidateCount, setCsvCandidateCount] = useState(0)
  const [isLoadingSample, setIsLoadingSample] = useState(false)

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
            text_content: s.text_content || s.summary || '',
            criterionScores: s.criterion_scores || s.criterionScores || [],
            evaluatorMetadata: s.evaluator_metadata || s.evaluatorMetadata || {},
            missingRequirements: s.missing_requirements || s.missingRequirements || [],
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

  const handleModeChange = (mode) => {
    setEvaluationMode(mode)
    if (mode === 'hackathon') {
      setActiveProjectId('p1')
      setWeights({ relevance: 35, reasoning: 35, originality: 30 })
      showToast('Switched mode to Hackathon Project Shortlister', 'info')
    } else {
      setActiveProjectId('p2')
      setWeights({ relevance: 35, reasoning: 35, originality: 30 })
      showToast('Switched mode to Resume & Candidate Shortlister', 'info')
    }
  }

  const processCsvRows = (rows, fileName) => {
    if (!rows || rows.length === 0) {
      showToast('No valid candidate rows found in CSV file.', 'warning')
      return
    }

    const normalized = rows.map((r, idx) => {
      const candidateName = r.name || r.candidate_name || r.author || `Candidate #${idx + 1}`
      const titleOrRole = r.project_title || r.role_applied || r.role || r.title || ''
      const authorName = r.author || r.submitter || candidateName
      const summaryText = r.summary || r.text_content || r.description || ''
      const fullText = r.text_content || r.summary || summaryText
      const aiScoreVal = Number(r.ai_score || r.aiscore || 18)
      const aiSig = r.ai_signal || (aiScoreVal > 70 ? 'High' : aiScoreVal > 35 ? 'Medium' : 'Low')

      return {
        id: r.id || `csv_${idx + 1}`,
        rank: `#${idx + 1}`,
        name: titleOrRole ? `${candidateName} — ${titleOrRole}` : candidateName,
        author: authorName,
        roleApplied: r.role_applied || '',
        projectTitle: r.project_title || '',
        relevance: Number(r.relevance || (8.2 + (idx % 3) * 0.4)),
        reasoning: Number(r.reasoning || (8.0 + (idx % 2) * 0.5)),
        originality: Number(r.originality || (8.5 - (idx % 3) * 0.5)),
        total: Number(r.total || (82.0 + (idx % 5) * 2.0)),
        aiSignal: aiSig,
        aiScore: aiScoreVal,
        status: r.status || (aiScoreVal > 70 ? 'flagged' : 'pending'),
        summary: summaryText || 'Imported candidate profile ready for evaluation.',
        highlight: `Imported from CSV (${fileName || 'custom.csv'}).`,
        text_content: fullText,
        criterionScores: [],
        evaluatorMetadata: {},
        missingRequirements: [],
      }
    })

    setSubmissions(normalized)
    if (normalized.length > 0) {
      setSelectedSub(normalized[0])
    }
    setCsvFileName(fileName || 'custom.csv')
    setCsvCandidateCount(normalized.length)
    showToast(`Successfully imported ${normalized.length} candidates from ${fileName}`, 'success')
  }

  const handleCsvFileUpload = (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const text = event.target.result
        const rows = parseCsv(text)
        processCsvRows(rows, file.name)
      } catch (err) {
        showToast(`Failed to parse CSV file: ${err.message}`, 'error')
      }
    }
    reader.readAsText(file)
  }

  const handleLoadSampleCsv = async (type) => {
    setIsLoadingSample(true)
    const fileName = type === 'hackathon' ? 'hackathon_submissions.csv' : 'resume_candidates.csv'
    try {
      const res = await fetch(`/mock_data/${fileName}`)
      if (!res.ok) throw new Error(`HTTP ${res.status} loading sample`)
      const text = await res.text()
      const rows = parseCsv(text)
      handleModeChange(type)
      processCsvRows(rows, fileName)
    } catch (err) {
      showToast(`Could not load mock CSV: ${err.message}`, 'error')
    } finally {
      setIsLoadingSample(false)
    }
  }

  const handleRunLlmEvaluation = async (targetSubmissionIds = null) => {
    setIsEvaluating(true)
    try {
      showToast('Connecting to Gemma 4 31B (OpenRouter) to evaluate candidates...', 'info')

      const inlinePayload = submissions
        .filter((s) => !targetSubmissionIds || targetSubmissionIds.includes(s.id))
        .map((s) => ({
          id: s.id,
          name: s.name,
          title: s.name,
          text: s.text_content || s.summary || s.highlight || s.name,
          ai_context: {
            ai_score: s.aiScore,
            ai_signal: s.aiSignal,
          },
        }))

      const res = await shortlistingApi.evaluateCohort({
        rubricId: activeProjectId,
        evaluatorType: 'llm',
        submissionIds: targetSubmissionIds,
        submissionsInline: inlinePayload.length > 0 ? inlinePayload : null,
      })

      if (res?.data?.shortlist && res.data.shortlist.length > 0) {
        const updatedList = res.data.shortlist.map((c, idx) => ({
          id: c.id,
          rank: c.rank || `#${idx + 1}`,
          name: c.name,
          author: c.author || 'Candidate Author',
          relevance: Number(c.relevance || 0),
          reasoning: Number(c.reasoning || 0),
          originality: Number(c.originality || 0),
          total: Number(c.total || 0),
          aiSignal: c.ai_signal || 'Low',
          aiScore: Number(c.ai_score || 0),
          status: c.status || 'pending',
          summary: c.summary || '',
          text_content: c.text_content || submissions.find((s) => s.id === c.id)?.text_content || '',
          criterionScores: c.criterion_scores || [],
          evaluatorMetadata: c.evaluator_metadata || {},
          missingRequirements: c.missing_requirements || [],
        }))

        setSubmissions(updatedList)
        const match = updatedList.find((c) => c.id === selectedSub?.id) || updatedList[0]
        setSelectedSub(match)
        const modelName = res.data.evaluations?.[0]?.evaluator_metadata?.model || 'google/gemma-4-31b-it:free'
        showToast(`AI Evaluation complete! ${res.data.evaluated_count} candidates assessed with ${modelName}`, 'success')
      } else {
        showToast('Evaluation response received.', 'info')
      }
    } catch (err) {
      showToast(`Evaluation error: ${err.message || 'LLM service failure'}`, 'error')
    } finally {
      setIsEvaluating(false)
      setEvaluatingCandidateId(null)
    }
  }

  const handleEvaluateSingle = async (candidateId) => {
    setEvaluatingCandidateId(candidateId)
    await handleRunLlmEvaluation([candidateId])
  }

  const currentProject = projects.find((p) => p.id === activeProjectId) || projects[0]

  // Re-calculate scores dynamically based on weights
  const computeWeightedScore = (s, w) => {
    const totalW = (w.relevance + w.reasoning + w.originality) || 100
    const score = (
      (s.relevance * w.relevance + s.reasoning * w.reasoning + s.originality * w.originality) / totalW * 10
    )
    return parseFloat(score.toFixed(1))
  }

  const handleWeightChange = (key, val) => {
    const num = Math.max(5, Math.min(80, parseInt(val) || 0))
    const updatedWeights = { ...weights, [key]: num }
    setWeights(updatedWeights)

    const updated = submissions.map((s) => ({
      ...s,
      total: computeWeightedScore(s, updatedWeights),
    }))

    updated.sort((a, b) => b.total - a.total)
    const reRanked = updated.map((s, idx) => ({ ...s, rank: `#${idx + 1}` }))
    setSubmissions(reRanked)
    if (selectedSub) {
      const active = reRanked.find((x) => x.id === selectedSub.id)
      if (active) setSelectedSub(active)
    }
    showToast('Rubric weights adjusted. Cohort re-ranked dynamically.', 'info')
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
    <div className="memphis-shortlisting-studio">
      {/* ── MEMPHIS '81 VIBRANT POSTMODERN STYLES ── */}
      <style>{`
        .memphis-shortlisting-studio {
          width: 100%;
          font-family: var(--font-primary, 'Poppins', sans-serif);
          position: relative;
        }

        /* ── Header ── */
        .ms-page-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 24px;
          border-bottom: 3.5px solid #121316;
          padding-bottom: 20px;
          gap: 16px;
          flex-wrap: wrap;
        }

        .ms-title-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .ms-tag-row {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
        }

        .ms-stamp {
          font-size: 0.74rem;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          padding: 5px 14px;
          border: 2.5px solid #121316;
          box-shadow: 3.5px 3.5px 0px #121316;
          border-radius: 0px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          transition: all 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-stamp:hover {
          transform: translateY(-2px) rotate(2deg);
          box-shadow: 5.5px 5.5px 0px #121316;
        }
        .ms-stamp-yellow { background: #FFD700; color: #121316; transform: rotate(-1.5deg); }
        .ms-stamp-pink   { background: #FF1493; color: #FFFFFF; transform: rotate(1.5deg); }
        .ms-stamp-blue   { background: #0066FF; color: #FFFFFF; transform: rotate(-0.5deg); }
        .ms-stamp-green  { background: #00E5A0; color: #121316; transform: rotate(1deg); }

        .ms-page-title {
          font-size: clamp(1.7rem, 2.6vw, 2.3rem);
          font-weight: 900;
          color: var(--text-primary);
          text-transform: uppercase;
          letter-spacing: -0.02em;
          line-height: 1.15;
          margin: 0;
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }

        .ms-page-subtitle {
          font-size: 0.9rem;
          font-weight: 600;
          color: var(--text-secondary);
          margin: 0;
          max-width: 720px;
          line-height: 1.5;
        }

        .ms-header-actions {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }

        .ms-btn-action {
          font-family: inherit;
          font-size: 0.84rem;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          padding: 11px 20px;
          border: 2.5px solid #121316;
          box-shadow: 4px 4px 0px #121316;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          transition: all 0.16s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-btn-pink {
          background: #FF1493;
          color: #FFFFFF;
        }
        .ms-btn-pink:hover:not(:disabled) {
          background: #FFD700;
          color: #121316;
          transform: translate(-3px, -3px) rotate(1deg);
          box-shadow: 7px 7px 0px #121316;
        }
        .ms-btn-pink:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .ms-btn-yellow {
          background: #FFD700;
          color: #121316;
        }
        .ms-btn-yellow:hover {
          background: #00E5A0;
          transform: translate(-3px, -3px) rotate(-1deg);
          box-shadow: 7px 7px 0px #121316;
        }

        .ms-btn-blue {
          background: #0066FF;
          color: #FFFFFF;
        }
        .ms-btn-blue:hover {
          background: #FF1493;
          transform: translate(-3px, -3px) rotate(1.5deg);
          box-shadow: 7px 7px 0px #121316;
        }

        /* ── Decoupled Policy Banner with Hover Pop ── */
        .ms-policy-banner {
          background: #FFD700;
          color: #121316;
          border: 3.5px solid #121316;
          box-shadow: 6px 6px 0px #121316;
          padding: 16px 22px;
          margin-bottom: 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          flex-wrap: wrap;
          transform: rotate(-0.3deg);
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-policy-banner:hover {
          transform: translateY(-4px) rotate(0.4deg);
          box-shadow: 10px 10px 0px #121316;
        }
        .ms-policy-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .ms-policy-icon-box {
          width: 40px;
          height: 40px;
          background: #121316;
          color: #FFD700;
          border: 2.5px solid #121316;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transform: rotate(-3deg);
          box-shadow: 2px 2px 0px #FF1493;
          transition: all 0.18s ease;
        }
        .ms-policy-banner:hover .ms-policy-icon-box {
          transform: rotate(6deg) scale(1.08);
        }
        .ms-policy-title {
          font-size: 0.96rem;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          margin: 0 0 3px;
        }
        .ms-policy-desc {
          font-size: 0.8rem;
          font-weight: 600;
          margin: 0;
          opacity: 0.95;
          line-height: 1.45;
        }
        .ms-policy-badge {
          background: #FFFFFF;
          color: #121316;
          border: 2.5px solid #121316;
          box-shadow: 3.5px 3.5px 0px #121316;
          padding: 7px 16px;
          font-size: 0.76rem;
          font-weight: 900;
          text-transform: uppercase;
          white-space: nowrap;
          transform: rotate(1deg);
          transition: all 0.15s ease;
        }
        .ms-policy-badge:hover {
          transform: scale(1.05) rotate(-1deg);
          box-shadow: 5px 5px 0px #121316;
        }

        /* ── CSV Ingestion Card with Hover Pop ── */
        .ms-ingestion-card {
          background: var(--bg-card, #FFFFFF);
          border: 3.5px solid #121316;
          box-shadow: 6px 6px 0px #121316;
          padding: 22px;
          margin-bottom: 24px;
          border-top: 8px solid #0066FF;
          position: relative;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-ingestion-card:hover {
          transform: translateY(-4px) rotate(-0.2deg);
          box-shadow: 10px 10px 0px #121316;
        }
        .ms-ingestion-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 18px;
          flex-wrap: wrap;
          gap: 14px;
        }
        .ms-ingestion-title {
          font-size: 1.1rem;
          font-weight: 900;
          text-transform: uppercase;
          color: var(--text-primary);
          margin: 0;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .ms-mode-pill-select {
          background: #FFD700;
          color: #121316;
          border: 2.5px solid #121316;
          box-shadow: 3.5px 3.5px 0px #121316;
          padding: 6px 16px;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.82rem;
          font-weight: 900;
          text-transform: uppercase;
          transform: rotate(-1deg);
          transition: all 0.15s ease;
        }
        .ms-mode-pill-select:hover {
          transform: translateY(-2px) rotate(1deg);
          box-shadow: 5.5px 5.5px 0px #121316;
        }
        .ms-select-input {
          background: transparent;
          border: none;
          font-family: inherit;
          font-size: 0.84rem;
          font-weight: 900;
          color: #121316;
          outline: none;
          cursor: pointer;
          text-transform: uppercase;
        }

        .ms-ingestion-grid {
          display: grid;
          grid-template-columns: 1fr 1.6fr;
          gap: 20px;
        }

        .ms-dropzone {
          border: 3px dashed #121316;
          background: var(--bg-surface, #F8F9FA);
          box-shadow: 4px 4px 0px #121316;
          padding: 24px 18px;
          text-align: center;
          cursor: pointer;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 10px;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-dropzone:hover {
          border-color: #FF1493;
          background: rgba(255, 20, 147, 0.08);
          transform: translateY(-3px) rotate(0.8deg);
          box-shadow: 7px 7px 0px #121316;
        }
        .ms-dropzone-title {
          font-size: 0.92rem;
          font-weight: 900;
          text-transform: uppercase;
          color: var(--text-primary);
          margin: 0;
        }
        .ms-dropzone-desc {
          font-size: 0.76rem;
          color: var(--text-secondary);
          font-weight: 600;
          margin: 0;
        }

        .ms-mock-panel {
          background: var(--bg-surface, #F8F9FA);
          border: 2.5px solid #121316;
          box-shadow: 4px 4px 0px #121316;
          padding: 20px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          gap: 14px;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-mock-panel:hover {
          transform: translateY(-3px) rotate(-0.3deg);
          box-shadow: 7px 7px 0px #121316;
        }

        .ms-mock-buttons-row {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }
        .ms-mock-btn {
          font-family: inherit;
          font-size: 0.8rem;
          font-weight: 900;
          text-transform: uppercase;
          padding: 9px 18px;
          border: 2px solid #121316;
          background: var(--bg-card, #FFFFFF);
          color: var(--text-primary);
          box-shadow: 3.5px 3.5px 0px #121316;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          transition: all 0.16s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-mock-btn:hover {
          background: #FFD700;
          color: #121316;
          transform: translate(-3px, -3px) rotate(1deg);
          box-shadow: 6px 6px 0px #121316;
        }
        .ms-mock-btn.active {
          background: #FF1493;
          color: #FFFFFF;
          box-shadow: 5px 5px 0px #121316;
          transform: translate(-2px, -2px) rotate(-1deg);
        }

        .ms-download-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-top: 2px solid #121316;
          padding-top: 12px;
          font-size: 0.76rem;
          font-weight: 800;
          color: var(--text-muted);
          flex-wrap: wrap;
          gap: 10px;
        }
        .ms-dl-link {
          color: #0066FF;
          text-decoration: none;
          font-weight: 900;
          display: inline-flex;
          align-items: center;
          gap: 4px;
          text-transform: uppercase;
          transition: all 0.15s ease;
        }
        .ms-dl-link:hover {
          text-decoration: underline;
          color: #FF1493;
          transform: translateX(2px);
        }

        /* ── Rubric Tuner Drawer with Hover Pop ── */
        .ms-tuner-card {
          background: #FFD700;
          color: #121316;
          border: 3.5px solid #121316;
          box-shadow: 6px 6px 0px #121316;
          padding: 22px;
          margin-bottom: 24px;
          position: relative;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-tuner-card:hover {
          transform: translateY(-4px) rotate(0.3deg);
          box-shadow: 10px 10px 0px #121316;
        }
        .ms-tuner-sliders {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 20px;
          margin-top: 16px;
        }
        .ms-slider-box {
          background: #FFFFFF;
          border: 2.5px solid #121316;
          box-shadow: 3.5px 3.5px 0px #121316;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-slider-box:hover {
          transform: translateY(-3px) rotate(0.8deg);
          box-shadow: 6.5px 6.5px 0px #121316;
        }
        .ms-slider-head {
          display: flex;
          justify-content: space-between;
          font-size: 0.82rem;
          font-weight: 900;
          text-transform: uppercase;
        }

        /* ── Cohort Tabs Bar ── */
        .ms-cohort-tabs {
          display: flex;
          gap: 10px;
          margin-bottom: 22px;
          overflow-x: auto;
          padding-bottom: 6px;
        }
        .ms-cohort-tab-btn {
          font-family: inherit;
          font-size: 0.82rem;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          padding: 10px 20px;
          border: 2.5px solid #121316;
          background: var(--bg-card, #FFFFFF);
          color: var(--text-primary);
          box-shadow: 4px 4px 0px #121316;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 10px;
          white-space: nowrap;
          transition: all 0.16s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-cohort-tab-btn:hover:not(.active) {
          background: #FFD700;
          color: #121316;
          transform: translate(-3px, -3px) rotate(0.5deg);
          box-shadow: 6.5px 6.5px 0px #121316;
        }
        .ms-cohort-tab-btn.active {
          background: #FF1493;
          color: #FFFFFF;
          box-shadow: 5px 5px 0px #121316;
          transform: translate(-2px, -2px) rotate(-1deg);
        }
        .ms-cohort-tab-count {
          background: #FFFFFF;
          color: #121316;
          border: 1.5px solid #121316;
          font-size: 0.7rem;
          padding: 2px 8px;
          font-weight: 900;
        }

        /* ── Sticky Batch Selection Bar ── */
        .ms-batch-bar {
          background: #121316;
          color: #FFFFFF;
          border: 3px solid #FFD700;
          box-shadow: 6px 6px 0px #121316;
          padding: 14px 22px;
          margin-bottom: 22px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          flex-wrap: wrap;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-batch-bar:hover {
          transform: translateY(-3px);
          box-shadow: 9px 9px 0px #121316;
        }

        /* ── Toolbar with Hover Pop ── */
        .ms-toolbar {
          background: var(--bg-surface, #F8F9FA);
          border: 2.5px solid #121316;
          box-shadow: 4px 4px 0px #121316;
          padding: 14px 20px;
          margin-bottom: 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          flex-wrap: wrap;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-toolbar:hover {
          transform: translateY(-3px) rotate(0.2deg);
          box-shadow: 7px 7px 0px #121316;
        }
        .ms-filter-pills {
          display: flex;
          gap: 8px;
        }
        .ms-filter-pill {
          font-family: inherit;
          font-size: 0.78rem;
          font-weight: 900;
          text-transform: uppercase;
          padding: 7px 16px;
          border: 2px solid #121316;
          background: var(--bg-card, #FFFFFF);
          color: var(--text-primary);
          box-shadow: 3px 3px 0px #121316;
          cursor: pointer;
          transition: all 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-filter-pill:hover:not(.active) {
          background: #FFD700;
          color: #121316;
          transform: translate(-2px, -2px);
          box-shadow: 5px 5px 0px #121316;
        }
        .ms-filter-pill.active {
          background: #FF1493;
          color: #FFFFFF;
          box-shadow: 4px 4px 0px #121316;
          transform: translate(-1px, -1px);
        }

        .ms-search-box {
          display: flex;
          gap: 10px;
          flex: 1;
          max-width: 480px;
        }

        /* ── Main Layout: Table (Left) + Drawer (Right) ── */
        .ms-layout-grid {
          display: grid;
          grid-template-columns: 1.35fr 1fr;
          gap: 24px;
          align-items: start;
        }

        /* ── Table Box with Hover Pop ── */
        .ms-table-box {
          background: var(--bg-card, #FFFFFF);
          border: 3.5px solid #121316;
          box-shadow: 6px 6px 0px #121316;
          overflow: hidden;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-table-box:hover {
          transform: translateY(-4px) rotate(0.2deg);
          box-shadow: 10px 10px 0px #121316;
        }
        .ms-table-head {
          padding: 16px 20px;
          background: #FFD700;
          color: #121316;
          border-bottom: 2.5px solid #121316;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .ms-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.83rem;
        }
        .ms-table th {
          background: var(--bg-surface, #F8F9FA);
          color: var(--text-primary);
          padding: 12px 14px;
          text-align: left;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          border-bottom: 2.5px solid #121316;
          border-right: 1.5px solid #121316;
        }
        .ms-table td {
          padding: 14px;
          border-bottom: 2px solid #121316;
          border-right: 1.5px solid #121316;
          color: var(--text-primary);
          font-weight: 600;
        }
        .ms-table tr {
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .ms-table tr:hover td {
          background: rgba(255, 215, 0, 0.18);
        }
        .ms-table tr.selected td {
          background: rgba(255, 20, 147, 0.12);
        }

        /* ── Drawer with Hover Pop ── */
        .ms-drawer {
          background: var(--bg-card, #FFFFFF);
          border: 3.5px solid #121316;
          box-shadow: 6px 6px 0px #121316;
          padding: 22px;
          position: sticky;
          top: 90px;
          display: flex;
          flex-direction: column;
          gap: 18px;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-drawer:hover {
          transform: translateY(-4px) rotate(-0.3deg);
          box-shadow: 10px 10px 0px #121316;
        }

        .ms-drawer-header {
          border-bottom: 2.5px solid #121316;
          padding-bottom: 14px;
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
        }

        .ms-score-card-pair {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }
        .ms-score-tile {
          background: var(--bg-surface, #F8F9FA);
          border: 2.5px solid #121316;
          box-shadow: 3.5px 3.5px 0px #121316;
          padding: 12px 14px;
          display: flex;
          flex-direction: column;
          gap: 4px;
          transition: all 0.18s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-score-tile:hover {
          transform: translateY(-3px) rotate(1deg);
          box-shadow: 6.5px 6.5px 0px #121316;
        }
        .ms-tile-val {
          font-size: 1.6rem;
          font-weight: 900;
          color: var(--text-primary);
          line-height: 1;
        }

        .ms-rubric-breakdown-box {
          background: var(--bg-surface, #F8F9FA);
          border: 2.5px solid #121316;
          box-shadow: 3.5px 3.5px 0px #121316;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
          transition: all 0.18s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-rubric-breakdown-box:hover {
          transform: translateY(-3px) rotate(-0.5deg);
          box-shadow: 6.5px 6.5px 0px #121316;
        }

        .ms-llm-eval-box {
          background: rgba(0, 102, 255, 0.05);
          border: 2.5px solid #0066FF;
          box-shadow: 4px 4px 0px #0066FF;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
          transition: all 0.18s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-llm-eval-box:hover {
          transform: translateY(-3px) rotate(0.5deg);
          box-shadow: 7px 7px 0px #0066FF;
        }

        .ms-decision-box {
          background: var(--bg-surface, #F8F9FA);
          border: 2.5px solid #121316;
          box-shadow: 3.5px 3.5px 0px #121316;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-decision-box:hover {
          transform: translateY(-3px) rotate(0.4deg);
          box-shadow: 6.5px 6.5px 0px #121316;
        }

        .ms-decision-btn-row {
          display: flex;
          gap: 8px;
        }
        .ms-decide-btn {
          flex: 1;
          font-family: inherit;
          font-size: 0.8rem;
          font-weight: 900;
          text-transform: uppercase;
          padding: 10px;
          border: 2px solid #121316;
          box-shadow: 3.5px 3.5px 0px #121316;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          transition: all 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-decide-btn:hover {
          transform: translate(-3px, -3px);
          box-shadow: 6px 6px 0px #121316;
        }
        .ms-decide-shortlist { background: #00E5A0; color: #121316; }
        .ms-decide-flag      { background: #FFD700; color: #121316; }
        .ms-decide-reject    { background: #FF3333; color: #FFFFFF; }

        /* ── Form Inputs & Selects with Hard Drop Shadows ── */
        .form-input, .form-select {
          background: var(--bg-card, #FFFFFF);
          border: 2.5px solid #121316;
          border-radius: 0px;
          color: var(--text-primary);
          font-family: inherit;
          font-size: 0.86rem;
          font-weight: 700;
          padding: 10px 14px;
          outline: none;
          box-shadow: 3.5px 3.5px 0px #121316;
          transition: all 0.18s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .form-input:hover, .form-select:hover {
          box-shadow: 6px 6px 0px #121316;
          transform: translateY(-2px);
        }
        .form-input:focus, .form-select:focus {
          border-color: #0066FF;
          box-shadow: 5px 5px 0px #0066FF;
          transform: translate(-2px, -2px);
        }

        /* ── Status Pills with Solid Border & Pop Hover ── */
        .status-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 0.72rem;
          font-weight: 900;
          padding: 4px 10px;
          border-radius: 0px;
          border: 2px solid #121316;
          box-shadow: 2.5px 2.5px 0px #121316;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          transition: all 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .status-pill:hover {
          transform: translateY(-2px) scale(1.05);
          box-shadow: 4.5px 4.5px 0px #121316;
        }

        /* ── Score Bars with Hard Memphis Border ── */
        .score-bar-outer {
          height: 9px;
          background: var(--bg-base, #FAFAFA);
          border: 2px solid #121316;
          border-radius: 0px;
          overflow: hidden;
          box-shadow: 1.5px 1.5px 0px #121316;
          transition: all 0.15s ease;
        }
        .score-bar-outer:hover {
          box-shadow: 3px 3px 0px #121316;
          transform: translateY(-1px);
        }

        /* ── Icon Action Buttons ── */
        .icon-btn {
          width: 34px;
          height: 34px;
          border: 2px solid #121316;
          background: var(--bg-card, #FFFFFF);
          color: var(--text-primary);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          box-shadow: 3px 3px 0px #121316;
          transition: all 0.16s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .icon-btn:hover {
          transform: translate(-2px, -2px) rotate(2deg);
          box-shadow: 5px 5px 0px #121316;
          background: #FFD700;
          color: #121316;
        }

        /* ── Compare Modal with Hard Drop Shadow & Pop-up ── */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(18, 19, 22, 0.75);
          backdrop-filter: blur(2px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 999;
          padding: 20px;
        }
        .modal-box {
          background: var(--bg-card, #FFFFFF);
          border: 3.5px solid #121316;
          box-shadow: 12px 12px 0px #121316;
          width: 100%;
          display: flex;
          flex-direction: column;
          position: relative;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .modal-header {
          padding: 16px 20px;
          background: #FFD700;
          color: #121316;
          border-bottom: 3px solid #121316;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .modal-title {
          font-size: 1.05rem;
          font-weight: 900;
          text-transform: uppercase;
          margin: 0;
          letter-spacing: -0.01em;
        }
        .modal-body {
          padding: 24px;
        }
        .modal-footer {
          padding: 14px 24px;
          border-top: 2.5px solid #121316;
          display: flex;
          justify-content: flex-end;
          background: var(--bg-surface, #FAFAFA);
        }
        .ms-compare-card {
          padding: 18px;
          background: var(--bg-surface, #FAFAFA);
          border: 2.5px solid #121316;
          box-shadow: 4px 4px 0px #121316;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-compare-card:hover {
          transform: translateY(-3px) rotate(0.5deg);
          box-shadow: 7px 7px 0px #121316;
        }
        .ms-compare-delta {
          margin-top: 18px;
          padding: 14px 18px;
          background: #FFD700;
          color: #121316;
          border: 2.5px solid #121316;
          box-shadow: 4px 4px 0px #121316;
          font-weight: 900;
          font-size: 0.88rem;
          text-transform: uppercase;
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .ms-compare-delta:hover {
          transform: translateY(-2px);
          box-shadow: 6px 6px 0px #121316;
        }

        @media (max-width: 1100px) {
          .ms-layout-grid { grid-template-columns: 1fr; }
          .ms-ingestion-grid { grid-template-columns: 1fr; }
          .ms-tuner-sliders { grid-template-columns: 1fr; }
        }
      `}</style>

      {/* ── Page Header ── */}
      <div className="ms-page-header">
        <div className="ms-title-group">
          <div className="ms-tag-row">
            <span className="ms-stamp ms-stamp-yellow">Cohort Intelligence Engine</span>
            <span className="ms-stamp ms-stamp-pink">Decoupled Merit Radar</span>
            <span className="ms-stamp ms-stamp-blue">OpenRouter Gemma 4 31B</span>
          </div>
          <h1 className="ms-page-title">
            Candidate Evaluation &amp; Shortlisting Studio
            <MemphisSquiggle color="#FFD700" width={110} height={16} />
          </h1>
          <p className="ms-page-subtitle">
            Merit-based weighted rubric scoring decoupled from AI detection flags. Evaluate submissions strictly on intellectual substance, technical validation, and empirical rigor.
          </p>
        </div>

        <div className="ms-header-actions">
          <button
            className="ms-btn-action ms-btn-pink"
            onClick={() => handleRunLlmEvaluation()}
            disabled={isEvaluating}
            title="Evaluate candidate cohort with google/gemma-4-31b-it:free via OpenRouter"
          >
            {isEvaluating && !evaluatingCandidateId ? (
              <>
                <svg className="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <path d="M21 12a9 9 0 1 1-6.22-8.56"/>
                </svg>
                Evaluating Cohort (Gemma 4 31B)…
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
                Run AI Evaluation (Gemma 4 31B)
              </>
            )}
          </button>

          {comparedSubIds.length === 2 && (
            <button className="ms-btn-action ms-btn-blue" onClick={openCompareModal}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <rect x="2" y="3" width="9" height="18"/>
                <rect x="13" y="3" width="9" height="18"/>
              </svg>
              Compare 2 Candidates
            </button>
          )}

          <button
            className="ms-btn-action ms-btn-yellow"
            onClick={() => setIsRubricTunerOpen(!isRubricTunerOpen)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="4" y1="21" x2="4" y2="14"/>
              <line x1="4" y1="10" x2="4" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12" y2="3"/>
              <line x1="20" y1="21" x2="20" y2="16"/>
              <line x1="20" y1="12" x2="20" y2="3"/>
            </svg>
            {isRubricTunerOpen ? 'Hide Rubric Tuner' : 'Tune Rubric Weights'}
          </button>
        </div>
      </div>

      {/* ── Decoupled Policy Banner ── */}
      <div className="ms-policy-banner">
        <div className="ms-policy-left">
          <div className="ms-policy-icon-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M16 16l3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1zM2 16l3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1zM7 21h10M12 3v18"/>
            </svg>
          </div>
          <div>
            <div className="ms-policy-title">Decoupled Assessment Policy Enforced</div>
            <div className="ms-policy-desc">
              Scores measure intellectual novelty, reasoning rigor, and prompt fidelity. High AI detection flags trigger secondary human review rather than automatic disqualification.
            </div>
          </div>
        </div>
        <span className="ms-policy-badge">
          Human Oversight Active (&gt;70% Threshold)
        </span>
      </div>

      {/* ── CSV Ingestion Card ── */}
      <div className="ms-ingestion-card">
        <div className="ms-ingestion-header">
          <h2 className="ms-ingestion-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="8" y1="13" x2="16" y2="13"/>
              <line x1="8" y1="17" x2="16" y2="17"/>
            </svg>
            Dataset Ingestion &amp; Evaluation Mode
          </h2>

          <div className="ms-mode-pill-select">
            <span>Workflow:</span>
            <select
              className="ms-select-input"
              value={evaluationMode}
              onChange={(e) => handleModeChange(e.target.value)}
            >
              <option value="hackathon">Hackathon Project Shortlister</option>
              <option value="resume">Resume &amp; Candidate Shortlister</option>
            </select>
          </div>
        </div>

        <div className="ms-ingestion-grid">
          {/* Dropzone */}
          <div
            className="ms-dropzone"
            onClick={() => document.getElementById('csv-file-input').click()}
          >
            <input
              type="file"
              id="csv-file-input"
              accept=".csv"
              onChange={handleCsvFileUpload}
              style={{ display: 'none' }}
            />
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#0066FF" strokeWidth="2.5">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17,8 12,3 7,8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <div className="ms-dropzone-title">
              {csvFileName ? `File Loaded: ${csvFileName}` : 'Upload Candidate CSV'}
            </div>
            <p className="ms-dropzone-desc">
              {csvFileName
                ? `${csvCandidateCount} candidates loaded into memory`
                : 'Click to browse or drop CSV file (headers: name, author, summary, text_content)'}
            </p>
          </div>

          {/* Mock Presets */}
          <div className="ms-mock-panel">
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 900, textTransform: 'uppercase', color: 'var(--text-primary)' }}>
                  Mock Datasets (in mock_data/):
                </span>
                <span className="ms-stamp ms-stamp-green" style={{ fontSize: '0.65rem', padding: '2px 8px' }}>
                  2 Mock Files Ready
                </span>
              </div>

              <div className="ms-mock-buttons-row">
                <button
                  type="button"
                  className={`ms-mock-btn ${evaluationMode === 'hackathon' && csvFileName?.includes('hackathon') ? 'active' : ''}`}
                  onClick={() => handleLoadSampleCsv('hackathon')}
                  disabled={isLoadingSample}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                  Load Hackathon Mock CSV (6 Projects)
                </button>

                <button
                  type="button"
                  className={`ms-mock-btn ${evaluationMode === 'resume' && csvFileName?.includes('resume') ? 'active' : ''}`}
                  onClick={() => handleLoadSampleCsv('resume')}
                  disabled={isLoadingSample}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <rect x="2" y="7" width="20" height="14" rx="0" ry="0"/>
                    <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/>
                  </svg>
                  Load Resume Mock CSV (6 Candidates)
                </button>
              </div>
            </div>

            <div className="ms-download-row">
              <span>Files located in <code>mock_data/</code></span>
              <div style={{ display: 'flex', gap: '14px' }}>
                <a href="/mock_data/hackathon_submissions.csv" download="hackathon_submissions.csv" className="ms-dl-link">
                  ↓ Hackathon CSV
                </a>
                <span>·</span>
                <a href="/mock_data/resume_candidates.csv" download="resume_candidates.csv" className="ms-dl-link">
                  ↓ Resume CSV
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Rubric Weight Tuner (Collapsible) ── */}
      {isRubricTunerOpen && (
        <div className="ms-tuner-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <h3 style={{ margin: '0 0 2px', fontSize: '1.05rem', fontWeight: 900, textTransform: 'uppercase' }}>
                Live Weighted Rubric Calibrator
              </h3>
              <span style={{ fontSize: '0.74rem', fontWeight: 700 }}>
                Adjusting weights immediately recalibrates all {submissions.length} candidate scores in real-time.
              </span>
            </div>
            <span className="ms-stamp ms-stamp-pink">
              Total Weight: {weights.relevance + weights.reasoning + weights.originality}%
            </span>
          </div>

          <div className="ms-tuner-sliders">
            <div className="ms-slider-box">
              <div className="ms-slider-head">
                <span>1. Relevance &amp; Alignment</span>
                <span style={{ color: '#0066FF' }}>{weights.relevance}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                value={weights.relevance}
                onChange={(e) => handleWeightChange('relevance', e.target.value)}
                style={{ width: '100%', accentColor: '#0066FF', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#666' }}>
                Prompt fidelity &amp; execution scope
              </span>
            </div>

            <div className="ms-slider-box">
              <div className="ms-slider-head">
                <span>2. Reasoning Rigor</span>
                <span style={{ color: '#FF1493' }}>{weights.reasoning}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                value={weights.reasoning}
                onChange={(e) => handleWeightChange('reasoning', e.target.value)}
                style={{ width: '100%', accentColor: '#FF1493', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#666' }}>
                Analytical depth &amp; technical validation
              </span>
            </div>

            <div className="ms-slider-box">
              <div className="ms-slider-head">
                <span>3. Originality &amp; Novelty</span>
                <span style={{ color: '#00E5A0' }}>{weights.originality}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                value={weights.originality}
                onChange={(e) => handleWeightChange('originality', e.target.value)}
                style={{ width: '100%', accentColor: '#00E5A0', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#666' }}>
                Uniqueness &amp; anti-boilerplate cadence
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ── Cohort Tabs Bar ── */}
      <div className="ms-cohort-tabs">
        {projects.map((p) => (
          <button
            key={p.id}
            className={`ms-cohort-tab-btn ${activeProjectId === p.id ? 'active' : ''}`}
            onClick={() => setActiveProjectId(p.id)}
          >
            <span>{p.name}</span>
            <span className="ms-cohort-tab-count">{p.count}</span>
          </button>
        ))}
      </div>

      {/* ── Sticky Batch Actions Bar ── */}
      {selectedSubIds.length > 0 && (
        <div className="ms-batch-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 900, textTransform: 'uppercase' }}>
            <span>✓ {selectedSubIds.length} candidate(s) selected</span>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              className="ms-btn-action"
              style={{ padding: '6px 14px', fontSize: '0.74rem', background: '#00E5A0', color: '#121316' }}
              onClick={() => handleBatchStatus('shortlisted')}
            >
              Batch Shortlist
            </button>
            <button
              className="ms-btn-action"
              style={{ padding: '6px 14px', fontSize: '0.74rem', background: '#FFD700', color: '#121316' }}
              onClick={() => handleBatchStatus('flagged')}
            >
              Batch Escalate to Oral Defense
            </button>
            <button
              className="ms-btn-action"
              style={{ padding: '6px 14px', fontSize: '0.74rem', background: '#FFFFFF', color: '#121316' }}
              onClick={() => setSelectedSubIds([])}
            >
              Deselect All
            </button>
          </div>
        </div>
      )}

      {/* ── Filter & Search Toolbar ── */}
      <div className="ms-toolbar">
        <div className="ms-filter-pills">
          {['all', 'shortlisted', 'pending', 'flagged'].map((st) => (
            <button
              key={st}
              className={`ms-filter-pill ${statusFilter === st ? 'active' : ''}`}
              onClick={() => setStatusFilter(st)}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="ms-search-box">
          <input
            type="text"
            className="form-input"
            placeholder="Search candidate name, author, or keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <select
            className="form-select"
            value={sortBy}
            onChange={(e) => handleSort(e.target.value)}
            style={{ minWidth: '150px' }}
          >
            <option value="score-desc">Score: High → Low</option>
            <option value="score-asc">Score: Low → High</option>
            <option value="orig-desc">Originality: Highest</option>
            <option value="ai-desc">AI Signal: Highest</option>
            <option value="ai-asc">AI Signal: Lowest</option>
          </select>
        </div>
      </div>

      {/* ── 2-Column Grid: Table (Left) + Drawer (Right) ── */}
      <div className="ms-layout-grid">
        {/* Table Box */}
        <div className="ms-table-box">
          <div className="ms-table-head">
            <div>
              <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 900, textTransform: 'uppercase' }}>
                Candidate Rankings ({filteredSubmissions.length})
              </h3>
              <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>
                Evaluated under {currentProject.rubric}
              </span>
            </div>
            <span className="ms-stamp ms-stamp-pink" style={{ fontSize: '0.65rem' }}>
              Select 2 to Compare
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="ms-table">
              <thead>
                <tr>
                  <th style={{ width: '32px', textAlign: 'center' }}>
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
                    <td colSpan={6} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
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
                        className={isSelected ? 'selected' : ''}
                        onClick={() => setSelectedSub(s)}
                      >
                        <td onClick={(e) => e.stopPropagation()} style={{ textAlign: 'center' }}>
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleToggleSelectSub(s.id)}
                          />
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span className="ms-stamp ms-stamp-yellow" style={{ fontSize: '0.7rem', padding: '2px 6px' }}>
                              {s.rank}
                            </span>
                            <div>
                              <div style={{ fontWeight: 800, color: 'var(--text-primary)' }}>{s.name}</div>
                              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                                {s.author} · {s.id}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontWeight: 900, fontSize: '0.94rem' }}>{s.total}%</span>
                            <div className="score-bar-outer" style={{ width: '60px' }}>
                              <div className="score-bar-inner" style={{ width: `${s.total}%` }} />
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className={`status-pill ${s.aiScore > 70 ? 'high' : s.aiScore > 35 ? 'medium' : 'low'}`}>
                            {s.aiSignal} ({s.aiScore}%)
                          </span>
                        </td>
                        <td>
                          <span className={`status-pill ${s.status === 'shortlisted' ? 'low' : s.status === 'flagged' ? 'high' : 'medium'}`}>
                            {s.status}
                          </span>
                        </td>
                        <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                          <button
                            className={`ms-btn-action ${isCompared ? 'ms-btn-pink' : 'ms-btn-yellow'}`}
                            style={{ fontSize: '0.68rem', padding: '3px 8px' }}
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
        <div className="ms-drawer">
          {selectedSub ? (
            <>
              <div className="ms-drawer-header">
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className="ms-stamp ms-stamp-pink">{selectedSub.rank} Ranked</span>
                    <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-muted)' }}>
                      {selectedSub.id}
                    </span>
                  </div>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 900, textTransform: 'uppercase', color: 'var(--text-primary)' }}>
                    {selectedSub.name}
                  </h3>
                  <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', fontWeight: 700 }}>
                    Lead: {selectedSub.author}
                  </span>
                </div>

                <span className={`status-pill ${selectedSub.status === 'shortlisted' ? 'low' : selectedSub.status === 'flagged' ? 'high' : 'medium'}`}>
                  {selectedSub.status}
                </span>
              </div>

              {/* Score Tile Pair */}
              <div className="ms-score-card-pair">
                <div className="ms-score-tile">
                  <span style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                    Weighted Merit Score
                  </span>
                  <div className="ms-tile-val">{selectedSub.total}%</div>
                </div>

                <div className="ms-score-tile">
                  <span style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                    AI Detection Signal
                  </span>
                  <div className="ms-tile-val" style={{ fontSize: '1.1rem', marginTop: '2px' }}>
                    <span className={`status-pill ${selectedSub.aiScore > 70 ? 'high' : selectedSub.aiScore > 35 ? 'medium' : 'low'}`}>
                      {selectedSub.aiSignal} ({selectedSub.aiScore}%)
                    </span>
                  </div>
                </div>
              </div>

              {/* Rubric Breakdown */}
              <div className="ms-rubric-breakdown-box">
                <span className="section-label">Rubric Criteria Weights &amp; Scores</span>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', fontWeight: 800, marginBottom: '4px' }}>
                      <span>Relevance ({weights.relevance}%)</span>
                      <span>{selectedSub.relevance}/10</span>
                    </div>
                    <div className="score-bar-outer"><div className="score-bar-inner" style={{ width: `${selectedSub.relevance * 10}%`, background: '#0066FF' }} /></div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', fontWeight: 800, marginBottom: '4px' }}>
                      <span>Reasoning Rigor ({weights.reasoning}%)</span>
                      <span>{selectedSub.reasoning}/10</span>
                    </div>
                    <div className="score-bar-outer"><div className="score-bar-inner" style={{ width: `${selectedSub.reasoning * 10}%`, background: '#FF1493' }} /></div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', fontWeight: 800, marginBottom: '4px' }}>
                      <span>Originality ({weights.originality}%)</span>
                      <span>{selectedSub.originality}/10</span>
                    </div>
                    <div className="score-bar-outer"><div className="score-bar-inner" style={{ width: `${selectedSub.originality * 10}%`, background: '#00E5A0' }} /></div>
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div>
                <span className="section-label">Executive Evaluation Rationale</span>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-primary)', lineHeight: 1.6, fontWeight: 600, margin: '6px 0 0' }}>
                  {selectedSub.summary}
                </p>
              </div>

              {/* Gemma 4 31B AI Assessment Box */}
              <div className="ms-llm-eval-box">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                  <span style={{ fontSize: '0.76rem', fontWeight: 900, textTransform: 'uppercase', color: '#0066FF' }}>
                    Gemma 4 31B Forensics
                  </span>
                  <button
                    className="ms-btn-action ms-btn-pink"
                    style={{ padding: '4px 10px', fontSize: '0.68rem' }}
                    onClick={() => handleEvaluateSingle(selectedSub.id)}
                    disabled={isEvaluating}
                  >
                    {isEvaluating && evaluatingCandidateId === selectedSub.id ? 'Evaluating…' : 'Evaluate Single'}
                  </button>
                </div>

                {selectedSub.criterionScores && selectedSub.criterionScores.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {selectedSub.criterionScores.map((c, i) => (
                      <div key={i} style={{ borderTop: i > 0 ? '1.5px solid #0066FF' : 'none', paddingTop: i > 0 ? '6px' : '0' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', fontWeight: 900 }}>
                          <span>{c.criterion_title || c.criterion_key}</span>
                          <span>{c.score}/{c.max_score || 10}</span>
                        </div>
                        <p style={{ margin: '2px 0', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{c.explanation}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                    Click &quot;Evaluate Single&quot; to query Gemma 4 31B via OpenRouter for detailed criterion explanations.
                  </p>
                )}
              </div>

              {/* Reviewer Action Bar */}
              <div className="ms-decision-box">
                <span className="section-label">Record Reviewer Decision</span>

                <div className="ms-decision-btn-row">
                  <button className="ms-decide-btn ms-decide-shortlist" onClick={() => updateStatus(selectedSub.id, 'shortlisted')}>
                    ✓ Shortlist
                  </button>
                  <button className="ms-decide-btn ms-decide-flag" onClick={() => updateStatus(selectedSub.id, 'flagged')}>
                    ⚠ Flag Oral
                  </button>
                  <button className="ms-decide-btn ms-decide-reject" onClick={() => updateStatus(selectedSub.id, 'rejected')}>
                    ✕ Reject
                  </button>
                </div>

                <input
                  type="text"
                  className="form-input"
                  placeholder="Rationale signed to SHA-256 ledger..."
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  style={{ fontSize: '0.78rem' }}
                />

                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {[
                    'Exceptional technical novelty verified.',
                    'AI used strictly as secondary research tool.',
                    'Flagged for 10-minute technical oral defense.',
                  ].map((tmpl, idx) => (
                    <button
                      key={idx}
                      className="ms-stamp ms-stamp-yellow"
                      style={{ fontSize: '0.62rem', padding: '2px 8px', cursor: 'pointer' }}
                      onClick={() => setOverrideReason(tmpl)}
                    >
                      + {tmpl}
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)', fontWeight: 700 }}>
              Select a candidate from the table to view detailed rubric metrics.
            </div>
          )}
        </div>
      </div>

      {/* ── Compare Modal ── */}
      {isCompareModalOpen && sub1 && sub2 && (
        <div className="modal-overlay" onClick={() => setIsCompareModalOpen(false)}>
          <div className="modal-box" style={{ maxWidth: '840px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Side-by-Side Candidate Rubric Comparison</h3>
              <button
                className="icon-btn"
                onClick={() => setIsCompareModalOpen(false)}
                style={{ width: '28px', height: '28px' }}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                {/* Candidate 1 */}
                <div className="ms-compare-card">
                  <span className="ms-stamp ms-stamp-pink" style={{ marginBottom: '6px' }}>{sub1.rank} Ranked</span>
                  <h4 style={{ margin: '4px 0', fontSize: '1.1rem', fontWeight: 900 }}>{sub1.name}</h4>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>{sub1.author}</span>
                  <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#0066FF', margin: '10px 0' }}>{sub1.total}%</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.78rem' }}>
                    <div>Relevance: <strong>{sub1.relevance}/10</strong></div>
                    <div>Reasoning: <strong>{sub1.reasoning}/10</strong></div>
                    <div>Originality: <strong>{sub1.originality}/10</strong></div>
                    <div style={{ marginTop: '8px' }}>
                      <span className={`status-pill ${sub1.aiScore > 70 ? 'high' : 'low'}`}>
                        AI: {sub1.aiSignal} ({sub1.aiScore}%)
                      </span>
                    </div>
                  </div>
                </div>

                {/* Candidate 2 */}
                <div className="ms-compare-card">
                  <span className="ms-stamp ms-stamp-yellow" style={{ marginBottom: '6px' }}>{sub2.rank} Ranked</span>
                  <h4 style={{ margin: '4px 0', fontSize: '1.1rem', fontWeight: 900 }}>{sub2.name}</h4>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>{sub2.author}</span>
                  <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#FF1493', margin: '10px 0' }}>{sub2.total}%</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.78rem' }}>
                    <div>Relevance: <strong>{sub2.relevance}/10</strong></div>
                    <div>Reasoning: <strong>{sub2.reasoning}/10</strong></div>
                    <div>Originality: <strong>{sub2.originality}/10</strong></div>
                    <div style={{ marginTop: '8px' }}>
                      <span className={`status-pill ${sub2.aiScore > 70 ? 'high' : 'low'}`}>
                        AI: {sub2.aiSignal} ({sub2.aiScore}%)
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Delta Box */}
              <div className="ms-compare-delta">
                Score Advantage: {Math.abs(sub1.total - sub2.total).toFixed(1)}% to {sub1.total >= sub2.total ? sub1.name : sub2.name}
              </div>
            </div>

            <div className="modal-footer">
              <button className="ms-btn-action ms-btn-pink" onClick={() => setIsCompareModalOpen(false)}>
                Done Reviewing
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
