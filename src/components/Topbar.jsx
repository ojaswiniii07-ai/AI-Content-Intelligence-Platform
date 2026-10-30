const labels = {
  dashboard: 'Forensic Dashboard',
  text:      'Text Forensics & Attribution',
  media:     'Media & Video Dissection',
  shortlist: 'Decoupled Shortlisting Studio',
  audit:     'SHA-256 Chained Audit Trail',
  simulator: 'FP / FN Threshold Simulator',
  batch:     'High-Throughput Batch Ingestion',
  profile:   'Forensic Lead Profile',
}

export default function Topbar({ activePage, onNavigate, theme, toggleTheme }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span
            style={{
              background: 'var(--color-pink)',
              color: '#FFFFFF',
              fontWeight: 900,
              fontSize: '0.7rem',
              padding: '2px 8px',
              border: '2px solid #121316',
              boxShadow: '2px 2px 0px #121316',
              transform: 'rotate(-2deg)',
            }}
          >
            MODULE
          </span>
          <div className="breadcrumb">{labels[activePage] || 'Dashboard'}</div>
        </div>
      </div>

      <div className="topbar-right">
        {/* Search */}
        <div className="search-box">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" placeholder="Search hash, candidate, scan… (Ctrl+K)" />
        </div>

        {/* Notifications */}
        <button className="topbar-icon-btn" title="Audit Alerts">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 01-3.46 0"/>
          </svg>
        </button>

        {/* Theme Toggle */}
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Switch to Day Mode' : 'Switch to Night Mode'}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>
              <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
            </svg>
          )}
        </button>

        {/* User Avatar → Profile */}
        <button
          className="user-card"
          style={{ padding: '4px 10px', marginLeft: '4px' }}
          onClick={() => onNavigate('profile')}
          title="Account Settings"
        >
          <div className="user-avatar">SA</div>
          <span style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Sanyam
          </span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ color: 'var(--text-primary)' }}>
            <polyline points="6,9 12,15 18,9"/>
          </svg>
        </button>
      </div>
    </header>
  )
}
