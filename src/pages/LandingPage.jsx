import { useState, useEffect } from 'react'

export default function LandingPage({ onEnter, theme = 'light', toggleTheme }) {
  const [activeInspectorSample, setActiveInspectorSample] = useState('ai') // 'ai' | 'human'
  const [pricingCycle, setPricingCycle] = useState('monthly') // 'monthly' | 'annual'
  const [copiedKey, setCopiedKey] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  // Floating shape positions / animations
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const handleMouseMove = (e) => {
      // Gentle parallax effect for Memphis floating decorations
      const x = (e.clientX / window.innerWidth - 0.5) * 20
      const y = (e.clientY / window.innerHeight - 0.5) * 20
      setMousePos({ x, y })
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  const copySampleApiKey = () => {
    navigator.clipboard?.writeText?.('aq_live_authentiq_9883f82a991c0e')
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2400)
  }

  return (
    <div className={`memphis-root ${theme === 'dark' ? 'memphis-dark' : 'memphis-light'}`}>
      {/* ── EMBEDDED MEMPHIS CSS SYSTEM ── */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,700;1,900&family=JetBrains+Mono:wght@400;600;700&display=swap');

        :root {
          --color-pink: #FF1493;
          --color-blue: #0066FF;
          --color-yellow: #FFD700;
          --color-red: #FF3333;
          --color-green: #00E5A0;
          --color-coral: #FF7F50;
          --color-purple: #9B59B6;
          --color-turquoise: #1ABC9C;
          --color-black: #121316;
          --color-white: #FFFFFF;
          --color-offwhite: #F8F9FA;
          --font-primary: 'Poppins', system-ui, -apple-system, sans-serif;
          --font-mono: 'JetBrains Mono', monospace;
          --border: 3px solid #121316;
          --border-thick: 4px solid #121316;
          --shadow-memphis: 6px 6px 0px #121316;
          --shadow-memphis-sm: 4px 4px 0px #121316;
          --shadow-memphis-lg: 10px 10px 0px #121316;
          --shadow-memphis-pink: 6px 6px 0px #FF1493;
          --shadow-memphis-yellow: 6px 6px 0px #FFD700;
          --shadow-memphis-blue: 6px 6px 0px #0066FF;
          --radius-sharp: 0px;
          --radius-pill: 9999px;
        }

        .memphis-root {
          font-family: var(--font-primary);
          --text-color-primary: #121316;
          --text-color-secondary: #333333;
          --nav-bg: #FFFFFF;
          --nav-text: #121316;
          color: var(--text-color-primary);
          background-color: #FAFAFA;
          background-image: 
            radial-gradient(#0066FF 1.5px, transparent 1.5px),
            radial-gradient(#FF1493 1.5px, transparent 1.5px);
          background-size: 36px 36px;
          background-position: 0 0, 18px 18px;
          min-height: 100vh;
          overflow-x: hidden;
          position: relative;
          box-sizing: border-box;
        }

        .memphis-root * {
          box-sizing: border-box;
        }

        /* Dark mode variant (80s Neon Synth / Dark Memphis) */
        .memphis-root.memphis-dark {
          --text-color-primary: #FFFFFF;
          --text-color-secondary: #E2E8F0;
          --nav-bg: #16171D;
          --nav-text: #FFFFFF;
          background-color: #16171D;
          color: var(--text-color-primary);
          background-image: 
            radial-gradient(rgba(0, 229, 160, 0.25) 1.5px, transparent 1.5px),
            radial-gradient(rgba(255, 20, 147, 0.25) 1.5px, transparent 1.5px);
          --border: 3px solid #FFFFFF;
          --border-thick: 4px solid #FFFFFF;
          --shadow-memphis: 6px 6px 0px #FFD700;
          --shadow-memphis-sm: 4px 4px 0px #00E5A0;
          --shadow-memphis-lg: 10px 10px 0px #FF1493;
        }

        /* Postmodern Memphis Buttons */
        .memphis-btn {
          font-family: var(--font-primary);
          font-weight: 800;
          font-size: 0.95rem;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          padding: 12px 24px;
          border: var(--border-thick);
          border-radius: var(--radius-sharp);
          cursor: pointer;
          transition: all 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          text-decoration: none;
          position: relative;
          user-select: none;
        }

        .memphis-btn:hover {
          transform: translate(-3px, -3px);
        }

        .memphis-btn:active {
          transform: translate(2px, 2px);
          box-shadow: 2px 2px 0px #121316 !important;
        }

        .btn-yellow {
          background: var(--color-yellow);
          color: var(--color-black);
          box-shadow: var(--shadow-memphis);
        }
        .btn-yellow:hover {
          box-shadow: 9px 9px 0px var(--color-black);
        }

        .btn-pink {
          background: var(--color-pink);
          color: var(--color-white);
          box-shadow: var(--shadow-memphis);
        }
        .btn-pink:hover {
          box-shadow: 9px 9px 0px var(--color-black);
        }

        .btn-blue {
          background: var(--color-blue);
          color: var(--color-white);
          box-shadow: var(--shadow-memphis);
        }
        .btn-blue:hover {
          box-shadow: 9px 9px 0px var(--color-black);
        }

        .btn-green {
          background: var(--color-green);
          color: var(--color-black);
          box-shadow: var(--shadow-memphis);
        }
        .btn-green:hover {
          box-shadow: 9px 9px 0px var(--color-black);
        }

        .btn-outline {
          background: var(--color-white);
          color: var(--color-black);
          box-shadow: var(--shadow-memphis);
        }
        .btn-outline:hover {
          box-shadow: 9px 9px 0px var(--color-black);
          background: var(--color-yellow);
        }

        /* Memphis Card System */
        .memphis-card {
          border: var(--border-thick);
          border-radius: var(--radius-sharp);
          background: var(--color-white);
          color: var(--color-black);
          box-shadow: var(--shadow-memphis);
          transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
          position: relative;
        }

        .memphis-card:hover {
          transform: translateY(-4px) rotate(1deg);
          box-shadow: var(--shadow-memphis-lg);
        }

        /* Memphis Badge Chips */
        .memphis-tag {
          font-family: var(--font-primary);
          font-size: 0.75rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          padding: 4px 10px;
          border: 2px solid var(--color-black);
          border-radius: var(--radius-sharp);
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }

        /* Geometric Floating Background Sprites */
        .shape-triangle {
          width: 0;
          height: 0;
          border-left: 20px solid transparent;
          border-right: 20px solid transparent;
          border-bottom: 35px solid var(--color-pink);
          filter: drop-shadow(4px 4px 0px var(--color-black));
          position: absolute;
          pointer-events: none;
        }

        .shape-circle {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          border: 3px solid var(--color-black);
          background: var(--color-yellow);
          box-shadow: 4px 4px 0px var(--color-black);
          position: absolute;
          pointer-events: none;
        }

        .shape-squiggle {
          position: absolute;
          pointer-events: none;
        }

        .shape-cross {
          position: absolute;
          pointer-events: none;
          font-size: 2rem;
          font-weight: 900;
          color: var(--color-blue);
          line-height: 1;
          user-select: none;
        }

        /* Striped retro patterns */
        .pattern-stripes-yellow {
          background: repeating-linear-gradient(
            45deg,
            var(--color-yellow),
            var(--color-yellow) 10px,
            #FFE033 10px,
            #FFE033 20px
          );
        }

        .pattern-stripes-pink {
          background: repeating-linear-gradient(
            -45deg,
            var(--color-pink),
            var(--color-pink) 10px,
            #FF3399 10px,
            #FF3399 20px
          );
        }

        .pattern-dots {
          background-image: radial-gradient(#121316 2px, transparent 2px);
          background-size: 14px 14px;
        }

        /* Retro Marquee Strip */
        @keyframes marqueeAnim {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }

        .marquee-track {
          display: flex;
          width: 200%;
          animation: marqueeAnim 20s linear infinite;
        }

        .marquee-track:hover {
          animation-play-state: paused;
        }

        /* 3D Perspective Hero Container */
        .hero-perspective-box {
          perspective: 1200px;
        }

        .hero-3d-card {
          transform-style: preserve-3d;
          transition: transform 0.4s ease;
        }

        .hero-3d-card:hover {
          transform: rotateX(4deg) rotateY(-6deg) rotateZ(1deg);
        }

        /* Responsive Breakpoints */
        @media (max-width: 900px) {
          .memphis-grid-3 {
            grid-template-columns: 1fr !important;
          }
          .memphis-hero-split {
            grid-template-columns: 1fr !important;
          }
          .memphis-nav-links {
            display: none !important;
          }
          .memphis-nav-links.mobile-open {
            display: flex !important;
            flex-direction: column;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: #FFFFFF;
            border-bottom: var(--border-thick);
            padding: 20px;
            gap: 15px;
            box-shadow: var(--shadow-memphis-lg);
          }
        }
      `}</style>

      {/* ── BACKGROUND FLOATING MEMPHIS ELEMENTS ── */}
      <div
        className="shape-triangle"
        style={{
          top: '12%',
          left: '4%',
          transform: `translate(${mousePos.x * 0.8}px, ${mousePos.y * 0.8}px) rotate(15deg)`,
          borderBottomColor: '#FF1493',
        }}
      />
      <div
        className="shape-circle"
        style={{
          top: '25%',
          right: '5%',
          transform: `translate(${mousePos.x * -0.6}px, ${mousePos.y * -0.6}px)`,
          background: '#FFD700',
        }}
      />
      <div
        className="shape-cross"
        style={{
          top: '48%',
          left: '2%',
          transform: `translate(${mousePos.x * 0.5}px, ${mousePos.y * 0.5}px) rotate(25deg)`,
          color: '#0066FF',
        }}
      >
        ✦
      </div>
      <div
        className="shape-triangle"
        style={{
          top: '70%',
          right: '3%',
          transform: `translate(${mousePos.x * -0.7}px, ${mousePos.y * -0.7}px) rotate(-40deg)`,
          borderBottomColor: '#00E5A0',
        }}
      />
      <div
        className="shape-cross"
        style={{
          top: '88%',
          left: '6%',
          transform: `translate(${mousePos.x * 0.9}px, ${mousePos.y * 0.9}px)`,
          color: '#FF3333',
        }}
      >
        ✚
      </div>

      {/* ── TOP ANNOUNCEMENT TICKER (MARQUEE) ── */}
      <div
        style={{
          background: 'var(--color-yellow)',
          borderBottom: 'var(--border)',
          overflow: 'hidden',
          padding: '8px 0',
          position: 'relative',
          zIndex: 40,
        }}
      >
        <div className="marquee-track">
          <div style={{ display: 'flex', gap: '40px', alignItems: 'center', whiteSpace: 'nowrap' }}>
            <span style={{ fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              ⚡ AUTHENTIQ V2.4 LAUNCHED: OPENROUTER GEMMA-4 31B EVALUATOR ACTIVE
            </span>
            <span>★</span>
            <span style={{ fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              ✦ SUB-SECOND ATTRIBUTION WITH SGD + LIGHTGBM FORENSIC ENSEMBLE
            </span>
            <span>★</span>
            <span style={{ fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              ▲ CRYPTOGRAPHIC SHA-256 AUDIT TRAILS: ZERO DISQUALIFICATION BIAS
            </span>
            <span>★</span>
            <span style={{ fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              ◼ SOVEREIGN MULTIMODAL FORENSIC INTELLIGENCE
            </span>
          </div>
          <div style={{ display: 'flex', gap: '40px', alignItems: 'center', whiteSpace: 'nowrap' }}>
            <span style={{ fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              ⚡ AUTHENTIQ V2.4 LAUNCHED: OPENROUTER GEMMA-4 31B EVALUATOR ACTIVE
            </span>
            <span>★</span>
            <span style={{ fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              ✦ SUB-SECOND ATTRIBUTION WITH SGD + LIGHTGBM FORENSIC ENSEMBLE
            </span>
            <span>★</span>
            <span style={{ fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              ▲ CRYPTOGRAPHIC SHA-256 AUDIT TRAILS: ZERO DISQUALIFICATION BIAS
            </span>
            <span>★</span>
            <span style={{ fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              ◼ SOVEREIGN MULTIMODAL FORENSIC INTELLIGENCE
            </span>
          </div>
        </div>
      </div>

      {/* ── NAVBAR ── */}
      <header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          background: 'var(--nav-bg)',
          borderBottom: 'var(--border-thick)',
          padding: '14px 24px',
        }}
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '20px',
          }}
        >
          {/* Brand Logo */}
          <div
            onClick={() => onEnter?.('dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            <div
              style={{
                width: '42px',
                height: '42px',
                background: 'var(--color-pink)',
                border: '3px solid var(--color-black)',
                boxShadow: '3px 3px 0px var(--color-black)',
                transform: 'rotate(-4deg)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF',
                fontWeight: 900,
                fontSize: '1.4rem',
              }}
            >
              Q
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    fontFamily: 'var(--font-primary)',
                    fontWeight: 900,
                    fontSize: '1.45rem',
                    letterSpacing: '-0.02em',
                    color: 'var(--nav-text)',
                    textTransform: 'uppercase',
                  }}
                >
                  Authenti<span style={{ color: 'var(--color-blue)' }}>Q</span>
                </span>
              </div>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-color-secondary)', letterSpacing: '0.04em' }}>
                AI CONTENT FORENSICS PLATFORM
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav
            className={`memphis-nav-links ${menuOpen ? 'mobile-open' : ''}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '26px',
            }}
          >
            <a
              href="#features"
              style={{
                fontFamily: 'var(--font-primary)',
                fontWeight: 700,
                fontSize: '0.88rem',
                color: 'var(--nav-text)',
                textDecoration: 'none',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                padding: '4px 6px',
                borderBottom: '2px solid transparent',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => (e.target.style.borderBottom = '2px solid var(--color-pink)')}
              onMouseLeave={(e) => (e.target.style.borderBottom = '2px solid transparent')}
            >
              Features
            </a>
            <a
              href="#inspector"
              style={{
                fontFamily: 'var(--font-primary)',
                fontWeight: 700,
                fontSize: '0.88rem',
                color: 'var(--nav-text)',
                textDecoration: 'none',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                padding: '4px 6px',
                borderBottom: '2px solid transparent',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => (e.target.style.borderBottom = '2px solid var(--color-blue)')}
              onMouseLeave={(e) => (e.target.style.borderBottom = '2px solid transparent')}
            >
              Live Dissection
            </a>
            <a
              href="#use-cases"
              style={{
                fontFamily: 'var(--font-primary)',
                fontWeight: 700,
                fontSize: '0.88rem',
                color: 'var(--nav-text)',
                textDecoration: 'none',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                padding: '4px 6px',
                borderBottom: '2px solid transparent',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => (e.target.style.borderBottom = '2px solid var(--color-green)')}
              onMouseLeave={(e) => (e.target.style.borderBottom = '2px solid transparent')}
            >
              Use Cases
            </a>
            <a
              href="#pricing"
              style={{
                fontFamily: 'var(--font-primary)',
                fontWeight: 700,
                fontSize: '0.88rem',
                color: 'var(--nav-text)',
                textDecoration: 'none',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                padding: '4px 6px',
                borderBottom: '2px solid transparent',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => (e.target.style.borderBottom = '2px solid var(--color-yellow)')}
              onMouseLeave={(e) => (e.target.style.borderBottom = '2px solid transparent')}
            >
              Pricing
            </a>
          </nav>

          {/* Action Buttons & Theme Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Theme Toggle Button */}
            <button
              onClick={toggleTheme}
              className="memphis-btn"
              style={{
                padding: '8px 12px',
                background: theme === 'dark' ? '#FFD700' : '#121316',
                color: theme === 'dark' ? '#121316' : '#FFFFFF',
                boxShadow: '3px 3px 0px var(--color-black)',
                fontSize: '0.78rem',
              }}
              title="Toggle Day / Night Mode"
            >
              {theme === 'dark' ? '☀️ DAY' : '🌙 NIGHT'}
            </button>

            {/* Main Launch CTA */}
            <button
              onClick={() => onEnter?.('dashboard')}
              className="memphis-btn btn-pink"
              style={{
                padding: '10px 20px',
                fontSize: '0.85rem',
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              <span>Launch Studio</span>
            </button>

            {/* Mobile Hamburger */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="memphis-btn"
              style={{
                display: 'none',
                padding: '8px 10px',
                background: '#FFFFFF',
              }}
              id="memphis-mobile-menu-btn"
            >
              ☰
            </button>
          </div>
        </div>
      </header>

      {/* ── HERO SECTION ── */}
      <section
        style={{
          position: 'relative',
          padding: '60px 24px 80px',
          maxWidth: '1280px',
          margin: '0 auto',
        }}
      >
        <div
          className="memphis-hero-split"
          style={{
            display: 'grid',
            gridTemplateColumns: '1.15fr 0.85fr',
            gap: '40px',
            alignItems: 'center',
          }}
        >
          {/* Left Hero Content */}
          <div>
            {/* Eyebrow Pill */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 14px',
                background: 'var(--color-yellow)',
                border: 'var(--border)',
                boxShadow: '4px 4px 0px var(--color-black)',
                transform: 'rotate(-2deg)',
                marginBottom: '24px',
              }}
            >
              <span style={{ fontSize: '1rem' }}>⚡</span>
              <span style={{ fontWeight: 800, fontSize: '0.78rem', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                POSTMODERN AI CONTENT FORENSICS &amp; ATTRIBUTION
              </span>
            </div>

            {/* Impactful Headline */}
            <h1
              style={{
                fontFamily: 'var(--font-primary)',
                fontWeight: 900,
                fontSize: 'clamp(2.4rem, 5.2vw, 4.2rem)',
                lineHeight: 1.08,
                letterSpacing: '-0.03em',
                textTransform: 'uppercase',
                margin: '0 0 22px 0',
                color: 'var(--text-color-primary)',
              }}
            >
              KILL THE{' '}
              <span
                style={{
                  background: 'var(--color-pink)',
                  color: '#FFFFFF',
                  padding: '2px 10px',
                  display: 'inline-block',
                  border: '3px solid var(--color-black)',
                  boxShadow: '4px 4px 0px var(--color-black)',
                  transform: 'rotate(1deg)',
                }}
              >
                SYNTHETIC.
              </span>
              <br />
              PROVE THE{' '}
              <span
                style={{
                  background: 'var(--color-blue)',
                  color: '#FFFFFF',
                  padding: '2px 10px',
                  display: 'inline-block',
                  border: '3px solid var(--color-black)',
                  boxShadow: '4px 4px 0px var(--color-black)',
                  transform: 'rotate(-1.5deg)',
                }}
              >
                AUTHENTIC.
              </span>
            </h1>

            {/* Subtitle */}
            <p
              style={{
                fontSize: '1.12rem',
                lineHeight: 1.6,
                fontWeight: 500,
                color: 'var(--text-color-secondary)',
                maxWidth: '580px',
                margin: '0 0 34px 0',
              }}
            >
              AuthentiQ delivers calibrated ML text attribution, facial video deepfake dissection, and decoupled rubric evaluation. Zero false-positive bias against classical writing, backed by tamper-evident SHA-256 audit ledgers.
            </p>

            {/* Dual Hero Buttons */}
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '36px' }}>
              <button
                onClick={() => onEnter?.('dashboard')}
                className="memphis-btn btn-yellow"
                style={{
                  fontSize: '1rem',
                  padding: '16px 32px',
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                <span>Start Free Forensics</span>
              </button>

              <button
                onClick={() => onEnter?.('text')}
                className="memphis-btn btn-outline"
                style={{
                  fontSize: '1rem',
                  padding: '16px 28px',
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <span>Try Live Inspector</span>
              </button>
            </div>

            {/* Micro Feature Proof Badges */}
            <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'center' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: '#FFFFFF',
                  color: '#121316',
                  border: '2px solid var(--color-black)',
                  padding: '6px 12px',
                  boxShadow: '2px 2px 0px var(--color-black)',
                  fontSize: '0.78rem',
                  fontWeight: 800,
                }}
              >
                <span style={{ color: 'var(--color-green)', fontSize: '1.1rem', fontWeight: 900 }}>✓</span>
                <span>Sub-Second Latency</span>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: '#FFFFFF',
                  color: '#121316',
                  border: '2px solid var(--color-black)',
                  padding: '6px 12px',
                  boxShadow: '2px 2px 0px var(--color-black)',
                  fontSize: '0.78rem',
                  fontWeight: 800,
                }}
              >
                <span style={{ color: 'var(--color-blue)', fontSize: '1.1rem', fontWeight: 900 }}>✓</span>
                <span>OpenRouter Gemma 4 Evaluator</span>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: '#FFFFFF',
                  color: '#121316',
                  border: '2px solid var(--color-black)',
                  padding: '6px 12px',
                  boxShadow: '2px 2px 0px var(--color-black)',
                  fontSize: '0.78rem',
                  fontWeight: 800,
                }}
              >
                <span style={{ color: 'var(--color-pink)', fontSize: '1.1rem', fontWeight: 900 }}>✓</span>
                <span>Decoupled Rubric Ethics</span>
              </div>
            </div>
          </div>

          {/* Right Hero: 3D / Abstract Memphis Interactive Element */}
          <div className="hero-perspective-box">
            <div
              className="hero-3d-card memphis-card"
              style={{
                padding: '24px',
                background: 'var(--color-white)',
                border: 'var(--border-thick)',
                boxShadow: '12px 12px 0px var(--color-black)',
                position: 'relative',
              }}
            >
              {/* Card Retro Header Bar */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: 'var(--border)',
                  paddingBottom: '14px',
                  marginBottom: '18px',
                }}
              >
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ width: '14px', height: '14px', borderRadius: '50%', background: 'var(--color-red)', border: '2px solid var(--color-black)' }} />
                  <span style={{ width: '14px', height: '14px', borderRadius: '50%', background: 'var(--color-yellow)', border: '2px solid var(--color-black)' }} />
                  <span style={{ width: '14px', height: '14px', borderRadius: '50%', background: 'var(--color-green)', border: '2px solid var(--color-black)' }} />
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    background: 'var(--color-yellow)',
                    padding: '2px 8px',
                    border: '1.5px solid var(--color-black)',
                  }}
                >
                  FORENSIC_STREAM://ACTIVE
                </div>
              </div>

              {/* Sample Selector Tabs */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '18px' }}>
                <button
                  type="button"
                  onClick={() => setActiveInspectorSample('ai')}
                  className="memphis-btn"
                  style={{
                    padding: '8px 12px',
                    fontSize: '0.76rem',
                    background: activeInspectorSample === 'ai' ? 'var(--color-pink)' : '#FFFFFF',
                    color: activeInspectorSample === 'ai' ? '#FFFFFF' : 'var(--color-black)',
                    boxShadow: activeInspectorSample === 'ai' ? '3px 3px 0px var(--color-black)' : 'none',
                  }}
                >
                  🤖 Synthetic AI Sample
                </button>
                <button
                  type="button"
                  onClick={() => setActiveInspectorSample('human')}
                  className="memphis-btn"
                  style={{
                    padding: '8px 12px',
                    fontSize: '0.76rem',
                    background: activeInspectorSample === 'human' ? 'var(--color-green)' : '#FFFFFF',
                    color: activeInspectorSample === 'human' ? '#121316' : 'var(--color-black)',
                    boxShadow: activeInspectorSample === 'human' ? '3px 3px 0px var(--color-black)' : 'none',
                  }}
                >
                  ✍️ Human Masterpiece
                </button>
              </div>

              {/* Live Detection Visual Feedback */}
              {activeInspectorSample === 'ai' ? (
                <div
                  style={{
                    background: '#FFF5F8',
                    border: '2px solid var(--color-pink)',
                    padding: '16px',
                    marginBottom: '16px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span style={{ fontWeight: 800, fontSize: '0.82rem', color: 'var(--color-pink)' }}>
                      AI PROBABILITY: 98.4%
                    </span>
                    <span
                      style={{
                        background: 'var(--color-red)',
                        color: '#FFFFFF',
                        fontWeight: 800,
                        fontSize: '0.68rem',
                        padding: '3px 8px',
                        border: '1.5px solid var(--color-black)',
                      }}
                    >
                      HIGHLY LIKELY AI
                    </span>
                  </div>

                  {/* Highlighted text preview */}
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', lineHeight: 1.5, margin: 0, color: '#333' }}>
                    <span style={{ background: '#FFB6C1', borderBottom: '2px solid #FF1493' }}>
                      "In today's fast-paced digital ecosystem, the integration of artificial intelligence is paramount.
                    </span>{' '}
                    <span style={{ background: '#FFE4E1', borderBottom: '2px solid #FF69B4' }}>
                      Furthermore, delving into automated intelligence systems streamlines operational workflows."
                    </span>
                  </p>

                  <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                    <span className="memphis-tag" style={{ background: 'var(--color-yellow)', fontSize: '0.65rem' }}>
                      Low Burstiness
                    </span>
                    <span className="memphis-tag" style={{ background: 'var(--color-pink)', color: '#FFF', fontSize: '0.65rem' }}>
                      Formulaic Connectors
                    </span>
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    background: '#F0FFF8',
                    border: '2px solid var(--color-green)',
                    padding: '16px',
                    marginBottom: '16px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span style={{ fontWeight: 800, fontSize: '0.82rem', color: '#00875A' }}>
                      AI PROBABILITY: 15.5%
                    </span>
                    <span
                      style={{
                        background: 'var(--color-green)',
                        color: '#121316',
                        fontWeight: 800,
                        fontSize: '0.68rem',
                        padding: '3px 8px',
                        border: '1.5px solid var(--color-black)',
                      }}
                    >
                      LIKELY HUMAN
                    </span>
                  </div>

                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', lineHeight: 1.5, margin: 0, color: '#333' }}>
                    <span style={{ background: '#D2FBD4' }}>
                      "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife."
                    </span>{' '}
                    — Jane Austen, Pride &amp; Prejudice
                  </p>

                  <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                    <span className="memphis-tag" style={{ background: 'var(--color-green)', fontSize: '0.65rem' }}>
                      Rich Classical Vocab
                    </span>
                    <span className="memphis-tag" style={{ background: 'var(--color-yellow)', fontSize: '0.65rem' }}>
                      High Organic Variance
                    </span>
                  </div>
                </div>
              )}

              {/* Bottom Card Controls */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'var(--color-black)',
                  color: '#FFFFFF',
                  padding: '10px 14px',
                  border: '2px solid var(--color-black)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-green)' }} />
                  <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    LATENCY: 42ms
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => onEnter?.('shortlist')}
                  style={{
                    background: 'var(--color-yellow)',
                    border: 'none',
                    fontWeight: 800,
                    fontSize: '0.72rem',
                    padding: '4px 10px',
                    cursor: 'pointer',
                    textTransform: 'uppercase',
                  }}
                >
                  Test In Studio →
                </button>
              </div>

              {/* Floating Decorative Memphis Badge */}
              <div
                style={{
                  position: 'absolute',
                  top: '-16px',
                  right: '-16px',
                  background: 'var(--color-yellow)',
                  border: '3px solid var(--color-black)',
                  boxShadow: '4px 4px 0px var(--color-black)',
                  transform: 'rotate(12deg)',
                  padding: '6px 12px',
                  fontWeight: 900,
                  fontSize: '0.74rem',
                  textTransform: 'uppercase',
                }}
              >
                ★ CALIBRATED ML
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── ZIGZAG SVG SEPARATOR ── */}
      <div style={{ width: '100%', height: '24px', overflow: 'hidden', lineHeight: 0 }}>
        <svg viewBox="0 0 1200 24" preserveAspectRatio="none" style={{ width: '100%', height: '24px' }}>
          <path
            d="M0,0 L20,24 L40,0 L60,24 L80,0 L100,24 L120,0 L140,24 L160,0 L180,24 L200,0 L220,24 L240,0 L260,24 L280,0 L300,24 L320,0 L340,24 L360,0 L380,24 L400,0 L420,24 L440,0 L460,24 L480,0 L500,24 L520,0 L540,24 L560,0 L580,24 L600,0 L620,24 L640,0 L660,24 L680,0 L700,24 L720,0 L740,24 L760,0 L780,24 L800,0 L820,24 L840,0 L860,24 L880,0 L900,24 L920,0 L940,24 L960,0 L980,24 L1000,0 L1020,24 L1040,0 L1060,24 L1080,0 L1100,24 L1120,0 L1140,24 L1160,0 L1180,24 L1200,0 V24 H0 Z"
            fill="var(--color-blue)"
          />
        </svg>
      </div>

      {/* ── FEATURES SECTION (3 DISTINCT CARDS) ── */}
      <section
        id="features"
        style={{
          background: 'var(--color-blue)',
          padding: '80px 24px',
          borderBottom: 'var(--border-thick)',
          color: '#FFFFFF',
          position: 'relative',
        }}
      >
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          {/* Section Header */}
          <div style={{ textAlign: 'center', marginBottom: '50px' }}>
            <span
              className="memphis-tag"
              style={{
                background: 'var(--color-yellow)',
                color: 'var(--color-black)',
                marginBottom: '14px',
                fontSize: '0.8rem',
                transform: 'rotate(-2deg)',
              }}
            >
              ✦ FORENSIC CAPABILITIES
            </span>
            <h2
              style={{
                fontFamily: 'var(--font-primary)',
                fontWeight: 900,
                fontSize: 'clamp(2rem, 4vw, 3.2rem)',
                textTransform: 'uppercase',
                letterSpacing: '-0.02em',
                margin: '10px 0',
                color: '#FFFFFF',
              }}
            >
              UNCOMPROMISED DETECTION ENGINES
            </h2>
            <p style={{ maxWidth: '640px', margin: '0 auto', fontSize: '1rem', color: '#E0E7FF', fontWeight: 500 }}>
              Three specialized intelligence modules engineered to eradicate synthetic manipulation without penalizing human intellectual merit.
            </p>
          </div>

          {/* 3 Features Cards Grid */}
          <div
            className="memphis-grid-3"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '30px',
            }}
          >
            {/* Feature Card 1: Text Forensics */}
            <div
              className="memphis-card"
              style={{
                padding: '32px 24px',
                background: '#FFFFFF',
                color: 'var(--color-black)',
              }}
            >
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  background: 'var(--color-pink)',
                  border: 'var(--border)',
                  boxShadow: '4px 4px 0px var(--color-black)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                  transform: 'rotate(-4deg)',
                }}
              >
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
              </div>

              <span className="memphis-tag" style={{ background: 'var(--color-pink)', color: '#FFF', marginBottom: '12px' }}>
                SGD + LightGBM
              </span>

              <h3 style={{ fontSize: '1.35rem', fontWeight: 800, margin: '8px 0 14px', textTransform: 'uppercase' }}>
                Calibrated Text Forensics
              </h3>

              <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#444', marginBottom: '20px' }}>
                Dual-stage ensemble combining sub-word char n-grams, word TF-IDF, and 12-dimensional linguistic burstiness vectors. Accurately flags ChatGPT while preserving classical prose.
              </p>

              <ul style={{ paddingLeft: '18px', margin: '0 0 24px', fontSize: '0.82rem', color: '#222', lineHeight: 1.7, fontWeight: 600 }}>
                <li>Sentence-level heat attribution</li>
                <li>Zero out-of-domain prompt leakage</li>
                <li>Vectorized batching under 60ms</li>
              </ul>

              <button
                type="button"
                onClick={() => onEnter?.('text')}
                className="memphis-btn btn-yellow"
                style={{ width: '100%', fontSize: '0.78rem', padding: '10px' }}
              >
                Open Text Forensics →
              </button>
            </div>

            {/* Feature Card 2: Deepfake & Video Dissection */}
            <div
              className="memphis-card"
              style={{
                padding: '32px 24px',
                background: '#FFFFFF',
                color: 'var(--color-black)',
                transform: 'translateY(-10px)',
              }}
            >
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  background: 'var(--color-yellow)',
                  border: 'var(--border)',
                  boxShadow: '4px 4px 0px var(--color-black)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                  transform: 'rotate(5deg)',
                }}
              >
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-black)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="23 7 16 12 23 17 23 7" />
                  <rect x="1" y="5" width="15" height="14" rx="0" ry="0" />
                </svg>
              </div>

              <span className="memphis-tag" style={{ background: 'var(--color-yellow)', color: 'var(--color-black)', marginBottom: '12px' }}>
                MTCNN + EfficientNet
              </span>

              <h3 style={{ fontSize: '1.35rem', fontWeight: 800, margin: '8px 0 14px', textTransform: 'uppercase' }}>
                Facial Deepfake Dissection
              </h3>

              <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#444', marginBottom: '20px' }}>
                Frame-by-frame convolutional facial landmark analysis detecting blend-boundary synthesis, frequency domain artifacts, and temporal micro-jitter across high-resolution video streams.
              </p>

              <ul style={{ paddingLeft: '18px', margin: '0 0 24px', fontSize: '0.82rem', color: '#222', lineHeight: 1.7, fontWeight: 600 }}>
                <li>Temporal frame glitch tracking</li>
                <li>Facial boundary heat maps</li>
                <li>Deepfake probability confidence</li>
              </ul>

              <button
                type="button"
                onClick={() => onEnter?.('media')}
                className="memphis-btn btn-pink"
                style={{ width: '100%', fontSize: '0.78rem', padding: '10px' }}
              >
                Dissect Media Frames →
              </button>
            </div>

            {/* Feature Card 3: Decoupled Recruiter Shortlister */}
            <div
              className="memphis-card"
              style={{
                padding: '32px 24px',
                background: '#FFFFFF',
                color: 'var(--color-black)',
              }}
            >
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  background: 'var(--color-green)',
                  border: 'var(--border)',
                  boxShadow: '4px 4px 0px var(--color-black)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                  transform: 'rotate(-3deg)',
                }}
              >
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-black)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                  <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>
              </div>

              <span className="memphis-tag" style={{ background: 'var(--color-green)', color: 'var(--color-black)', marginBottom: '12px' }}>
                Gemma 4 31B OpenRouter
              </span>

              <h3 style={{ fontSize: '1.35rem', fontWeight: 800, margin: '8px 0 14px', textTransform: 'uppercase' }}>
                Decoupled Candidate Studio
              </h3>

              <p style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#444', marginBottom: '20px' }}>
                Evaluates resumes and hackathon submissions on technical depth and reasoning. AI is monitored as an advisory metric — never disqualifying candidates solely for assistive AI.
              </p>

              <ul style={{ paddingLeft: '18px', margin: '0 0 24px', fontSize: '0.82rem', color: '#222', lineHeight: 1.7, fontWeight: 600 }}>
                <li>CSV file dataset drag-and-drop</li>
                <li>Hackathon vs Resume preset modes</li>
                <li>Dynamic rubric weight recalibration</li>
              </ul>

              <button
                type="button"
                onClick={() => onEnter?.('shortlist')}
                className="memphis-btn btn-green"
                style={{ width: '100%', fontSize: '0.78rem', padding: '10px' }}
              >
                Launch Shortlisting →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── LIVE INTERACTIVE INSPECTOR PREVIEW (SECTION 4) ── */}
      <section
        id="inspector"
        style={{
          padding: '80px 24px',
          maxWidth: '1280px',
          margin: '0 auto',
        }}
      >
        <div
          className="memphis-card"
          style={{
            background: 'var(--color-white)',
            padding: '40px',
            border: 'var(--border-thick)',
            boxShadow: 'var(--shadow-memphis-lg)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '20px',
              borderBottom: 'var(--border)',
              paddingBottom: '24px',
              marginBottom: '30px',
            }}
          >
            <div>
              <span className="memphis-tag" style={{ background: 'var(--color-pink)', color: '#FFF', marginBottom: '8px' }}>
                ⚡ REALTIME INFERENCE RUNTIME
              </span>
              <h3 style={{ margin: '6px 0 0', fontSize: '1.8rem', fontWeight: 900, textTransform: 'uppercase' }}>
                Interactive Verification Terminal
              </h3>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                onClick={copySampleApiKey}
                className="memphis-btn btn-yellow"
                style={{ fontSize: '0.78rem', padding: '10px 18px' }}
              >
                {copiedKey ? '✓ API Key Copied!' : '📋 Copy Demo API Key'}
              </button>
              <button
                type="button"
                onClick={() => onEnter?.('dashboard')}
                className="memphis-btn btn-blue"
                style={{ fontSize: '0.78rem', padding: '10px 18px' }}
              >
                Open Terminal
              </button>
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '24px',
            }}
            className="memphis-hero-split"
          >
            {/* Terminal Input Box */}
            <div
              style={{
                background: '#1A1C23',
                color: '#A0AEC0',
                padding: '20px',
                border: '3px solid var(--color-black)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.82rem',
              }}
            >
              <div style={{ color: '#00E5A0', marginBottom: '12px', fontWeight: 700 }}>
                // INPUT BUFFER: STDIN TEXT (54 WORDS)
              </div>
              <div style={{ color: '#FFFFFF', lineHeight: 1.6 }}>
                "In today's rapidly evolving digital landscape, organizations are increasingly turning to cloud-native paradigms to optimize their operational workflows. Furthermore, by delving deep into artificial intelligence and automated orchestration, enterprises can foster cross-functional synergies..."
              </div>
              <div style={{ marginTop: '20px', color: '#FFD700', fontSize: '0.72rem' }}>
                &gt; Analyzing character n-grams... [DONE 18ms]
                <br />
                &gt; Computing burstiness variance... [DONE 24ms]
                <br />
                &gt; Evaluating LightGBM decision trees... [DONE 38ms]
              </div>
            </div>

            {/* Terminal Output Metrics */}
            <div
              style={{
                background: '#FFFBEA',
                border: '3px solid var(--color-black)',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <span style={{ fontWeight: 800, fontSize: '0.85rem', textTransform: 'uppercase' }}>
                    Forensic Verdict:
                  </span>
                  <span
                    style={{
                      background: 'var(--color-red)',
                      color: '#FFF',
                      fontWeight: 900,
                      fontSize: '0.74rem',
                      padding: '4px 10px',
                      border: '2px solid var(--color-black)',
                    }}
                  >
                    HIGHLY LIKELY AI (98.4%)
                  </span>
                </div>

                <div style={{ marginBottom: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', fontWeight: 700, marginBottom: '4px' }}>
                    <span>AI-Typical Phrasing</span>
                    <span>100%</span>
                  </div>
                  <div style={{ height: '12px', background: '#FFFFFF', border: '2px solid var(--color-black)' }}>
                    <div style={{ width: '100%', height: '100%', background: 'var(--color-pink)' }} />
                  </div>
                </div>

                <div style={{ marginBottom: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', fontWeight: 700, marginBottom: '4px' }}>
                    <span>Structural Uniformity</span>
                    <span>94.8%</span>
                  </div>
                  <div style={{ height: '12px', background: '#FFFFFF', border: '2px solid var(--color-black)' }}>
                    <div style={{ width: '94.8%', height: '100%', background: 'var(--color-yellow)' }} />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', fontWeight: 700, marginBottom: '4px' }}>
                    <span>Burstiness Deviation</span>
                    <span>Low (0.12)</span>
                  </div>
                  <div style={{ height: '12px', background: '#FFFFFF', border: '2px solid var(--color-black)' }}>
                    <div style={{ width: '85%', height: '100%', background: 'var(--color-blue)' }} />
                  </div>
                </div>
              </div>

              <div
                style={{
                  background: 'var(--color-white)',
                  border: '2px solid var(--color-black)',
                  padding: '8px 12px',
                  marginTop: '16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>
                  SHA-256 HASH: <code>8f4a...91ce</code>
                </span>
                <span className="memphis-tag" style={{ background: 'var(--color-green)', fontSize: '0.62rem' }}>
                  IMMUTABLE
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── USE CASES SECTION (3 CARDS) ── */}
      <section
        id="use-cases"
        style={{
          background: 'var(--color-yellow)',
          padding: '80px 24px',
          borderTop: 'var(--border-thick)',
          borderBottom: 'var(--border-thick)',
        }}
      >
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          {/* Section Header */}
          <div style={{ textAlign: 'center', marginBottom: '50px' }}>
            <span
              className="memphis-tag"
              style={{
                background: 'var(--color-pink)',
                color: '#FFFFFF',
                marginBottom: '14px',
                fontSize: '0.8rem',
                transform: 'rotate(2deg)',
              }}
            >
              ★ REAL-WORLD APPLICATIONS
            </span>
            <h2
              style={{
                fontFamily: 'var(--font-primary)',
                fontWeight: 900,
                fontSize: 'clamp(2rem, 4vw, 3.2rem)',
                textTransform: 'uppercase',
                letterSpacing: '-0.02em',
                margin: '10px 0',
                color: 'var(--color-black)',
              }}
            >
              PROVEN ENTERPRISE USE CASES
            </h2>
            <p style={{ maxWidth: '600px', margin: '0 auto', fontSize: '1rem', color: '#222', fontWeight: 500 }}>
              Discover how universities, recruitment platforms, and media intelligence desks deploy AuthentiQ daily.
            </p>
          </div>

          {/* 3 Use Cases Grid */}
          <div
            className="memphis-grid-3"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '28px',
            }}
          >
            {/* Use Case 1: Academic & Research Integrity */}
            <div
              className="memphis-card"
              style={{
                padding: '30px 24px',
                background: '#FFFFFF',
                transform: 'rotate(-1.5deg)',
              }}
            >
              <div style={{ fontSize: '1.2rem', fontWeight: 900, color: 'var(--color-pink)', textTransform: 'uppercase', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.6rem' }}>🎓</span> Higher Education
              </div>
              <p style={{ fontSize: '0.94rem', lineHeight: 1.6, color: '#333', fontWeight: 500, marginBottom: '24px' }}>
                Universities and academic publishers deploy AuthentiQ to safeguard essay competitions and scholarly submissions. Calibrated burstiness curves prevent false accusations against classical literature while highlighting uncredited LLM generation.
              </p>
              <div style={{ borderTop: '2px solid var(--color-black)', paddingTop: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '50%',
                    background: 'var(--color-pink)',
                    border: '2px solid var(--color-black)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 900,
                    color: '#FFF',
                  }}
                >
                  ED
                </div>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '0.88rem' }}>Academic &amp; Research Integrity</div>
                  <div style={{ fontSize: '0.72rem', color: '#666', fontWeight: 600 }}>Universities &amp; Scientific Journals</div>
                </div>
              </div>
            </div>

            {/* Use Case 2: Talent Acquisition & Hackathons */}
            <div
              className="memphis-card"
              style={{
                padding: '30px 24px',
                background: '#FFFFFF',
                transform: 'rotate(1.2deg)',
              }}
            >
              <div style={{ fontSize: '1.2rem', fontWeight: 900, color: 'var(--color-blue)', textTransform: 'uppercase', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.6rem' }}>💼</span> Tech Recruitment
              </div>
              <p style={{ fontSize: '0.94rem', lineHeight: 1.6, color: '#333', fontWeight: 500, marginBottom: '24px' }}>
                Recruitment teams and hackathon organizers ingest hundreds of candidate submissions via CSV in seconds. Submissions are ranked on empirical reasoning and originality, strictly decoupling assistive AI flags from automatic disqualification.
              </p>
              <div style={{ borderTop: '2px solid var(--color-black)', paddingTop: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '50%',
                    background: 'var(--color-green)',
                    border: '2px solid var(--color-black)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 900,
                    color: '#121316',
                  }}
                >
                  TA
                </div>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '0.88rem' }}>Talent Acquisition &amp; Hackathons</div>
                  <div style={{ fontSize: '0.72rem', color: '#666', fontWeight: 600 }}>Technical Hiring &amp; Innovation Sprints</div>
                </div>
              </div>
            </div>

            {/* Use Case 3: Newsroom Deepfake Verification */}
            <div
              className="memphis-card"
              style={{
                padding: '30px 24px',
                background: '#FFFFFF',
                transform: 'rotate(-0.8deg)',
              }}
            >
              <div style={{ fontSize: '1.2rem', fontWeight: 900, color: 'var(--color-green)', textTransform: 'uppercase', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.6rem' }}>📹</span> Media Intelligence
              </div>
              <p style={{ fontSize: '0.94rem', lineHeight: 1.6, color: '#333', fontWeight: 500, marginBottom: '24px' }}>
                Broadcast newsrooms and fact-checking desks ingest eyewitness video clips to dissect facial blend boundaries and audio-video temporal sync in real time, backed by cryptographic SHA-256 audit ledgers for courtroom-ready proof.
              </p>
              <div style={{ borderTop: '2px solid var(--color-black)', paddingTop: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '50%',
                    background: 'var(--color-yellow)',
                    border: '2px solid var(--color-black)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 900,
                    color: '#121316',
                  }}
                >
                  MF
                </div>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '0.88rem' }}>Eyewitness Video &amp; Deepfake Defense</div>
                  <div style={{ fontSize: '0.72rem', color: '#666', fontWeight: 600 }}>Broadcast Desks &amp; Trust/Safety Officers</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── PRICING SECTION (3 TIERS, HIGHLIGHT MIDDLE) ── */}
      <section
        id="pricing"
        style={{
          padding: '80px 24px',
          maxWidth: '1280px',
          margin: '0 auto',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <span
            className="memphis-tag"
            style={{
              background: 'var(--color-green)',
              color: 'var(--color-black)',
              marginBottom: '14px',
              fontSize: '0.8rem',
              transform: 'rotate(-2deg)',
            }}
          >
            💰 TRANSPARENT TIERS
          </span>
          <h2
            style={{
              fontFamily: 'var(--font-primary)',
              fontWeight: 900,
              fontSize: 'clamp(2rem, 4vw, 3.2rem)',
              textTransform: 'uppercase',
              letterSpacing: '-0.02em',
              margin: '10px 0',
              color: 'var(--color-black)',
            }}
          >
            HONEST TIERS. NO SURPRISES.
          </h2>
          <p style={{ maxWidth: '580px', margin: '0 auto 24px', fontSize: '1rem', color: '#555', fontWeight: 500 }}>
            Start with our full-powered free tier or scale to enterprise high-throughput verification clusters.
          </p>

          {/* Monthly / Annual Toggle */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              border: 'var(--border)',
              background: '#FFFFFF',
              boxShadow: '4px 4px 0px var(--color-black)',
              padding: '4px',
            }}
          >
            <button
              type="button"
              onClick={() => setPricingCycle('monthly')}
              style={{
                fontFamily: 'var(--font-primary)',
                fontWeight: 800,
                fontSize: '0.82rem',
                padding: '6px 16px',
                border: 'none',
                background: pricingCycle === 'monthly' ? 'var(--color-pink)' : 'transparent',
                color: pricingCycle === 'monthly' ? '#FFF' : 'var(--color-black)',
                cursor: 'pointer',
              }}
            >
              Monthly Billing
            </button>
            <button
              type="button"
              onClick={() => setPricingCycle('annual')}
              style={{
                fontFamily: 'var(--font-primary)',
                fontWeight: 800,
                fontSize: '0.82rem',
                padding: '6px 16px',
                border: 'none',
                background: pricingCycle === 'annual' ? 'var(--color-pink)' : 'transparent',
                color: pricingCycle === 'annual' ? '#FFF' : 'var(--color-black)',
                cursor: 'pointer',
              }}
            >
              Annual Billing (Save 20%)
            </button>
          </div>
        </div>

        {/* 3 Pricing Cards */}
        <div
          className="memphis-grid-3"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '30px',
            alignItems: 'stretch',
          }}
        >
          {/* Tier 1: Starter Scout */}
          <div
            className="memphis-card"
            style={{
              padding: '36px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <span className="memphis-tag" style={{ background: '#E2E8F0', marginBottom: '14px' }}>
                COMMUNITY TIER
              </span>
              <h3 style={{ fontSize: '1.4rem', fontWeight: 900, textTransform: 'uppercase', margin: '8px 0 6px' }}>
                Starter Scout
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#666', lineHeight: 1.5, marginBottom: '20px' }}>
                Ideal for individual researchers, educators, and independent content reviewers.
              </p>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '24px' }}>
                <span style={{ fontSize: '2.8rem', fontWeight: 900, lineHeight: 1 }}>₹0</span>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#666' }}>/ forever</span>
              </div>

              <div style={{ borderTop: '2px solid var(--color-black)', paddingTop: '20px', marginBottom: '24px' }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.85rem', fontWeight: 600 }}>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> 2,500 words text analysis / day
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> Sentence heat attribution maps
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> 5 video frame scans / day
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> OpenRouter Free tier access
                  </li>
                </ul>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onEnter?.('dashboard')}
              className="memphis-btn btn-outline"
              style={{ width: '100%' }}
            >
              Get Started Free
            </button>
          </div>

          {/* Tier 2: Pro Investigator (HIGHLIGHTED) */}
          <div
            className="memphis-card"
            style={{
              padding: '36px 28px',
              background: '#FFFFFF',
              border: '4px solid var(--color-pink)',
              boxShadow: '12px 12px 0px var(--color-pink)',
              transform: 'scale(1.04)',
              position: 'relative',
              zIndex: 10,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            {/* Top Ribbon */}
            <div
              style={{
                position: 'absolute',
                top: '-16px',
                right: '24px',
                background: 'var(--color-yellow)',
                border: '2px solid var(--color-black)',
                boxShadow: '3px 3px 0px var(--color-black)',
                fontWeight: 900,
                fontSize: '0.72rem',
                padding: '4px 12px',
                textTransform: 'uppercase',
                transform: 'rotate(2deg)',
              }}
            >
              ★ MOST POPULAR
            </div>

            <div>
              <span className="memphis-tag" style={{ background: 'var(--color-pink)', color: '#FFF', marginBottom: '14px' }}>
                PROFESSIONAL
              </span>
              <h3 style={{ fontSize: '1.4rem', fontWeight: 900, textTransform: 'uppercase', margin: '8px 0 6px' }}>
                Pro Investigator
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#666', lineHeight: 1.5, marginBottom: '20px' }}>
                For universities, hiring managers, and media organizations requiring full forensic power.
              </p>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '24px' }}>
                <span style={{ fontSize: '2.8rem', fontWeight: 900, lineHeight: 1, color: 'var(--color-pink)' }}>
                  {pricingCycle === 'monthly' ? '₹49' : '₹39'}
                </span>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#666' }}>/ month</span>
              </div>

              <div style={{ borderTop: '2px solid var(--color-black)', paddingTop: '20px', marginBottom: '24px' }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.85rem', fontWeight: 600 }}>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> Unlimited text forensic scans
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> CSV bulk candidate shortlisting
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> 1080p full video deepfake dissection
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> Gemma-4 31B OpenRouter priority
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> SHA-256 cryptographic audit logs
                  </li>
                </ul>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onEnter?.('dashboard')}
              className="memphis-btn btn-pink"
              style={{ width: '100%', fontSize: '0.95rem', padding: '14px' }}
            >
              Start 14-Day Free Pro
            </button>
          </div>

          {/* Tier 3: Enterprise Fleet */}
          <div
            className="memphis-card"
            style={{
              padding: '36px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <span className="memphis-tag" style={{ background: 'var(--color-blue)', color: '#FFF', marginBottom: '14px' }}>
                SCALE &amp; SECURITY
              </span>
              <h3 style={{ fontSize: '1.4rem', fontWeight: 900, textTransform: 'uppercase', margin: '8px 0 6px' }}>
                Enterprise Fleet
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#666', lineHeight: 1.5, marginBottom: '20px' }}>
                Custom compliance, dedicated GPU inference clusters, and bespoke rubric training.
              </p>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '24px' }}>
                <span style={{ fontSize: '2.8rem', fontWeight: 900, lineHeight: 1 }}>
                  {pricingCycle === 'monthly' ? '₹199' : '₹159'}
                </span>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#666' }}>/ month</span>
              </div>

              <div style={{ borderTop: '2px solid var(--color-black)', paddingTop: '20px', marginBottom: '24px' }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.85rem', fontWeight: 600 }}>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> Air-gapped on-premise deployment
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> Custom fine-tuned rubric models
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> Dedicated 99.99% uptime SLA
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: 'var(--color-green)', fontWeight: 900 }}>✓</span> SOC2 Type II compliance audit
                  </li>
                </ul>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onEnter?.('dashboard')}
              className="memphis-btn btn-blue"
              style={{ width: '100%' }}
            >
              Contact Sales
            </button>
          </div>
        </div>
      </section>

      {/* ── FINAL HIGH-ENERGY MEMPHIS CTA BANNER ── */}
      <section
        style={{
          background: 'var(--color-pink)',
          borderTop: 'var(--border-thick)',
          borderBottom: 'var(--border-thick)',
          padding: '80px 24px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Background Retro Grid Stripe */}
        <div
          style={{
            maxWidth: '1000px',
            margin: '0 auto',
            textAlign: 'center',
            position: 'relative',
            zIndex: 10,
          }}
        >
          <span
            className="memphis-tag"
            style={{
              background: 'var(--color-yellow)',
              color: 'var(--color-black)',
              marginBottom: '16px',
              fontSize: '0.82rem',
              transform: 'rotate(-3deg)',
            }}
          >
            ⚡ INSTANT ONBOARDING ⚡
          </span>

          <h2
            style={{
              fontFamily: 'var(--font-primary)',
              fontWeight: 900,
              fontSize: 'clamp(2.2rem, 4.8vw, 3.8rem)',
              textTransform: 'uppercase',
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              lineHeight: 1.1,
              margin: '12px 0 20px',
              textShadow: '4px 4px 0px var(--color-black)',
            }}
          >
            READY TO EXPOSE THE BOTS AND HONOR TRUE ORIGINALS?
          </h2>

          <p
            style={{
              fontSize: '1.1rem',
              fontWeight: 600,
              color: '#FFE4E1',
              maxWidth: '620px',
              margin: '0 auto 34px',
              lineHeight: 1.6,
            }}
          >
            Join 4,500+ educators, recruitment teams, and trust-and-safety investigators safeguarding content integrity with AuthentiQ.
          </p>

          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => onEnter?.('dashboard')}
              className="memphis-btn btn-yellow"
              style={{
                fontSize: '1.05rem',
                padding: '16px 36px',
              }}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              <span>Get AuthentiQ Studio Free</span>
            </button>

            <button
              type="button"
              onClick={() => onEnter?.('shortlist')}
              className="memphis-btn btn-outline"
              style={{
                fontSize: '1.05rem',
                padding: '16px 32px',
              }}
            >
              <span>Explore Recruiter Mode</span>
            </button>
          </div>

          <div style={{ marginTop: '24px', fontSize: '0.78rem', fontWeight: 700, color: '#FFFFFF', letterSpacing: '0.04em' }}>
            NO CREDIT CARD REQUIRED • SUB-SECOND INFERENCE • 100% DECOUPLED ETHICS
          </div>
        </div>
      </section>

      {/* ── FULL FOOTER ── */}
      <footer
        style={{
          background: '#121316',
          color: '#FFFFFF',
          padding: '60px 24px 40px',
          borderTop: 'var(--border-thick)',
        }}
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            display: 'grid',
            gridTemplateColumns: '1.4fr 1fr 1fr 1fr 1fr',
            gap: '40px',
            marginBottom: '50px',
          }}
          className="memphis-hero-split"
        >
          {/* Brand Info */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <div
                style={{
                  width: '34px',
                  height: '34px',
                  background: 'var(--color-pink)',
                  border: '2px solid #FFFFFF',
                  color: '#FFFFFF',
                  fontWeight: 900,
                  fontSize: '1.2rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                Q
              </div>
              <span style={{ fontSize: '1.3rem', fontWeight: 900, letterSpacing: '-0.02em', textTransform: 'uppercase' }}>
                Authenti<span style={{ color: 'var(--color-blue)' }}>Q</span>
              </span>
            </div>

            <p style={{ fontSize: '0.82rem', color: '#A0AEC0', lineHeight: 1.6, marginBottom: '20px', maxWidth: '300px' }}>
              Next-generation multimodal content intelligence platform. Calibrated text forensics, facial video deepfake analysis, and verifiable candidate evaluations.
            </p>

            {/* Social Icons */}
            <div style={{ display: 'flex', gap: '10px' }}>
              {/* GitHub */}
              <a
                href="https://github.com/ojaswiniii07-ai/AI-Content-Intelligence-Platform"
                target="_blank"
                rel="noreferrer"
                style={{
                  width: '36px',
                  height: '36px',
                  background: '#2D3748',
                  border: '2px solid #FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  textDecoration: 'none',
                  transition: 'transform 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translate(-2px, -2px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'none')}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                </svg>
              </a>

              {/* Twitter / X */}
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noreferrer"
                style={{
                  width: '36px',
                  height: '36px',
                  background: 'var(--color-blue)',
                  border: '2px solid #FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  textDecoration: 'none',
                  transition: 'transform 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translate(-2px, -2px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'none')}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" />
                </svg>
              </a>

              {/* Discord */}
              <a
                href="https://discord.com"
                target="_blank"
                rel="noreferrer"
                style={{
                  width: '36px',
                  height: '36px',
                  background: 'var(--color-purple)',
                  border: '2px solid #FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  textDecoration: 'none',
                  transition: 'transform 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translate(-2px, -2px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'none')}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="9" cy="12" r="1" />
                  <circle cx="15" cy="12" r="1" />
                  <path d="M7.5 7.5c3.5-1 5.5-1 9 0" />
                  <path d="M7 16.5c3.5 1 6.5 1 10 0" />
                  <path d="M2 12c0 5.5 4.5 10 10 10s10-4.5 10-10S17.5 2 12 2 2 6.5 2 12z" />
                </svg>
              </a>

              {/* LinkedIn */}
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noreferrer"
                style={{
                  width: '36px',
                  height: '36px',
                  background: 'var(--color-green)',
                  border: '2px solid #FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#121316',
                  textDecoration: 'none',
                  transition: 'transform 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translate(-2px, -2px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'none')}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
                  <rect x="2" y="9" width="4" height="12" />
                  <circle cx="4" cy="4" r="2" />
                </svg>
              </a>
            </div>
          </div>

          {/* Column 2: Forensics */}
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.88rem', textTransform: 'uppercase', marginBottom: '16px', color: 'var(--color-yellow)' }}>
              Forensic Engines
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.8rem', color: '#CBD5E0' }}>
              <li>
                <span onClick={() => onEnter?.('text')} style={{ cursor: 'pointer', transition: 'color 0.15s' }}>
                  Text AI Attribution
                </span>
              </li>
              <li>
                <span onClick={() => onEnter?.('media')} style={{ cursor: 'pointer', transition: 'color 0.15s' }}>
                  Deepfake Video Scanner
                </span>
              </li>
              <li>
                <span onClick={() => onEnter?.('shortlist')} style={{ cursor: 'pointer', transition: 'color 0.15s' }}>
                  Candidate Shortlisting
                </span>
              </li>
              <li>
                <span onClick={() => onEnter?.('simulator')} style={{ cursor: 'pointer', transition: 'color 0.15s' }}>
                  FP/FN Risk Simulator
                </span>
              </li>
            </ul>
          </div>

          {/* Column 3: Platform */}
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.88rem', textTransform: 'uppercase', marginBottom: '16px', color: 'var(--color-pink)' }}>
              Platform
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.8rem', color: '#CBD5E0' }}>
              <li>
                <span onClick={() => onEnter?.('audit')} style={{ cursor: 'pointer', transition: 'color 0.15s' }}>
                  SHA-256 Audit Ledger
                </span>
              </li>
              <li>
                <span onClick={() => onEnter?.('batch')} style={{ cursor: 'pointer', transition: 'color 0.15s' }}>
                  Batch File Ingestion
                </span>
              </li>
              <li>
                <a href="#inspector" style={{ color: '#CBD5E0', textDecoration: 'none' }}>
                  OpenRouter Gemma 4
                </a>
              </li>
              <li>
                <a href="/mock_data/hackathon_submissions.csv" download style={{ color: 'var(--color-green)', textDecoration: 'none' }}>
                  ↓ Mock Hackathon CSV
                </a>
              </li>
              <li>
                <a href="/mock_data/resume_candidates.csv" download style={{ color: 'var(--color-yellow)', textDecoration: 'none' }}>
                  ↓ Mock Resume CSV
                </a>
              </li>
            </ul>
          </div>

          {/* Column 4: Resources */}
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.88rem', textTransform: 'uppercase', marginBottom: '16px', color: 'var(--color-green)' }}>
              Documentation
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.8rem', color: '#CBD5E0' }}>
              <li>
                <a href="/MODEL_PERFORMANCE_METRICS.md" style={{ color: '#CBD5E0', textDecoration: 'none' }}>
                  Model Metrics Report
                </a>
              </li>
              <li>
                <a href="/AUTHENTIQ_PITCH_DECK_PRD.md" style={{ color: '#CBD5E0', textDecoration: 'none' }}>
                  PRD &amp; Architecture
                </a>
              </li>
              <li>
                <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer" style={{ color: '#CBD5E0', textDecoration: 'none' }}>
                  FastAPI Swagger Docs
                </a>
              </li>
              <li>
                <span style={{ color: '#718096' }}>Stitch Canvas Skills</span>
              </li>
            </ul>
          </div>

          {/* Column 5: Legal & Policy */}
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.88rem', textTransform: 'uppercase', marginBottom: '16px', color: 'var(--color-blue)' }}>
              Governance
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.8rem', color: '#CBD5E0' }}>
              <li>
                <span style={{ color: '#CBD5E0', cursor: 'pointer' }}>Decoupling Charter</span>
              </li>
              <li>
                <span style={{ color: '#CBD5E0', cursor: 'pointer' }}>Privacy Policy</span>
              </li>
              <li>
                <span style={{ color: '#CBD5E0', cursor: 'pointer' }}>Terms of Service</span>
              </li>
              <li>
                <span style={{ color: '#CBD5E0', cursor: 'pointer' }}>Responsible AI Code</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Copyright Strip */}
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            borderTop: '1px solid #2D3748',
            paddingTop: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
            fontSize: '0.76rem',
            color: '#718096',
          }}
        >
          <div>
            © 2026 AuthentiQ Technologies Inc. Built with Memphis 1980s Postmodern Aesthetics. All rights reserved.
          </div>
          <div style={{ display: 'flex', gap: '16px', fontWeight: 600 }}>
            <span style={{ color: 'var(--color-pink)' }}>Vibrant</span>
            <span>•</span>
            <span style={{ color: 'var(--color-yellow)' }}>Geometric</span>
            <span>•</span>
            <span style={{ color: 'var(--color-blue)' }}>Postmodern</span>
            <span>•</span>
            <span style={{ color: 'var(--color-green)' }}>Calibrated</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
