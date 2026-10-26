import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import Dashboard from './pages/Dashboard'
import TextAnalysis from './pages/TextAnalysis'
import MediaAnalysis from './pages/MediaAnalysis'
import Shortlisting from './pages/Shortlisting'
import AuditTrail from './pages/AuditTrail'
import FPFNSimulator from './pages/FPFNSimulator'
import BatchProcessing from './pages/BatchProcessing'
import Toast from './components/Toast'
import './App.css'

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [toast, setToast] = useState(null)

  const showToast = (message, type = 'info') => {
    setToast({ message, type, id: Date.now() })
    setTimeout(() => setToast(null), 3800)
  }

  const pages = {
    dashboard: <Dashboard onNavigate={setActivePage} showToast={showToast} />,
    text:      <TextAnalysis showToast={showToast} />,
    media:     <MediaAnalysis showToast={showToast} />,
    shortlist: <Shortlisting showToast={showToast} />,
    audit:     <AuditTrail showToast={showToast} />,
    simulator: <FPFNSimulator showToast={showToast} />,
    batch:     <BatchProcessing showToast={showToast} />,
  }

  return (
    <>
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <div className="main-layout">
        <Topbar activePage={activePage} onNavigate={setActivePage} />
        <main className="page-content">
          {pages[activePage]}
        </main>
      </div>
      {toast && <Toast key={toast.id} message={toast.message} type={toast.type} />}
    </>
  )
}
