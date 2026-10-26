import { useState } from 'react'

const CaveatBox = ({ text }) => (
  <div className="caveat-box">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
    <p>{text || 'Deepfake signals are probabilistic indicators. Ambient lighting, video compression, or network artifacts can trigger false cues. Require secondary human verification before action.'}</p>
  </div>
)

export default function MediaAnalysis({ showToast }) {
  const [activeDetectors, setActiveDetectors] = useState([
    'Face Blend Artifacts',
    'Lighting Inconsistency',
    'Facial Motion',
    'Audio/Video Sync'
  ])
  const [analyzing, setAnalyzing] = useState(false)
  const [resultsReady, setResultsReady] = useState(true)
  const [selectedFile, setSelectedFile] = useState(null)
  const [activeFrame, setActiveFrame] = useState(4)

  const allDetectors = [
    'Face Blend Artifacts',
    'Lighting Inconsistency',
    'Facial Motion',
    'Audio/Video Sync',
    'Metadata Provenance',
    'Compression Analysis'
  ]

  const toggleDetector = (det) => {
    if (activeDetectors.includes(det)) {
      setActiveDetectors(activeDetectors.filter(d => d !== det))
    } else {
      setActiveDetectors([...activeDetectors, det])
    }
  }

  const handleSimulateUpload = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file.name)
      showToast(`Selected file: ${file.name}`, 'info')
    }
  }

  const triggerAnalysis = () => {
    setAnalyzing(true)
    setTimeout(() => {
      setAnalyzing(false)
      setResultsReady(true)
      showToast('Media analysis finished. 3 anomaly signals detected.', 'success')
    }, 1800)
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Media Deepfake Analysis</h1>
          <p className="page-subtitle">Detect manipulation artifacts in images, video, and audio with frame-level visualization</p>
        </div>
        <div className="confidence-pill">
          <span className="pulse-dot" />
          Vision-Audio Engine v3.1
        </div>
      </div>

      <div className="media-layout">
        <div className="card media-upload-card">
          <div className="card-header">
            <h3 className="card-title">Upload Media</h3>
            <span className="card-tag">Async Processing</span>
          </div>

          <label className="upload-zone large" style={{ cursor: 'pointer' }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <polygon points="23,7 16,12 23,17 23,7"/>
              <rect x="1" y="5" width="15" height="14" rx="2"/>
            </svg>
            <p>{selectedFile ? selectedFile : 'Drop video, image, or audio here'}</p>
            <span className="upload-hint">MP4, MOV, JPG, PNG, WAV — max 500MB</span>
            <input type="file" onChange={handleSimulateUpload} style={{ display: 'none' }} accept="video/*,image/*,audio/*" />
            <button type="button" className="btn-secondary" style={{ marginTop: '8px' }} onClick={(e) => {
              e.stopPropagation()
              e.currentTarget.parentElement.querySelector('input')?.click()
            }}>
              Browse Files
            </button>
          </label>

          <div className="detector-options">
            <h4 className="section-label">Active Detectors ({activeDetectors.length}/6)</h4>
            <div className="detector-grid">
              {allDetectors.map(det => {
                const isActive = activeDetectors.includes(det)
                return (
                  <button
                    key={det}
                    type="button"
                    className={`detector-chip ${isActive ? 'active' : ''}`}
                    onClick={() => toggleDetector(det)}
                  >
                    {det} {isActive ? '✓' : '+'}
                  </button>
                )
              })}
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <button
              className="btn-primary full-width"
              disabled={analyzing}
              onClick={triggerAnalysis}
            >
              {analyzing ? (
                <>
                  <svg className="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/></svg>
                  Processing Media Frames...
                </>
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="5,3 19,12 5,21 5,3"/></svg>
                  Analyze Authenticity
                </>
              )}
            </button>
          </div>

          <div style={{ marginTop: '16px' }}>
            <CaveatBox text="Artifact cues are indicators of potential synthetic manipulation. They do not constitute formal legal forensics." />
          </div>
        </div>

        <div className="card media-results-card">
          <div className="card-header">
            <h3 className="card-title">Artifact Visualization & Frame Heatmap</h3>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="icon-btn" title="Download report" onClick={() => showToast('Report downloaded', 'success')}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7,10 12,15 17,10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              </button>
              <button className="icon-btn" title="Flag for manual review" onClick={() => showToast('Flagged for Tier-2 Human Review', 'warning')}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>
              </button>
            </div>
          </div>

          {resultsReady ? (
            <>
              <div className="assessment-bar">
                <div className="assessment-label">
                  <span>Synthetic Manipulation Probability: 68.4%</span>
                  <span className="confidence-tag" style={{ background: 'var(--orange-dim)', color: 'var(--orange)' }}>
                    Suspicious Artifacts
                  </span>
                </div>
                <div className="assessment-track">
                  <div className="assessment-fill" style={{ width: '68.4%' }} />
                </div>
                <div className="assessment-scale">
                  <span>Authentic (0%)</span>
                  <span>Uncertain (50%)</span>
                  <span>Deepfake Synthetic (100%)</span>
                </div>
              </div>

              <div className="media-preview-area" style={{ position: 'relative', overflow: 'hidden', padding: 0 }}>
                {/* SVG Visual Frame Inspector */}
                <div style={{ width: '100%', height: '220px', background: '#0a0a16', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                  <svg viewBox="0 0 400 200" style={{ width: '100%', height: '100%' }}>
                    {/* Simulated video frame with bounding boxes and heat overlay */}
                    <rect x="0" y="0" width="400" height="200" fill="#0d0d1f" />
                    {/* Mock subject silhouette */}
                    <ellipse cx="200" cy="110" rx="42" ry="54" fill="#1e1e38" stroke="#334155" strokeWidth="1.5" />
                    <circle cx="200" cy="80" r="28" fill="#2a2a4c" />
                    {/* Anomaly bounding heat zones */}
                    <rect x="178" y="74" width="44" height="26" fill="rgba(239,68,68,0.25)" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="3,2" rx="4" />
                    <text x="180" y="70" fill="#ef4444" fontSize="8" fontWeight="bold">Face Blend δ: 0.84</text>
                    
                    <rect x="170" y="105" width="60" height="24" fill="rgba(249,115,22,0.2)" stroke="#f97316" strokeWidth="1.2" strokeDasharray="3,2" rx="4" />
                    <text x="172" y="101" fill="#f97316" fontSize="8" fontWeight="bold">Audio Sync: -83ms</text>
                    
                    {/* Timeline overlay on bottom */}
                    <rect x="10" y="170" width="380" height="18" fill="rgba(15,23,42,0.85)" rx="4" />
                    {/* Scrubber markers */}
                    <rect x="16" y="176" width="30" height="6" fill="#10b981" rx="2" />
                    <rect x="52" y="176" width="80" height="6" fill="#ef4444" rx="2" />
                    <rect x="138" y="176" width="40" height="6" fill="#f97316" rx="2" />
                    <rect x="184" y="176" width="200" height="6" fill="#334155" rx="2" />
                    
                    {/* Cursor scrubber */}
                    <line x1={activeFrame * 36 + 40} y1="166" x2={activeFrame * 36 + 40} y2="192" stroke="#a855f7" strokeWidth="2.5" />
                  </svg>
                  
                  <div style={{ position: 'absolute', bottom: '8px', right: '12px', fontSize: '0.68rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.6)', padding: '2px 8px', borderRadius: '4px' }}>
                    Frame {activeFrame * 12 + 18} / 360 (00:0{activeFrame}.42s)
                  </div>
                </div>
              </div>

              {/* Scrubber controls */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Timeline Scrub:</span>
                <input
                  type="range"
                  min="1"
                  max="8"
                  value={activeFrame}
                  onChange={(e) => setActiveFrame(Number(e.target.value))}
                  style={{ flex: 1, accentColor: 'var(--purple)', cursor: 'pointer' }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                  00:0{activeFrame}.00
                </span>
              </div>

              <div className="signal-list">
                <div className="signal-item">
                  <div className="signal-icon orange">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
                  </div>
                  <div className="signal-info">
                    <span className="signal-name">Blending Boundary Artifact at frame 0:04–0:09</span>
                    <span className="signal-desc">High gradient inconsistency along mandibular jawline & hairline. Common with face-swap synthesis.</span>
                  </div>
                </div>

                <div className="signal-item">
                  <div className="signal-icon yellow">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  </div>
                  <div className="signal-info">
                    <span className="signal-name">Phoneme-to-Viseme Audio Sync Deviation: -83ms</span>
                    <span className="signal-desc">Slight desynchronization between lip articulation and audio track. Within compression variance range.</span>
                  </div>
                </div>

                <div className="signal-item">
                  <div className="signal-icon green">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20,6 9,17 4,12"/></svg>
                  </div>
                  <div className="signal-info">
                    <span className="signal-name">Metadata Provenance Intact</span>
                    <span className="signal-desc">EXIF timestamps and encoding headers match valid hardware camera device profiles.</span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1"><polygon points="23,7 16,12 23,17 23,7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
              <p>Upload a video or audio file to inspect frame-level manipulation signals</p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
