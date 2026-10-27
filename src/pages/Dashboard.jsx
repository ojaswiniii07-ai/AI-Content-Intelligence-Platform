import { useState, useEffect } from 'react'
import { dashboardApi } from '../services/api'

export default function Dashboard({ onNavigate, showToast }) {
  const [stats, setStats] = useState([
    { label: 'Submissions Analyzed', value: '14,821', change: '+12.4% vs last month', dir: 'positive', color: 'purple',
      extra: <svg className="sparkline" viewBox="0 0 100 28" preserveAspectRatio="none"><defs><linearGradient id="sp1" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#a855f7"/><stop offset="100%" stopColor="#06b6d4"/></linearGradient></defs><polyline points="0,24 16,18 32,20 48,10 64,13 80,6 96,8 100,4" fill="none" stroke="url(#sp1)" strokeWidth="2"/></svg>,
      icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg> },
    { label: 'AI-Flagged Items', value: '3,204', change: '+8.1% vs last month', dir: 'negative', color: 'orange',
      extra: <div className="gauge-wrap"><svg viewBox="0 0 80 48"><path d="M10 43 A30 30 0 0 1 70 43" fill="none" stroke="#1e1e3a" strokeWidth="8" strokeLinecap="round"/><path d="M10 43 A30 30 0 0 1 70 43" fill="none" stroke="#f97316" strokeWidth="8" strokeLinecap="round" strokeDasharray="94" strokeDashoffset="38"/><text x="40" y="40" textAnchor="middle" fill="#cbd5e1" fontSize="9" fontWeight="600">21.6%</text></svg></div>,
      icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> },
    { label: 'Detector Confidence', value: '94.7%', change: '+1.2% model improvement', dir: 'positive', color: 'cyan',
      extra: <div className="gauge-wrap"><svg viewBox="0 0 80 48"><defs><linearGradient id="gc1" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#06b6d4"/><stop offset="100%" stopColor="#a855f7"/></linearGradient></defs><path d="M10 43 A30 30 0 0 1 70 43" fill="none" stroke="#1e1e3a" strokeWidth="8" strokeLinecap="round"/><path d="M10 43 A30 30 0 0 1 70 43" fill="none" stroke="url(#gc1)" strokeWidth="8" strokeLinecap="round" strokeDasharray="94" strokeDashoffset="5"/><text x="40" y="40" textAnchor="middle" fill="#cbd5e1" fontSize="9" fontWeight="600">94.7%</text></svg></div>,
      icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20,6 9,17 4,12"/></svg> },
    { label: 'Human Reviewed', value: '8,106', change: '+22.3% reviewer activity', dir: 'positive', color: 'green',
      extra: <svg className="sparkline" viewBox="0 0 100 28" preserveAspectRatio="none"><defs><linearGradient id="sp2" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#10b981"/><stop offset="100%" stopColor="#06b6d4"/></linearGradient></defs><polyline points="0,26 16,20 32,16 48,18 64,8 80,10 96,4 100,6" fill="none" stroke="url(#sp2)" strokeWidth="2"/></svg>,
      icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/></svg> },
  ])

  const [activities, setActivities] = useState([
    { icon: 'ai-flag', name: 'Essay — Climate Change Policy', meta: 'hackathon-batch-4 · 2 min ago', badge: 'high', badgeLabel: 'High' },
    { icon: 'media',   name: 'Video — Interview Recording',  meta: 'media-queue · 8 min ago',       badge: 'medium', badgeLabel: 'Medium' },
    { icon: 'ok',      name: 'Research Abstract — ML Systems',meta: 'edu-cohort-2026 · 15 min ago', badge: 'low',  badgeLabel: 'Low' },
    { icon: 'ai-flag', name: 'Cover Letter — Product Manager',meta: 'recruiter-portal · 32 min ago',badge: 'high', badgeLabel: 'High' },
    { icon: 'ok',      name: 'Business Case — Supply Chain', meta: 'corp-eval-q4 · 1 hr ago',       badge: 'inconclusive', badgeLabel: 'N/A' },
  ])

  useEffect(() => {
    let mounted = true
    async function loadData() {
      try {
        const metricsRes = await dashboardApi.getMetrics()
        if (mounted && metricsRes?.data?.stats) {
          // Merge incoming values with UI visual elements
          setStats(prev => prev.map((s, idx) => {
            const apiItem = metricsRes.data.stats[idx]
            if (apiItem) {
              return { ...s, value: apiItem.value || s.value, change: apiItem.change || s.change }
            }
            return s
          }))
        }
      } catch {
        // Keeps graceful fallback in offline mode
      }

      try {
        const actRes = await dashboardApi.getActivities()
        if (mounted && actRes?.data && actRes.data.length > 0) {
          setActivities(actRes.data)
        }
      } catch {
        // Keeps fallback
      }
    }
    loadData()
    return () => { mounted = false }
  }, [])

  const modules = [
    { id: 'text',      color: 'purple', label: 'Text + Heatmap',  stat: '9,214 runs', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg> },
    { id: 'media',     color: 'cyan',   label: 'Media Deepfake',  stat: '1,840 runs', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="23,7 16,12 23,17 23,7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg> },
    { id: 'text',      color: 'orange', label: 'Similarity Check',stat: '5,407 runs', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 012 2v7"/><line x1="6" y1="9" x2="6" y2="21"/></svg> },
    { id: 'shortlist', color: 'green',  label: 'Shortlisting',    stat: '2,362 runs', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9,11 12,14 22,4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg> },
  ]

  const ActivityIcon = ({ type }) => {
    const icons = {
      'ai-flag': <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>,
      'media':   <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="23,7 16,12 23,17 23,7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>,
      'ok':      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20,6 9,17 4,12"/></svg>,
    }
    return icons[type] || null
  }

  const UpArrow = () => <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="18,15 12,9 6,15"/></svg>
  const DnArrow = () => <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="18,9 12,15 6,9"/></svg>

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="page-subtitle">Platform-wide intelligence metrics at a glance</p>
        </div>
        <button className="btn-primary" onClick={() => onNavigate('text')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          New Analysis
        </button>
      </div>

      <div className="stats-grid">
        {stats.map((s, i) => (
          <div className="stat-card" key={i}>
            <div className="stat-header">
              <span className="stat-label">{s.label}</span>
              <div className={`stat-icon ${s.color}`}>{s.icon}</div>
            </div>
            <div className="stat-value">{s.value}</div>
            <div className={`stat-change ${s.dir}`}>
              {s.dir === 'positive' ? <UpArrow/> : <DnArrow/>}
              {s.change}
            </div>
            {s.extra}
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        {/* Recent Submissions */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Recent Submissions</h3>
            <button className="card-action-btn" onClick={() => onNavigate('shortlist')}>View all →</button>
          </div>
          <div className="activity-list">
            {activities.map((a, i) => (
              <div className="activity-item" key={i} onClick={() => { onNavigate('text'); showToast(`Opened: ${a.name}`, 'info') }}>
                <div className={`activity-icon ${a.icon}`}><ActivityIcon type={a.icon}/></div>
                <div className="activity-info">
                  <span className="activity-name">{a.name}</span>
                  <span className="activity-meta">{a.meta}</span>
                </div>
                <div className={`activity-badge ${a.badge}`}>{a.badgeLabel}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Analysis Modules */}
        <div className="card">
          <div className="card-header"><h3 className="card-title">Analysis Modules</h3></div>
          <div className="module-grid">
            {modules.map((m, i) => (
              <div className="module-item" key={i} onClick={() => onNavigate(m.id)}>
                <div className={`module-icon ${m.color}`}>{m.icon}</div>
                <span className="module-name">{m.label}</span>
                <span className="module-stat">{m.stat}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Trend Chart */}
        <div className="card card-wide">
          <div className="card-header">
            <h3 className="card-title">Detection Trends</h3>
            <div className="chart-legend">
              <span className="legend-dot purple"></span><span>AI Flagged</span>
              <span className="legend-dot cyan"></span><span>Confirmed Human</span>
              <span className="legend-dot orange"></span><span>Inconclusive</span>
            </div>
          </div>
          <div className="chart-area">
            <svg viewBox="0 0 680 148" preserveAspectRatio="xMidYMid meet" style={{width:'100%',height:'100%'}}>
              <defs>
                <linearGradient id="agP" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#a855f7" stopOpacity="0.35"/><stop offset="100%" stopColor="#a855f7" stopOpacity="0"/></linearGradient>
                <linearGradient id="agC" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#06b6d4" stopOpacity="0.2"/><stop offset="100%" stopColor="#06b6d4" stopOpacity="0"/></linearGradient>
              </defs>
              {[32,64,96,128].map(y => <line key={y} x1="0" y1={y} x2="680" y2={y} stroke="#1a1a2e" strokeWidth="1"/>)}
              <path d="M0,125 C56,95 112,85 170,72 C226,59 282,88 340,62 C398,36 452,52 510,30 C568,8 624,22 680,8 L680,148 L0,148 Z" fill="url(#agP)"/>
              <path d="M0,138 C56,130 112,122 170,112 C226,102 282,120 340,106 C398,92 452,102 510,86 C568,70 624,82 680,62 L680,148 L0,148 Z" fill="url(#agC)"/>
              <path d="M0,125 C56,95 112,85 170,72 C226,59 282,88 340,62 C398,36 452,52 510,30 C568,8 624,22 680,8" fill="none" stroke="#a855f7" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M0,138 C56,130 112,122 170,112 C226,102 282,120 340,106 C398,92 452,102 510,86 C568,70 624,82 680,62" fill="none" stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M0,144 C56,141 112,139 170,137 C226,135 282,141 340,135 C398,129 452,133 510,127 C568,121 624,125 680,119" fill="none" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="4,3"/>
              {[[170,72],[340,62],[510,30],[680,8]].map(([cx,cy],i) => <circle key={i} cx={cx} cy={cy} r="4" fill="#a855f7" stroke="#0d0d1a" strokeWidth="2"/>)}
              {['May','Jun','Jul','Aug','Sep','Oct'].map((m,i) => <text key={m} x={i*110+4} y="145" fill="#4a5568" fontSize="9">{m}</text>)}
            </svg>
          </div>
        </div>

        {/* Cohort Donut */}
        <div className="card">
          <div className="card-header"><h3 className="card-title">Cohort Distribution</h3></div>
          <div className="donut-chart-container">
            <svg viewBox="0 0 160 160" style={{width:'110px',height:'110px',flexShrink:0}}>
              <circle cx="80" cy="80" r="56" fill="none" stroke="#1e1e3a" strokeWidth="18"/>
              <circle cx="80" cy="80" r="56" fill="none" stroke="#a855f7" strokeWidth="18" strokeDasharray="141 211" strokeDashoffset="70" strokeLinecap="round"/>
              <circle cx="80" cy="80" r="56" fill="none" stroke="#06b6d4" strokeWidth="18" strokeDasharray="84 268" strokeDashoffset="-71" strokeLinecap="round"/>
              <circle cx="80" cy="80" r="56" fill="none" stroke="#10b981" strokeWidth="18" strokeDasharray="63 289" strokeDashoffset="-155" strokeLinecap="round"/>
              <circle cx="80" cy="80" r="56" fill="none" stroke="#f97316" strokeWidth="18" strokeDasharray="63 289" strokeDashoffset="-218" strokeLinecap="round"/>
            </svg>
            <div className="donut-legend">
              {[['#a855f7','Education','40%'],['#06b6d4','Recruiting','24%'],['#10b981','Hackathon','18%'],['#f97316','Media','18%']].map(([c,l,v]) => (
                <div className="donut-item" key={l}>
                  <span className="donut-dot" style={{background:c}}/>
                  <span className="donut-label">{l}</span>
                  <span className="donut-val">{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
