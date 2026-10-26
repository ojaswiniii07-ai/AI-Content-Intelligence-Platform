export default function Sidebar({ activePage, onNavigate }) {
  const navItems = [
    {
      section: 'Main',
      items: [
        { id: 'dashboard', label: 'Dashboard', badge: null, icon: (
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
        )},
        { id: 'text', label: 'Text Analysis', badge: 'New', icon: (
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
            <polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
        )},
        { id: 'media', label: 'Media Analysis', badge: null, icon: (
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="23,7 16,12 23,17 23,7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
          </svg>
        )},
        { id: 'shortlist', label: 'Shortlisting', badge: null, icon: (
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
        )},
      ]
    },
    {
      section: 'Analysis',
      items: [
        { id: 'audit', label: 'Audit Trail', badge: null, icon: (
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        )},
        { id: 'simulator', label: 'FP/FN Simulator', badge: null, icon: (
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
          </svg>
        )},
        { id: 'batch', label: 'Batch Processing', badge: null, icon: (
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
          </svg>
        )},
      ]
    }
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
          </svg>
        </div>
        <span className="logo-text">ContentIQ</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(group => (
          <div key={group.section}>
            <div className="nav-section-label">{group.section}</div>
            {group.items.map(item => (
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

      <div className="sidebar-footer">
        <div className="user-card">
          <div className="user-avatar">OJ</div>
          <div className="user-info">
            <span className="user-name">Ojaswini</span>
            <span className="user-role">Admin</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
