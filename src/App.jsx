import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import LandingPage from './pages/LandingPage'
import Dashboard from './pages/Dashboard'
import TextAnalysis from './pages/TextAnalysis'
import MediaAnalysis from './pages/MediaAnalysis'
import Shortlisting from './pages/Shortlisting'
import AuditTrail from './pages/AuditTrail'
import FPFNSimulator from './pages/FPFNSimulator'
import BatchProcessing from './pages/BatchProcessing'
import UserProfile from './pages/UserProfile'
import Toast from './components/Toast'
import './App.css'

export default function App() {
  const [showLanding, setShowLanding] = useState(true)
  const [activePage, setActivePage] = useState('dashboard')
  const [toast, setToast] = useState(null)

  // ── Theme ──────────────────────────────────────────────────
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('aq-theme')
    if (saved) return saved
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('aq-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  // ── Toast ──────────────────────────────────────────────────
  const showToast = (message, type = 'info') => {
    setToast({ message, type, id: Date.now() })
    setTimeout(() => setToast(null), 3800)
  }

  // ── Page registry ──────────────────────────────────────────
  const pages = {
    dashboard: <Dashboard onNavigate={setActivePage} showToast={showToast} />,
    text:      <TextAnalysis showToast={showToast} />,
    media:     <MediaAnalysis showToast={showToast} />,
    shortlist: <Shortlisting showToast={showToast} />,
    audit:     <AuditTrail showToast={showToast} />,
    simulator: <FPFNSimulator showToast={showToast} />,
    batch:     <BatchProcessing showToast={showToast} />,
    profile:   <UserProfile showToast={showToast} onNavigate={setActivePage} />,
  }

  const handleNavigate = (page) => {
    if (page === 'landing') {
      setShowLanding(true)
    } else if (pages[page]) {
      setActivePage(page)
    }
  }

  // ── Landing ────────────────────────────────────────────────
  if (showLanding) {
    return (
      <>
        <LandingPage
          onEnter={(target = 'dashboard') => {
            if (target && pages[target]) {
              setActivePage(target)
            }
            setShowLanding(false)
          }}
          theme={theme}
          toggleTheme={toggleTheme}
        />
        {toast && <Toast key={toast.id} message={toast.message} type={toast.type} />}
      </>
    )
  }

  // ── App Shell ──────────────────────────────────────────────
  return (
    <>
      <Sidebar activePage={activePage} onNavigate={handleNavigate} />
      <div className="main-layout">
        <Topbar
          activePage={activePage}
          onNavigate={handleNavigate}
          theme={theme}
          toggleTheme={toggleTheme}
        />
        <main className="page-content">
          {pages[activePage] || pages['dashboard']}
        </main>
      </div>
      {toast && <Toast key={toast.id} message={toast.message} type={toast.type} />}
    </>
  )
}
