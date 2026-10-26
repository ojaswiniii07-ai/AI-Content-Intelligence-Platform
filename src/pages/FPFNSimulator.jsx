import { useState } from 'react'

export default function FPFNSimulator({ showToast }) {
  const [model, setModel] = useState('v2.4')
  const [threshold, setThreshold] = useState(0.60)
  const [dataset, setDataset] = useState('edu-2400')
  const [simulating, setSimulating] = useState(false)

  // Dynamically calculate metrics based on threshold
  // Conservative threshold (higher): lower FP, higher FN, higher precision, lower recall
  // Aggressive threshold (lower): higher FP, lower FN, lower precision, higher recall
  const fpRate = (4.1 * Math.pow(1 - threshold + 0.3, 1.8)).toFixed(1)
  const fnRate = (8.7 * Math.pow(threshold + 0.2, 1.6)).toFixed(1)
  const precision = Math.min(99.4, (91.3 + (threshold - 0.6) * 12)).toFixed(1)
  const recall = Math.max(72.0, (94.7 - (threshold - 0.6) * 22)).toFixed(1)

  // Confusion matrix counts for 2,400 labeled samples (1,200 Human, 1,200 AI)
  const totalSamples = 2400
  const actualHuman = 1200
  const actualAI = 1200

  const falsePositives = Math.round((actualHuman * parseFloat(fpRate)) / 100)
  const trueNegatives = actualHuman - falsePositives
  const falseNegatives = Math.round((actualAI * parseFloat(fnRate)) / 100)
  const truePositives = actualAI - falseNegatives

  const handleRunSim = () => {
    setSimulating(true)
    setTimeout(() => {
      setSimulating(false)
      showToast(`Simulation updated for threshold ${threshold.toFixed(2)} on ${totalSamples} samples`, 'success')
    }, 700)
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">False Positive / False Negative Simulator</h1>
          <p className="page-subtitle">Calibrate detector confidence thresholds on labeled benchmarks before cohort deployment</p>
        </div>
        <div className="confidence-pill">
          <span className="pulse-dot" />
          Benchmark Simulator Active
        </div>
      </div>

      <div className="simulator-layout">
        {/* Test configuration card */}
        <div className="card sim-config-card">
          <div className="card-header">
            <h3 className="card-title">Test Configuration</h3>
          </div>

          <div className="form-group">
            <label className="form-label">Detector Model</label>
            <select
              className="filter-select full"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              <option value="v2.4">text-detector-v2.4 (Active Production)</option>
              <option value="v2.3">text-detector-v2.3 (Legacy)</option>
              <option value="v2.2">text-detector-v2.2</option>
              <option value="multimodal-v1">vision-engine-v3.1</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Benchmark Dataset</label>
            <select
              className="filter-select full"
              value={dataset}
              onChange={(e) => setDataset(e.target.value)}
            >
              <option value="edu-2400">Academic Essays (2,400 samples, English)</option>
              <option value="recruiting-1500">Job Cover Letters (1,500 samples)</option>
              <option value="code-900">Technical Proposals (900 samples)</option>
            </select>
            <p className="form-hint">
              ⚠ Small or synthetic samples cannot guarantee real-world cohort performance.
            </p>
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="form-label">Decision Threshold</label>
              <span style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--purple)', fontSize: '0.9rem' }}>
                {threshold.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              className="threshold-slider"
              min="0.20"
              max="0.95"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
            />
            <div className="threshold-labels">
              <span>← Aggressive (Lower FN)</span>
              <span>Conservative (Lower FP) →</span>
            </div>
          </div>

          <button
            className="btn-primary full-width"
            onClick={handleRunSim}
            disabled={simulating}
          >
            {simulating ? 'Re-calculating...' : 'Recalculate Bounds'}
          </button>
        </div>

        {/* Results & Confusion Matrix */}
        <div className="card sim-results-card">
          <div className="card-header">
            <h3 className="card-title">Performance Metrics & Trade-off</h3>
            <span className="card-tag">Threshold: {threshold.toFixed(2)}</span>
          </div>

          <div className="metrics-grid">
            <div className="metric-box">
              <div className="metric-value red">{fpRate}%</div>
              <div className="metric-label">False Positive Rate (FPR)</div>
              <div className="metric-desc">Authentic human flagged as AI</div>
            </div>

            <div className="metric-box">
              <div className="metric-value orange">{fnRate}%</div>
              <div className="metric-label">False Negative Rate (FNR)</div>
              <div className="metric-desc">Synthetic AI missed as human</div>
            </div>

            <div className="metric-box">
              <div className="metric-value green">{precision}%</div>
              <div className="metric-label">Precision</div>
              <div className="metric-desc">Of flagged submissions, actually AI</div>
            </div>

            <div className="metric-box">
              <div className="metric-value cyan">{recall}%</div>
              <div className="metric-label">Recall</div>
              <div className="metric-desc">Proportion of all AI content flagged</div>
            </div>
          </div>

          {/* 2x2 Confusion Matrix Visualization */}
          <div style={{ marginBottom: '16px' }}>
            <h4 className="section-label">Confusion Matrix (N = {totalSamples.toLocaleString()})</h4>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '120px 1fr 1fr',
              gap: '6px',
              fontSize: '0.75rem',
              textAlign: 'center'
            }}>
              <div />
              <div style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Predicted Human</div>
              <div style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Predicted AI Flag</div>

              <div style={{ fontWeight: 600, color: 'var(--text-muted)', textAlign: 'right', paddingRight: '8px' }}>
                Actual Human:
              </div>
              <div style={{ background: 'var(--green-dim)', border: '1px solid rgba(16,185,129,0.3)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--green)', display: 'block' }}>{trueNegatives}</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>True Negative</span>
              </div>
              <div style={{ background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.3)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--red)', display: 'block' }}>{falsePositives}</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>False Positive</span>
              </div>

              <div style={{ fontWeight: 600, color: 'var(--text-muted)', textAlign: 'right', paddingRight: '8px' }}>
                Actual AI:
              </div>
              <div style={{ background: 'var(--orange-dim)', border: '1px solid rgba(249,115,22,0.3)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--orange)', display: 'block' }}>{falseNegatives}</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>False Negative</span>
              </div>
              <div style={{ background: 'var(--purple-dim)', border: '1px solid rgba(168,85,247,0.3)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--purple)', display: 'block' }}>{truePositives}</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>True Positive</span>
              </div>
            </div>
          </div>

          <div className="sim-meta">
            <span>Benchmark: 2,400 stratified samples &middot; English &middot; Model: {model}</span>
            <span>Threshold recommendation for high-stakes decisions: &ge; 0.70</span>
          </div>

          <div className="caveat-box">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <p>
              Performance metrics are valid only for the specific domain, language, and distribution tested. Never extrapolate simulated benchmark accuracy to disparate writing styles or languages.
            </p>
          </div>
        </div>
      </div>
    </>
  )
}
