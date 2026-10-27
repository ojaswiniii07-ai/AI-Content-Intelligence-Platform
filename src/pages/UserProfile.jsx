import { useState } from 'react'

export default function UserProfile({ showToast, onNavigate }) {
  const [activeSection, setActiveSection] = useState('profile')
  const [user, setUser] = useState({
    name: 'Sanyam Aggarwal',
    email: 'sanyam@authentiq.ai',
    role: 'Admin',
    organization: 'AuthentiQ Platform',
    bio: 'AI integrity researcher and platform administrator.',
    initials: 'SA',
  })
  const [saving, setSaving] = useState(false)
  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    highRiskFlags: true,
    weeklyDigest: false,
    modelUpdates: true,
  })

  const sectionNav = [
    { id: 'profile',       label: 'Profile',        icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg> },
    { id: 'notifications', label: 'Notifications',  icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg> },
    { id: 'security',      label: 'Security',       icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg> },
    { id: 'appearance',    label: 'Appearance',     icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg> },
    { id: 'api',           label: 'API Keys',       icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 017.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg> },
  ]

  const handleSave = async () => {
    setSaving(true)
    await new Promise(r => setTimeout(r, 600))
    setSaving(false)
    showToast('Profile updated successfully', 'success')
  }

  const toggleNotif = (key) => {
    setNotifications(prev => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Account Settings</h1>
          <p className="page-subtitle">Manage your profile, preferences, and security</p>
        </div>
        <button className="btn-secondary" onClick={() => onNavigate('dashboard')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
          Back to Dashboard
        </button>
      </div>

      <div className="profile-layout">
        {/* Left Nav */}
        <div className="card profile-nav-card" style={{ alignSelf: 'start', gap: '2px', padding: '10px' }}>
          {sectionNav.map(s => (
            <button
              key={s.id}
              className={`profile-nav-item ${activeSection === s.id ? 'active' : ''}`}
              onClick={() => setActiveSection(s.id)}
            >
              {s.icon}
              <span>{s.label}</span>
            </button>
          ))}
        </div>

        {/* Right Content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Profile Section */}
          {activeSection === 'profile' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Personal Information</h3>
              </div>

              {/* Avatar */}
              <div style={{ marginBottom: '24px' }}>
                <div className="section-label">Profile Photo</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div className="avatar-large">{user.initials}</div>
                  <div>
                    <button className="btn-secondary" style={{ marginBottom: '6px', display: 'block' }}>
                      Upload Photo
                    </button>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>JPG, PNG or GIF · max 2MB</div>
                  </div>
                </div>
              </div>

              <div className="divider" />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Full Name</label>
                    <input
                      className="form-input"
                      value={user.name}
                      onChange={e => setUser(u => ({ ...u, name: e.target.value }))}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Email Address</label>
                    <input
                      className="form-input"
                      type="email"
                      value={user.email}
                      onChange={e => setUser(u => ({ ...u, email: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Role</label>
                    <select
                      className="form-select"
                      value={user.role}
                      onChange={e => setUser(u => ({ ...u, role: e.target.value }))}
                    >
                      <option value="Admin">Admin</option>
                      <option value="Reviewer">Reviewer</option>
                      <option value="Analyst">Analyst</option>
                      <option value="Viewer">Viewer</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Organization</label>
                    <input
                      className="form-input"
                      value={user.organization}
                      onChange={e => setUser(u => ({ ...u, organization: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Bio</label>
                  <textarea
                    className="form-textarea"
                    value={user.bio}
                    onChange={e => setUser(u => ({ ...u, bio: e.target.value }))}
                    rows={3}
                    style={{ minHeight: '80px' }}
                  />
                  <span className="form-hint">Appears on audit trail entries and exported reports.</span>
                </div>

                <div style={{ display: 'flex', gap: '10px', paddingTop: '4px' }}>
                  <button className="btn-primary" onClick={handleSave} disabled={saving}>
                    {saving ? (
                      <>
                        <svg className="spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/></svg>
                        Saving…
                      </>
                    ) : 'Save Changes'}
                  </button>
                  <button className="btn-secondary">Cancel</button>
                </div>
              </div>
            </div>
          )}

          {/* Notifications */}
          {activeSection === 'notifications' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Notification Preferences</h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                {[
                  { key: 'emailAlerts',    label: 'Email Alerts',      desc: 'Receive email notifications for completed analyses' },
                  { key: 'highRiskFlags',  label: 'High-Risk Flags',   desc: 'Instant notification when a high-risk submission is detected' },
                  { key: 'weeklyDigest',   label: 'Weekly Digest',     desc: 'Aggregated weekly report of platform activity' },
                  { key: 'modelUpdates',   label: 'Model Updates',     desc: 'Get notified when ML models are retrained or improved' },
                ].map(({ key, label, desc }) => (
                  <div key={key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 0', borderBottom: '1px solid var(--border)' }}>
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '3px' }}>{label}</div>
                      <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>{desc}</div>
                    </div>
                    <button
                      onClick={() => toggleNotif(key)}
                      style={{
                        width: '42px', height: '24px', borderRadius: '12px',
                        background: notifications[key] ? 'var(--indigo)' : 'var(--bg-elevated)',
                        border: '1px solid ' + (notifications[key] ? 'var(--indigo)' : 'var(--border-strong)'),
                        cursor: 'pointer', transition: 'var(--transition)',
                        position: 'relative', flexShrink: 0,
                      }}
                      aria-label={`Toggle ${label}`}
                    >
                      <div style={{
                        width: '16px', height: '16px', borderRadius: '50%', background: 'white',
                        position: 'absolute', top: '3px',
                        left: notifications[key] ? '22px' : '3px',
                        transition: 'var(--transition)',
                        boxShadow: '0 1px 3px rgba(0,0,0,.2)',
                      }} />
                    </button>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: '20px' }}>
                <button className="btn-primary" onClick={() => showToast('Notification preferences saved', 'success')}>
                  Save Preferences
                </button>
              </div>
            </div>
          )}

          {/* Security */}
          {activeSection === 'security' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Change Password</h3>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div className="form-group">
                    <label className="form-label">Current Password</label>
                    <input className="form-input" type="password" placeholder="••••••••" />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">New Password</label>
                      <input className="form-input" type="password" placeholder="••••••••" />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Confirm Password</label>
                      <input className="form-input" type="password" placeholder="••••••••" />
                    </div>
                  </div>
                  <div>
                    <button className="btn-primary" onClick={() => showToast('Password updated successfully', 'success')}>
                      Update Password
                    </button>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Two-Factor Authentication</h3>
                  <span className="card-tag">Recommended</span>
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.6 }}>
                  Add an extra layer of security to your account. When 2FA is enabled, you'll need a verification code in addition to your password.
                </p>
                <button className="btn-secondary" onClick={() => showToast('2FA setup coming soon', 'info')}>
                  Enable 2FA
                </button>
              </div>

              <div className="danger-zone">
                <div className="danger-zone-title">⚠ Danger Zone</div>
                <div className="danger-zone-desc">
                  Permanently delete your account and all associated data. This action cannot be undone.
                </div>
                <button className="btn-danger" onClick={() => showToast('Account deletion requires email confirmation', 'warning')}>
                  Delete Account
                </button>
              </div>
            </div>
          )}

          {/* Appearance */}
          {activeSection === 'appearance' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Appearance</h3>
              </div>
              <div className="section-label" style={{ marginBottom: '14px' }}>Color Theme</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '24px' }}>
                {[
                  { id: 'light', label: 'Light', preview: '#ffffff' },
                  { id: 'dark', label: 'Dark', preview: '#0c0e14' },
                  { id: 'system', label: 'System', preview: 'linear-gradient(135deg, #ffffff 50%, #0c0e14 50%)' },
                ].map(t => (
                  <button
                    key={t.id}
                    onClick={() => showToast(`Theme: ${t.label} (use the toggle in topbar)`, 'info')}
                    style={{
                      padding: '16px', border: '2px solid var(--border)', borderRadius: 'var(--radius)',
                      background: 'var(--bg-elevated)', cursor: 'pointer', transition: 'var(--transition)',
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px',
                    }}
                  >
                    <div style={{ width: '48px', height: '32px', borderRadius: '6px', background: t.preview, border: '1px solid var(--border)' }} />
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>{t.label}</span>
                  </button>
                ))}
              </div>

              <div className="divider" />

              <div className="section-label" style={{ marginBottom: '14px' }}>Font Size</div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {['Small', 'Medium', 'Large'].map(size => (
                  <button key={size} className={`detector-chip ${size === 'Medium' ? 'active' : ''}`} onClick={() => showToast(`Font size: ${size}`, 'info')}>
                    {size}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* API Keys */}
          {activeSection === 'api' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">API Keys</h3>
                <button className="btn-secondary" style={{ fontSize: '0.78rem' }} onClick={() => showToast('API key generated', 'success')}>
                  + Generate New Key
                </button>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: 1.6 }}>
                Use API keys to integrate AuthentiQ into your own applications. Keys are scoped per workspace and can be revoked at any time.
              </p>

              {[
                { name: 'Production API Key', created: 'Oct 15, 2025', lastUsed: '2 hours ago', status: 'active' },
                { name: 'Staging API Key', created: 'Sep 1, 2025', lastUsed: '3 days ago', status: 'active' },
              ].map((key, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 0', borderBottom: '1px solid var(--border)' }}>
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                      {key.name}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', gap: '12px' }}>
                      <span>Created {key.created}</span>
                      <span>Last used {key.lastUsed}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span className="status-pill low">Active</span>
                    <button className="icon-btn" onClick={() => showToast(`API key copied to clipboard`, 'info')} title="Copy key">
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                      </svg>
                    </button>
                    <button className="icon-btn" onClick={() => showToast('API key revoked', 'warning')} title="Revoke key">
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3,6 5,6 21,6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
