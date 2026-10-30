export default function Sidebar({ activePage, onNavigate }) {
  const navItems = [
    {
      section: 'Forensics Studio',
      items: [
        {
          id: 'dashboard',
          label: 'Dashboard',
          badge: null,
          icon: (
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <rect x="3" y="3" width="7" height="7" rx="0"/>
              <rect x="14" y="3" width="7" height="7" rx="0"/>
              <rect x="3" y="14" width="7" height="7" rx="0"/>
              <rect x="14" y="14" width="7" height="7" rx="0"/>
            </svg>
          ),
        },
        {
          id: 'text',
          label: 'Text Analysis',
          badge: 'ML',
          icon: (
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          ),
        },
        {
          id: 'media',
          label: 'Media Analysis',
          badge: 'Deepfake',
          icon: (
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <polygon points="23,7 16,12 23,17 23,7"/>
              <rect x="1" y="5" width="15" height="14" rx="0"/>
            </svg>
          ),
        },
        {
          id: 'shortlist',
          label: 'Shortlisting',
          badge: 'Gemma 4',
          icon: (
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="8" y1="6" x2="21" y2="6"/>
              <line x1="8" y1="12" x2="21" y2="12"/>
              <line x1="8" y1="18" x2="21" y2="18"/>
              <line x1="3" y1="6" x2="3.01" y2="6"/>
              <line x1="3" y1="12" x2="3.01" y2="12"/>
              <line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
          ),
        },
      ],
    },
    {
      section: 'Governance & Audits',
      items: [
        {
          id: 'audit',
          label: 'Audit Trail',
          badge: 'SHA-256',
          icon: (
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          ),
        },
        {
          id: 'simulator',
          label: 'FP/FN Simulator',
          badge: null,
          icon: (
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
            </svg>
          ),
        },
        {
          id: 'batch',
          label: 'Batch Processing',
          badge: null,
          icon: (
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
            </svg>
          ),
        },
      ],
    },
  ]

  return (
    <aside className="sidebar">
      {/* Memphis Brand Logo */}
      <div
        className="sidebar-logo"
        onClick={() => onNavigate('landing')}
        style={{ cursor: 'pointer' }}
        title="Return to AuthentiQ Memphis Landing Page"
      >
        <div className="logo-mark">
          <span>Q</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="logo-text">AuthentiQ</span>
          </div>
          <span style={{ fontSize: '0.62rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
            FORENSIC STUDIO
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {navItems.map((group) => (
          <div key={group.section} style={{ marginBottom: '10px' }}>
            <div className="nav-section-label">{group.section}</div>
            {group.items.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                onClick={() => onNavigate(item.id)}
              >
                {item.icon}
                <span>{item.label}</span>
                {item.badge && <span className="nav-badge">{item.badge}</span>}
              </button>
            ))}
          </div>
        ))}
      </nav>

      {/* Memphis Footer / User Card */}
      <div className="sidebar-footer">
        <div
          className="user-card"
          onClick={() => onNavigate('profile')}
          title="Account Settings"
        >
          <div className="user-avatar">SA</div>
          <div className="user-info">
            <span className="user-name">Sanyam Aggarwal</span>
            <span className="user-role">★ Forensic Lead</span>
          </div>
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            style={{ marginLeft: 'auto', flexShrink: 0, color: 'var(--text-primary)' }}
          >
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
          </svg>
        </div>
      </div>
    </aside>
  )
}
