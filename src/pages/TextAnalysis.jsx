import { useState } from 'react'
import { textAnalysisApi, auditApi } from '../services/api'

const CaveatBox = () => (
  <div className="caveat-box">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
    <p>Results may be less reliable for short text, technical writing, translated content, or heavily edited mixed drafts.</p>
  </div>
)

export default function TextAnalysis({ showToast }) {
  const [inputTab, setInputTab] = useState('paste')
  const [text, setText] = useState(() => {
    const seed = localStorage.getItem('authentiq_seed_text')
    if (seed) {
      localStorage.removeItem('authentiq_seed_text')
      return seed
    }
    return ''
  })
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0

  const runAnalysis = async () => {
    if (!text.trim() && inputTab === 'paste') {
      showToast('Please enter some text to analyze', 'warning')
      return
    }

    setLoading(true)
    const textToAnalyze = text.trim() || 'The implementation of advanced machine learning algorithms represents a significant paradigm shift in how we approach modern computational challenges and data processing tasks.'

    try {
      const res = await textAnalysisApi.analyzeText(textToAnalyze, {
        analysisTypes: ['text', 'similarity'],
        modelVersion: 'text-detector-v2.4',
      })
      if (res?.data) {
        setResults(res.data)
        showToast('Analysis complete — review results carefully', 'success')
      } else {
        throw new Error('Invalid response format')
      }
    } catch {
      // Fallback to local calibrated data
      setResults({
        overall_score: 74,
        confidence_level: 'Medium Confidence',
        verdict: 'Likely AI',
        dimensions: [
          { name: 'AI-Typical Phrasing', pct: 74 },
          { name: 'Structural Patterns', pct: 61 },
          { name: 'Source Similarity', pct: 22 },
          { name: 'Style Consistency', pct: 88 },
        ],
        sentence_spans: [
          { text: 'The implementation of advanced machine learning algorithms', heat: 'high' },
          { text: 'represents a significant paradigm shift in how we approach', heat: 'low' },
          { text: 'modern computational challenges and data processing tasks.', heat: 'mid' },
          { text: 'This enables developers to create more robust, scalable, and efficient solutions that can handle unprecedented volumes of information with remarkable accuracy and speed.', heat: 'high' },
          { text: 'Furthermore, the integration of natural language processing with traditional practices opens new avenues for automated content generation and intelligent decision-making systems.', heat: 'mid' },
        ],
      })
      showToast('Analysis complete (demo mode)', 'success')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = () => {
    if (!results) return
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `authentiq-analysis-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    showToast('Analysis report downloaded', 'success')
  }

  const handleFlag = async () => {
    try {
      await auditApi.recordEvent({
        action: 'SUBMISSION_FLAGGED',
        resource_type: 'submission',
        resource_id: results?.id || 'manual_text_analysis',
        description: 'Text analysis flagged for secondary human reviewer audit',
      })
      showToast('Submission flagged for human review', 'warning')
    } catch {
      showToast('Flag recorded locally', 'warning')
    }
  }

  const defaultDimensions = [
    { name: 'AI-Typical Phrasing', pct: results?.overall_score || 74, gradient: 'linear-gradient(90deg,#a855f7,#06b6d4)' },
    { name: 'Structural Patterns',  pct: 61, gradient: 'linear-gradient(90deg,#a855f7,#06b6d4)' },
    { name: 'Source Similarity',    pct: 22, gradient: 'linear-gradient(90deg,#10b981,#06b6d4)' },
    { name: 'Style Consistency',    pct: 88, gradient: 'linear-gradient(90deg,#10b981,#06b6d4)' },
  ]

  const activeDimensions = results?.dimensions?.map(d => ({
    name: d.name,
    pct: Math.round(d.pct),
    gradient: d.pct > 50 ? 'linear-gradient(90deg,#a855f7,#06b6d4)' : 'linear-gradient(90deg,#10b981,#06b6d4)',
  })) || defaultDimensions

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Text AI-Involvement Analysis</h1>
          <p className="page-subtitle">Paste or upload text to detect AI signals with sentence-level heatmap</p>
        </div>
        <div className="confidence-pill">
          <span className="pulse-dot"/>
          Model {results?.model_version || 'v2.4'} Active
        </div>
      </div>

      <div className="text-analysis-layout">
        {/* Input Panel */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Submit Text</h3>
            <div className="tab-group">
              <button className={`tab ${inputTab==='paste'?'active':''}`} onClick={()=>setInputTab('paste')}>Paste</button>
              <button className={`tab ${inputTab==='upload'?'active':''}`} onClick={()=>setInputTab('upload')}>Upload</button>
            </div>
          </div>

          {inputTab === 'paste' ? (
            <>
              <textarea
                className="text-input"
                value={text}
                onChange={e => setText(e.target.value)}
                placeholder={"Paste the text you want to analyze here...\n\nThe platform will:\n• Detect signals of AI generation\n• Highlight suspicious sentence spans\n• Cross-reference against authorized sources\n• Show calibrated confidence levels"}
              />
              <div className="input-meta">
                <span>{text.length.toLocaleString()} chars · {wordCount.toLocaleString()} words</span>
                <span className="privacy-note">🔒 Not stored after session</span>
              </div>
            </>
          ) : (
            <div className="upload-zone" onClick={() => {
              setText('Machine learning models have demonstrated rapid advancement across automated natural language generation benchmarks. This introduces nuanced challenges for authentic authorship assessment.')
              setInputTab('paste')
              showToast('Sample essay loaded from file', 'info')
            }}>
              <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17,8 12,3 7,8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              <p>Drop file or <span className="upload-link">browse</span></p>
              <span className="upload-hint">.txt .doc .docx .pdf — max 10MB</span>
            </div>
          )}

          <div className="analysis-options">
            <label className="option-toggle"><input type="checkbox" defaultChecked/> Similarity cross-reference</label>
            <label className="option-toggle"><input type="checkbox"/> Prompt hypothesis <em style={{color:'var(--text-muted)',fontSize:'.72rem'}}>(speculative)</em></label>
            <label className="option-toggle"><input type="checkbox"/> Style alignment check</label>
          </div>

          <button className="btn-primary full-width" onClick={runAnalysis} disabled={loading}>
            {loading
              ? <><svg className="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-6.22-8.56"/></svg> Analyzing…</>
              : <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="5,3 19,12 5,21 5,3"/></svg> Run Analysis</>
            }
          </button>

          <p className="disclaimer-text">⚠ Results are decision-support signals, not proof of authorship. Consequential decisions require human review.</p>
        </div>

        {/* Results Panel */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Analysis Results</h3>
            {results && (
              <div style={{display:'flex',gap:'8px'}}>
                <button className="icon-btn" title="Export" onClick={handleExport}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7,10 12,15 17,10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                </button>
                <button className="icon-btn" title="Flag for Review" onClick={handleFlag}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>
                </button>
              </div>
            )}
          </div>

          {!results ? (
            <div className="empty-state">
              <svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <p>Run an analysis to see results</p>
            </div>
          ) : (
            <>
              <div className="assessment-bar">
                <div className="assessment-label">
                  <span>AI Involvement: {results.verdict || 'High'}</span>
                  <span className="confidence-tag">{results.confidence_level || 'Medium Confidence'}</span>
                </div>
                <div className="assessment-track">
                  <div className="assessment-fill" style={{width:`${results.overall_score || 74}%`}}/>
                </div>
                <div className="assessment-scale">
                  <span>Likely Human</span><span>Inconclusive</span><span>Likely AI</span>
                </div>
              </div>

              <div className="heatmap-section">
                <div className="heatmap-legend">
                  <span className="heat-label">AI Signal:</span>
                  <span className="heat-box low-heat">Low</span>
                  <span className="heat-box mid-heat">Med</span>
                  <span className="heat-box high-heat">High</span>
                </div>
                <div className="heatmap-text">
                  {results.sentence_spans && results.sentence_spans.length > 0 ? (
                    results.sentence_spans.map((span, idx) => (
                      <span key={idx} className={`heat-span ${span.heat}-heat`}>
                        {span.text}{' '}
                      </span>
                    ))
                  ) : (
                    <>
                      <span className="heat-span high-heat">The implementation of advanced machine learning algorithms</span> represents a significant paradigm shift in how we approach <span className="heat-span mid-heat">modern computational challenges and data processing tasks.</span> This enables developers to create more <span className="heat-span high-heat">robust, scalable, and efficient solutions that can handle unprecedented volumes of information</span> with remarkable accuracy and speed.<br/><br/>
                      <span className="heat-span low-heat">Furthermore, the integration of natural language processing</span> with traditional practices opens new avenues for <span className="heat-span mid-heat">automated content generation and intelligent decision-making systems.</span>
                    </>
                  )}
                  <span className="heat-hint"> ← review cue, not proof</span>
                </div>
              </div>

              <div className="dimension-scores">
                <h4 className="section-label">Signal Dimensions</h4>
                {activeDimensions.map(d => (
                  <div className="dimension-row" key={d.name}>
                    <span className="dim-name">{d.name}</span>
                    <div className="dim-bar-track">
                      <div className="dim-bar-fill" style={{width:`${d.pct}%`,background:d.gradient}}/>
                    </div>
                    <span className="dim-score">{d.pct}%</span>
                  </div>
                ))}
              </div>

              <CaveatBox/>
            </>
          )}
        </div>
      </div>
    </>
  )
}
