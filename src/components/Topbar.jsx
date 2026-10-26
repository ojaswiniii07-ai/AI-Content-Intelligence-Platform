const labels = {
  dashboard: 'Dashboard', text: 'Text Analysis', media: 'Media Analysis',
  shortlist: 'Shortlisting', audit: 'Audit Trail', simulator: 'FP/FN Simulator', batch: 'Batch Processing'
}

export default function Topbar({ activePage }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="breadcrumb">{labels[activePage] || 'Dashboard'}</div>
      </div>
      <div className="topbar-right">
        <div className="search-box">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" placeholder="Search submissions… (Ctrl+K)" />
        </div>
        <div className="date-filter">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <span>Last 30 days</span>
        </div>
      </div>
    </header>
  )
}
