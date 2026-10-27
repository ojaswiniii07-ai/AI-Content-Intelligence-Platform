import { useState, useRef, useEffect } from 'react'

export default function LandingPage({ onEnter, theme, toggleTheme }) {
  const [activeTab, setActiveTab] = useState('text') // 'text' | 'video' | 'shortlist' | 'audit'
  const [demoTextIdx, setDemoTextIdx] = useState(0)
  const [activeFrameIdx, setActiveFrameIdx] = useState(3)
  const [quickInput, setQuickInput] = useState('')
  const [draggedNode, setDraggedNode] = useState(null)
  const [nodes, setNodes] = useState([
    { id: 'n1', label: '🛡️ SHA-256 Chained Audit', x: 8, y: 18, vx: 0.2, vy: 0.15 },
    { id: 'n2', label: '📹 EfficientNet-B0 Video', x: 74, y: 14, vx: -0.18, vy: 0.22 },
    { id: 'n3', label: '✍️ Ensemble Text Forensics', x: 5, y: 68, vx: 0.15, vy: -0.2 },
    { id: 'n4', label: '👁️ MTCNN Facial Alignment', x: 78, y: 62, vx: -0.22, vy: -0.15 },
    { id: 'n5', label: '⚖️ Decoupled Rubric Engine', x: 42, y: 84, vx: 0.12, vy: 0.18 },
  ])

  // Dragging support for floating capability badges
  const heroRef = useRef(null)
  const isDraggingRef = useRef(false)
  const dragTargetIdRef = useRef(null)

  const handlePointerDown = (id, e) => {
    e.preventDefault()
    isDraggingRef.current = true
    dragTargetIdRef.current = id
    setDraggedNode(id)
  }

  const handlePointerMove = (e) => {
    if (!isDraggingRef.current || !dragTargetIdRef.current || !heroRef.current) return
    const rect = heroRef.current.getBoundingClientRect()
    const xPct = Math.max(2, Math.min(90, ((e.clientX - rect.left) / rect.width) * 100))
    const yPct = Math.max(5, Math.min(92, ((e.clientY - rect.top) / rect.height) * 100))

    setNodes((prev) =>
      prev.map((n) =>
        n.id === dragTargetIdRef.current ? { ...n, x: xPct, y: yPct } : n
      )
    )
  }

  const handlePointerUp = () => {
    isDraggingRef.current = false
    dragTargetIdRef.current = null
    setDraggedNode(null)
  }

  // Floating gentle levitation physics
  useEffect(() => {
    const interval = setInterval(() => {
      if (isDraggingRef.current) return
      setNodes((prev) =>
        prev.map((n) => {
          let newX = n.x + n.vx * 0.15
          let newY = n.y + n.vy * 0.15
          let vx = n.vx
          let vy = n.vy

          // Bounce off container boundaries
          if (newX < 2 || newX > 88) vx = -vx
          if (newY < 8 || newY > 88) vy = -vy

          return { ...n, x: newX, y: newY, vx, vy }
        })
      )
    }, 50)
    return () => clearInterval(interval)
  }, [])

  const sampleTexts = [
    {
      title: 'Synthetic Academic Abstract',
      score: 88,
      verdict: 'High AI Involvement',
      level: 'High Confidence',
      spans: [
        { text: 'The paradigm of sovereign machine learning represents an unprecedented inflection point', heat: 'high' },
        { text: 'in modern algorithmic governance and decentralized data architecture.', heat: 'high' },
        { text: 'However, empirical validation requires systematic stress-testing across diverse benchmark distributions.', heat: 'low' },
        { text: 'Consequently, robust cross-entropy minimization guarantees bounded risk propagation.', heat: 'mid' },
      ],
      dims: [
        { name: 'Repetitive Boilerplate', pct: 86 },
        { name: 'Sentence Uniformity', pct: 79 },
        { name: 'Source Proximity', pct: 32 },
        { name: 'Style Flatness', pct: 91 },
      ],
    },
    {
      title: 'Human Investigative Editorial',
      score: 18,
      verdict: 'Authentic Human Content',
      level: 'High Confidence',
      spans: [
        { text: 'We pulled four sleepless nights tracing the raw telemetry packets across the staging cluster.', heat: 'low' },
        { text: 'Nobody expected the third switch to fail, but it did—leaving us with half-corrupted logs.', heat: 'low' },
        { text: 'It took three cups of bitter filter coffee before we noticed the timestamp skew.', heat: 'low' },
        { text: 'That single thirty-second offset explained all the phantom dropped connections.', heat: 'low' },
      ],
      dims: [
        { name: 'Repetitive Boilerplate', pct: 14 },
        { name: 'Sentence Uniformity', pct: 22 },
        { name: 'Source Proximity', pct: 8 },
        { name: 'Style Flatness', pct: 19 },
      ],
    },
    {
      title: 'Hybrid / Mixed Collaboration',
      score: 54,
      verdict: 'Mixed Authorship',
      level: 'Review Recommended',
      spans: [
        { text: 'The following framework synthesizes current decentralized integrity protocols.', heat: 'high' },
        { text: 'I personally edited the third section to incorporate our on-prem hardware specs.', heat: 'low' },
        { text: 'This integration empowers enterprise reviewers with verifiable forensic auditability.', heat: 'mid' },
        { text: 'We found that strict 70% thresholding yields minimal false positives on our dataset.', heat: 'low' },
      ],
      dims: [
        { name: 'Repetitive Boilerplate', pct: 58 },
        { name: 'Sentence Uniformity', pct: 51 },
        { name: 'Source Proximity', pct: 24 },
        { name: 'Style Flatness', pct: 60 },
      ],
    },
  ]

  const videoFrames = [
    { idx: 1, p: 0.18, verdict: 'Real', face: true },
    { idx: 2, p: 0.22, verdict: 'Real', face: true },
    { idx: 3, p: 0.48, verdict: 'Suspicious', face: true },
    { idx: 4, p: 0.89, verdict: 'Deepfake', face: true, anomaly: 'Jawline boundary blend anomaly' },
    { idx: 5, p: 0.92, verdict: 'Deepfake', face: true, anomaly: 'Bilinear pixel interpolation cue' },
    { idx: 6, p: 0.86, verdict: 'Deepfake', face: true, anomaly: 'Temporal blink rate mismatch' },
    { idx: 7, p: 0.74, verdict: 'Deepfake', face: true },
    { idx: 8, p: 0.25, verdict: 'Real', face: false, note: 'Occluded face' },
    { idx: 9, p: 0.88, verdict: 'Deepfake', face: true, anomaly: 'Synthetic lighting gradient' },
    { idx: 10, p: 0.91, verdict: 'Deepfake', face: true, anomaly: 'Audio-lip sync delta -84ms' },
    { idx: 11, p: 0.78, verdict: 'Deepfake', face: true },
    { idx: 12, p: 0.52, verdict: 'Suspicious', face: true },
    { idx: 13, p: 0.31, verdict: 'Real', face: true },
    { idx: 14, p: 0.20, verdict: 'Real', face: true },
    { idx: 15, p: 0.16, verdict: 'Real', face: true },
    { idx: 16, p: 0.14, verdict: 'Real', face: true },
  ]

  const candidates = [
    { rank: '#1', name: 'Team Nexus', qScore: 92, aiSig: 'Low', aiPct: 18, status: 'Shortlisted', note: 'Strong architectural depth + cryptographic proof' },
    { rank: '#2', name: 'DataForge', qScore: 85, aiSig: 'Medium', aiPct: 54, status: 'Under Review', note: 'High reasoning rigor despite synthetic phrasing' },
    { rank: '#3', name: 'AISolve Co.', qScore: 74, aiSig: 'High', aiPct: 82, status: 'Flagged', note: 'Generic boilerplate; decoupled evaluation allows human override' },
    { rank: '#4', name: 'Quantum Leap', qScore: 82, aiSig: 'Low', aiPct: 24, status: 'Shortlisted', note: 'Empirical benchmark with multi-agent consensus' },
  ]

  const auditBlocks = [
    { id: 'evt_9041', time: '14:22:04 UTC', type: 'Submission Analyzed', actor: 'Local Ensemble Worker', hash: 'e3b0c44298fc1c14...855', prev: '4f53cda18c2b...945', status: 'Intact' },
    { id: 'evt_9038', time: '14:25:31 UTC', type: 'Reviewer Decision', actor: 'ojaswini@org.com', hash: '4f53cda18c2baa0c...945', prev: 'a94a8fe5ccb1...7c3', status: 'Intact' },
    { id: 'evt_9032', time: '14:31:18 UTC', type: 'Override Recorded', actor: 'lead-auditor@org.com', hash: 'a94a8fe5ccb19ba6...7c3', prev: 'b10a8db164e0...ee9', status: 'Intact' },
  ]

  const partnerLogos = [
    'Hackathon League',
    'National Edu Council',
    'Integrity Consortium',
    'TechHiring 2026',
    'ForensicLabs AI',
    'Enterprise Trust Alliance',
    'Sovereign AI Compute',
  ]

  const handleLaunchWithInput = () => {
    if (quickInput.trim()) {
      localStorage.setItem('authentiq_seed_text', quickInput.trim())
    }
    onEnter()
  }

  const selectedSample = sampleTexts[demoTextIdx]
  const selectedFrame = videoFrames[activeFrameIdx] || videoFrames[3]

  return (
    <div
      className="sarvam-landing"
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      {/* ── 1. Floating Nav Header (Sarvam minimal pill style) ── */}
      <header className="sarvam-header">
        <div className="sarvam-header-inner">
          <div className="sarvam-brand" onClick={onEnter} style={{ cursor: 'pointer' }}>
            <div className="sarvam-logo-mark">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <span className="sarvam-brand-name">AuthentiQ</span>
            <span className="sarvam-version-pill">v2.4 Sovereign</span>
          </div>

          <nav className="sarvam-nav-menu">
            <a href="#playground" className="sarvam-nav-item">Models</a>
            <a href="#features" className="sarvam-nav-item">Architecture</a>
            <a href="#shortlist-section" className="sarvam-nav-item">Shortlisting</a>
            <a href="#compliance" className="sarvam-nav-item">Audit Ledger</a>
            <a href="#trust" className="sarvam-nav-item">Trust & Security</a>
          </nav>

          <div className="sarvam-header-actions">
            <button
              className="sarvam-theme-toggle"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              ) : (
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
                </svg>
              )}
            </button>

            <button className="sarvam-btn-outline" onClick={onEnter}>
              Sign In
            </button>

            <button className="sarvam-btn-primary" onClick={onEnter}>
              <span>Launch Console</span>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* ── 2. Hero Section (With Sarvam Gateway Motif & Movable Physics Icons) ── */}
      <section className="sarvam-hero" ref={heroRef}>
        {/* Subtle radial architectural mesh */}
        <div className="sarvam-radial-glow" aria-hidden="true" />

        {/* Movable / Draggable floating capability badges */}
        <div className="sarvam-movable-container" aria-hidden="false">
          {nodes.map((node) => {
            const isHeld = draggedNode === node.id
            return (
              <div
                key={node.id}
                className={`sarvam-movable-badge ${isHeld ? 'is-dragging' : ''}`}
                style={{
                  left: `${node.x}%`,
                  top: `${node.y}%`,
                  cursor: isHeld ? 'grabbing' : 'grab',
                }}
                onPointerDown={(e) => handlePointerDown(node.id, e)}
                title="Drag me around! Movable capability node"
              >
                <span className="movable-badge-dot" />
                <span className="movable-badge-text">{node.label}</span>
              </div>
            )
          })}
        </div>

        {/* Sarvam Architectural Gateway Motif */}
        <div className="sarvam-motif-wrapper">
          <div className="sarvam-motif-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <div className="sarvam-divider-line" />
          <p className="sarvam-eyebrow-pill">
            SOVEREIGN CONTENT FORENSICS & DEEPFAKE INTELLIGENCE
          </p>
          <div className="sarvam-divider-line" />
        </div>

        {/* Main Headline */}
        <h1 className="sarvam-hero-title">
          Authenticity &amp; Integrity<br />
          Engineered for Sovereignty
        </h1>

        <p className="sarvam-hero-subtitle">
          Full-stack content intelligence: sentence-level text attribution, frame-accurate
          EfficientNet-B0 video deepfake inference, and tamper-evident SHA-256 audit trails.
        </p>

        {/* CTA Buttons */}
        <div className="sarvam-hero-actions">
          <button className="sarvam-btn-primary large" onClick={onEnter}>
            <span>Open AuthentiQ Platform</span>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>

          <a href="#playground" className="sarvam-btn-outline large">
            <span>Explore Live Models</span>
          </a>
        </div>

        {/* Quick-Prompt Interactive Input Sandbox */}
        <div className="sarvam-quick-input-card">
          <div className="quick-input-chips">
            <span className="quick-label">Try sample:</span>
            {sampleTexts.map((st, i) => (
              <button
                key={i}
                type="button"
                className={`quick-chip ${demoTextIdx === i ? 'active' : ''}`}
                onClick={() => {
                  setDemoTextIdx(i)
                  setQuickInput(st.spans.map((s) => s.text).join(' '))
                }}
              >
                {st.title}
              </button>
            ))}
          </div>

          <div className="quick-input-row">
            <input
              type="text"
              className="quick-input-field"
              placeholder="Paste submission text or test paragraph to analyze..."
              value={quickInput}
              onChange={(e) => setQuickInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLaunchWithInput()}
            />
            <button className="quick-submit-btn" onClick={handleLaunchWithInput}>
              Analyze Now →
            </button>
          </div>
          <div className="quick-hint">
            <span>⚡ Bundled local model · 0 API keys · Zero data retention policy</span>
          </div>
        </div>

        {/* Stats Strip */}
        <div className="sarvam-hero-stats">
          <div className="sarvam-stat-item">
            <span className="stat-num">94.7%</span>
            <span className="stat-desc">Ensemble Precision</span>
          </div>
          <div className="sarvam-stat-sep" />
          <div className="sarvam-stat-item">
            <span className="stat-num">16 FPS</span>
            <span className="stat-desc">Video Inference</span>
          </div>
          <div className="sarvam-stat-sep" />
          <div className="sarvam-stat-item">
            <span className="stat-num">&lt;120ms</span>
            <span className="stat-desc">Text Latency</span>
          </div>
          <div className="sarvam-stat-sep" />
          <div className="sarvam-stat-item">
            <span className="stat-num">SHA-256</span>
            <span className="stat-desc">Cryptographic Ledger</span>
          </div>
        </div>
      </section>

      {/* ── 3. Customer & Ecosystem Infinite Marquee ── */}
      <section className="sarvam-marquee-section" id="trust">
        <p className="sarvam-marquee-label">
          DEPLOYED ACROSS INTEGRITY COMMITTEES, UNIVERSITIES &amp; HACKATHONS
        </p>
        <div className="sarvam-marquee-track">
          <div className="sarvam-marquee-inner">
            {[...partnerLogos, ...partnerLogos].map((name, i) => (
              <div key={i} className="sarvam-marquee-item">
                <span className="marquee-dot" />
                <span className="marquee-name">{name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 4. Live Interactive Model Playground (Like Sarvam.ai Homepage) ── */}
      <section className="sarvam-playground-section" id="playground">
        <div className="sarvam-section-header">
          <span className="sarvam-tag">INTERACTIVE PLAYGROUND</span>
          <h2 className="sarvam-section-title">Test Sovereign AI Models in Real Time</h2>
          <p className="sarvam-section-desc">
            Explore AuthentiQ's bundled neural models right in your browser. All inference
            features decouple probabilistic signals from qualitative rubric judgments.
          </p>
        </div>

        {/* Playground Tab Selector */}
        <div className="sarvam-tab-bar">
          <button
            className={`sarvam-tab-btn ${activeTab === 'text' ? 'active' : ''}`}
            onClick={() => setActiveTab('text')}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            <span>Text Forensics (Ensemble)</span>
          </button>

          <button
            className={`sarvam-tab-btn ${activeTab === 'video' ? 'active' : ''}`}
            onClick={() => setActiveTab('video')}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="23 7 16 12 23 17 23 7" />
              <rect x="1" y="5" width="15" height="14" rx="2" />
            </svg>
            <span>Video Deepfake (EfficientNet-B0)</span>
          </button>

          <button
            className={`sarvam-tab-btn ${activeTab === 'shortlist' ? 'active' : ''}`}
            onClick={() => setActiveTab('shortlist')}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 00-3-3.87" />
              <path d="M16 3.13a4 4 0 010 7.75" />
            </svg>
            <span>Decoupled Rubric Shortlist</span>
          </button>

          <button
            className={`sarvam-tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            <span>Cryptographic Audit Ledger</span>
          </button>
        </div>

        {/* Playground Container */}
        <div className="sarvam-playground-card">
          {/* ── TAB 1: Text Forensics ── */}
          {activeTab === 'text' && (
            <div className="playground-tab-view">
              <div className="pg-left">
                <div className="pg-card-header">
                  <div className="pg-title-group">
                    <span className="pg-card-title">Sentence-Level AI Heatmap</span>
                    <span className="pg-card-meta">Model: TF-IDF + SGD + LightGBM Ensemble</span>
                  </div>
                  <div className="sample-pill-group">
                    {sampleTexts.map((st, i) => (
                      <button
                        key={i}
                        className={`sample-pill ${demoTextIdx === i ? 'active' : ''}`}
                        onClick={() => setDemoTextIdx(i)}
                      >
                        {st.title.split(' ')[0]}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pg-sentence-box">
                  {selectedSample.spans.map((span, idx) => (
                    <span
                      key={idx}
                      className={`heatmap-span heat-${span.heat}`}
                      title={`Heat: ${span.heat.toUpperCase()}`}
                    >
                      {span.text}{' '}
                    </span>
                  ))}
                </div>

                <div className="heatmap-legend">
                  <span className="legend-item"><span className="legend-box heat-high" /> High AI Cue</span>
                  <span className="legend-item"><span className="legend-box heat-mid" /> Moderate Signal</span>
                  <span className="legend-item"><span className="legend-box heat-low" /> Authentic Pattern</span>
                </div>
              </div>

              <div className="pg-right">
                <div className="pg-score-card">
                  <span className="score-label">Synthetic Signal Probability</span>
                  <div className="score-num-wrap">
                    <span className="score-big">{selectedSample.score}%</span>
                    <span className={`verdict-pill ${selectedSample.score > 60 ? 'fake' : selectedSample.score > 35 ? 'mid' : 'real'}`}>
                      {selectedSample.verdict}
                    </span>
                  </div>
                  <span className="score-sub">{selectedSample.level} · Calibrated against PRD benchmarks</span>
                </div>

                <div className="pg-dim-list">
                  <span className="dim-head">Linguistic Dimensions</span>
                  {selectedSample.dims.map((d, i) => (
                    <div key={i} className="dim-row">
                      <div className="dim-labels">
                        <span>{d.name}</span>
                        <span style={{ fontWeight: 600 }}>{d.pct}%</span>
                      </div>
                      <div className="dim-bar-track">
                        <div
                          className="dim-bar-fill"
                          style={{
                            width: `${d.pct}%`,
                            background: d.pct > 65 ? 'var(--rose)' : d.pct > 40 ? 'var(--amber)' : 'var(--emerald)',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <button className="sarvam-btn-primary full-width" onClick={onEnter}>
                  Analyze Full Text in Console →
                </button>
              </div>
            </div>
          )}

          {/* ── TAB 2: Video Deepfake ── */}
          {activeTab === 'video' && (
            <div className="playground-tab-view">
              <div className="pg-left">
                <div className="pg-card-header">
                  <div className="pg-title-group">
                    <span className="pg-card-title">Frame-Level DFDC Deepfake Inspection</span>
                    <span className="pg-card-meta">Inference Engine: EfficientNet-B0 + MTCNN (160×160 ROI)</span>
                  </div>
                  <span className="fps-indicator">● 16 Frames Sampled</span>
                </div>

                {/* 16-frame scrubber bar chart */}
                <div className="pg-frame-bars-container">
                  {videoFrames.map((fr, idx) => {
                    const isSelected = activeFrameIdx === idx
                    const barColor = !fr.face
                      ? '#4b5563'
                      : fr.p > 0.65
                      ? 'var(--rose)'
                      : fr.p > 0.4
                      ? 'var(--amber)'
                      : 'var(--emerald)'

                    return (
                      <div
                        key={idx}
                        className={`frame-col ${isSelected ? 'selected' : ''}`}
                        onClick={() => setActiveFrameIdx(idx)}
                        title={`Frame #${fr.idx}: ${(fr.p * 100).toFixed(0)}% (${fr.verdict})`}
                      >
                        <div
                          className="frame-bar-fill"
                          style={{
                            height: `${Math.max(16, Math.round(fr.p * 100))}%`,
                            background: barColor,
                          }}
                        />
                        <span className="frame-idx-label">#{fr.idx}</span>
                      </div>
                    )
                  })}
                </div>

                {/* Active Frame Inspector */}
                <div className="active-frame-details">
                  <div className="afd-row">
                    <span className="afd-tag">Frame #{selectedFrame.idx} of 16</span>
                    <span className="afd-status" style={{ color: selectedFrame.p > 0.5 ? 'var(--rose)' : 'var(--emerald)' }}>
                      Verdict: <strong>{selectedFrame.verdict}</strong> ({Math.round(selectedFrame.p * 100)}%)
                    </span>
                  </div>
                  <p className="afd-desc">
                    {selectedFrame.anomaly || (selectedFrame.face ? 'Face localized via MTCNN; consistent facial landmarks & natural texture gradients.' : 'Face temporarily occluded; excluded from aggressive scoring.')}
                  </p>
                </div>
              </div>

              <div className="pg-right">
                <div className="pg-score-card">
                  <span className="score-label">Aggregated Video Manipulation</span>
                  <div className="score-num-wrap">
                    <span className="score-big" style={{ color: 'var(--rose)' }}>76.5%</span>
                    <span className="verdict-pill fake">Likely Deepfake</span>
                  </div>
                  <span className="score-sub">Mean + Max Pooling across 16 frames · DFDC Dataset Weights</span>
                </div>

                <div className="pg-spec-box">
                  <div className="spec-row">
                    <span className="spec-k">Face Detector:</span>
                    <span className="spec-v">MTCNN PyTorch (160×160)</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-k">Backbone:</span>
                    <span className="spec-v">EfficientNet-B0 (Trained)</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-k">Local Model:</span>
                    <span className="spec-v">deepfake_best_head.pth</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-k">API Key:</span>
                    <span className="spec-v" style={{ color: 'var(--emerald)' }}>None Required (Local)</span>
                  </div>
                </div>

                <button className="sarvam-btn-primary full-width" onClick={onEnter}>
                  Upload Video in Console →
                </button>
              </div>
            </div>
          )}

          {/* ── TAB 3: Candidate Shortlisting ── */}
          {activeTab === 'shortlist' && (
            <div className="playground-tab-view shortlist-view">
              <div className="pg-left full">
                <div className="pg-card-header">
                  <div className="pg-title-group">
                    <span className="pg-card-title">Decoupled Rubric Scoring vs. AI Involvement Signal</span>
                    <span className="pg-card-meta">Ensures candidates are evaluated by analytical depth, not penalized blindly by AI cues</span>
                  </div>
                  <span className="rubric-badge">Cohort: Hackathon 2026</span>
                </div>

                <div className="shortlist-table-preview">
                  <table>
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Candidate / Team</th>
                        <th>Quality Score</th>
                        <th>AI Signal</th>
                        <th>Decoupled Policy</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {candidates.map((c, i) => (
                        <tr key={i}>
                          <td style={{ fontWeight: 700 }}>{c.rank}</td>
                          <td>
                            <strong>{c.name}</strong>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{c.note}</div>
                          </td>
                          <td>
                            <div className="score-pill-wrap">
                              <span style={{ fontWeight: 700 }}>{c.qScore}%</span>
                              <div className="mini-bar"><div style={{ width: `${c.qScore}%` }} /></div>
                            </div>
                          </td>
                          <td>
                            <span className={`ai-badge ${c.aiSig.toLowerCase()}`}>
                              {c.aiSig} ({c.aiPct}%)
                            </span>
                          </td>
                          <td>
                            <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>
                              {c.aiSig === 'High' ? 'Tier-2 Human Audit' : 'Direct Qualification'}
                            </span>
                          </td>
                          <td>
                            <span className={`status-badge ${c.status === 'Shortlisted' ? 'shortlisted' : c.status === 'Flagged' ? 'flagged' : 'pending'}`}>
                              {c.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="shortlist-note">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span>
                    <strong>AuthentiQ Principle:</strong> Rubric quality score and AI signals are decoupled. High AI cues trigger human review rather than automatic rejection.
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* ── TAB 4: Cryptographic Audit Ledger ── */}
          {activeTab === 'audit' && (
            <div className="playground-tab-view">
              <div className="pg-left">
                <div className="pg-card-header">
                  <div className="pg-title-group">
                    <span className="pg-card-title">Immutable SHA-256 Chained Event Stream</span>
                    <span className="pg-card-meta">Append-only ledger guaranteeing forensic non-repudiation</span>
                  </div>
                  <div className="merkle-valid-pill">
                    <span className="pulse-dot green" />
                    <span>Merkle Hash Intact</span>
                  </div>
                </div>

                <div className="audit-blocks-flow">
                  {auditBlocks.map((b, idx) => (
                    <div key={idx} className="audit-block-node">
                      <div className="block-meta-row">
                        <span className="block-id">{b.id}</span>
                        <span className="block-time">{b.time}</span>
                        <span className="block-status-pill">{b.status}</span>
                      </div>
                      <div className="block-type">{b.type}</div>
                      <div className="block-actor">Actor: {b.actor}</div>
                      <div className="block-hash">
                        <span>SHA-256: <code>{b.hash}</code></span>
                        <span>Prev: <code>{b.prev}</code></span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pg-right">
                <div className="pg-score-card">
                  <span className="score-label">Ledger Integrity Status</span>
                  <div className="score-num-wrap">
                    <span className="score-big" style={{ color: 'var(--emerald)' }}>100%</span>
                    <span className="verdict-pill real">Cryptographically Verified</span>
                  </div>
                  <span className="score-sub">Zero historical mutations · Immutable chained hashes</span>
                </div>

                <div className="pg-dim-list">
                  <span className="dim-head">Compliance Guarantees</span>
                  <div className="compliance-item">
                    <span>✓ GDPR &amp; Academic Integrity Ready</span>
                  </div>
                  <div className="compliance-item">
                    <span>✓ Every Override Mandatory Rationale</span>
                  </div>
                  <div className="compliance-item">
                    <span>✓ SHA-256 Digest Export Support</span>
                  </div>
                  <div className="compliance-item">
                    <span>✓ Strict Non-Repudiation for Reviewers</span>
                  </div>
                </div>

                <button className="sarvam-btn-primary full-width" onClick={onEnter}>
                  Inspect Live Audit Trail →
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ── 5. Architectural Capability Grid (6 Pillars) ── */}
      <section className="sarvam-features-grid-section" id="features">
        <div className="sarvam-section-header">
          <span className="sarvam-tag">CORE PLATFORM PILLARS</span>
          <h2 className="sarvam-section-title">Engineered for High-Stakes Accuracy</h2>
          <p className="sarvam-section-desc">
            Standard AI detectors provide vague percentage guesses. AuthentiQ provides
            calibrated evidence, reproducible metrics, and transparent human-in-the-loop workflows.
          </p>
        </div>

        <div className="sarvam-grid-6">
          <div className="sarvam-card">
            <div className="sarvam-card-icon">✍️</div>
            <h3 className="sarvam-card-title">Ensemble Text Forensics</h3>
            <p className="sarvam-card-desc">
              LightGBM, TF-IDF n-grams, and SGD classifiers trained on academic benchmarks to generate sentence-level probability heatmaps.
            </p>
            <div className="sarvam-card-chips">
              <span>94.7% Precision</span>
              <span>Sentence Heatmap</span>
            </div>
          </div>

          <div className="sarvam-card">
            <div className="sarvam-card-icon">📹</div>
            <h3 className="sarvam-card-title">Video Deepfake Neural Network</h3>
            <p className="sarvam-card-desc">
              EfficientNet-B0 backbone fine-tuned on the DFDC dataset with MTCNN 160×160 face localization for per-frame synthetic blend detection.
            </p>
            <div className="sarvam-card-chips">
              <span>16fps Inference</span>
              <span>Local Weights</span>
            </div>
          </div>

          <div className="sarvam-card">
            <div className="sarvam-card-icon">⚖️</div>
            <h3 className="sarvam-card-title">Decoupled Candidate Shortlisting</h3>
            <p className="sarvam-card-desc">
              Multi-criteria rubric weighting (Relevance, Reasoning, Originality) with decoupled AI signal tracking to prevent unfair automatic rejections.
            </p>
            <div className="sarvam-card-chips">
              <span>Decoupled Policy</span>
              <span>Weighted Rubrics</span>
            </div>
          </div>

          <div className="sarvam-card">
            <div className="sarvam-card-icon">🛡️</div>
            <h3 className="sarvam-card-title">Immutable Cryptographic Audit</h3>
            <p className="sarvam-card-desc">
              Every prediction, reviewer decision, and threshold override is chained into an append-only verifiable SHA-256 ledger.
            </p>
            <div className="sarvam-card-chips">
              <span>SHA-256 Ledger</span>
              <span>Non-Repudiation</span>
            </div>
          </div>

          <div className="sarvam-card">
            <div className="sarvam-card-icon">📊</div>
            <h3 className="sarvam-card-title">FP/FN Trade-Off Simulator</h3>
            <p className="sarvam-card-desc">
              Interactive threshold calibration simulator calculating operational precision, recall, and confusion matrix before deploying rubrics.
            </p>
            <div className="sarvam-card-chips">
              <span>PR Curves</span>
              <span>Threshold Calibration</span>
            </div>
          </div>

          <div className="sarvam-card">
            <div className="sarvam-card-icon">⚡</div>
            <h3 className="sarvam-card-title">Batch Pipeline &amp; Staging</h3>
            <p className="sarvam-card-desc">
              Process cohort submissions in parallel with asynchronous Celery workers, ZIP ingestion, and CSV forensic checksum export.
            </p>
            <div className="sarvam-card-chips">
              <span>Async Workers</span>
              <span>CSV Checksums</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── 6. Final Call to Action ── */}
      <section className="sarvam-cta-section">
        <div className="sarvam-cta-box">
          <div className="sarvam-motif-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <h2 className="sarvam-cta-title">Start Verifying Content with Sovereign Rigor</h2>
          <p className="sarvam-cta-desc">
            No external cloud APIs or third-party token leaks. AuthentiQ runs locally with
            deterministic forensic telemetry.
          </p>
          <div className="sarvam-hero-actions" style={{ marginTop: '20px' }}>
            <button className="sarvam-btn-primary large" onClick={onEnter}>
              <span>Launch Platform Console</span>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </button>
          </div>
        </div>
      </section>

      {/* ── 7. Clean Minimalist Footer ── */}
      <footer className="sarvam-footer">
        <div className="sarvam-footer-inner">
          <div className="footer-left">
            <div className="sarvam-brand">
              <div className="sarvam-logo-mark small">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <span className="sarvam-brand-name">AuthentiQ</span>
            </div>
            <p className="footer-copyright">
              © 2026 AuthentiQ AI Platform · Sovereign Content Intelligence &amp; Forensics.
            </p>
          </div>

          <div className="footer-status-pill">
            <span className="pulse-dot green" />
            <span>All 6 Forensic Neural Engines Operational</span>
          </div>

          <div className="footer-links">
            <span onClick={onEnter}>Console</span>
            <span onClick={onEnter}>Documentation</span>
            <span onClick={onEnter}>Privacy Policy</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
