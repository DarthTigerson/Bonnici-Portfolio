import { useState, useEffect } from 'react'

const NAV = [
  { id: 'about',    label: 'About' },
  { id: 'doing',    label: 'Work' },
  { id: 'projects', label: 'Projects' },
  { id: 'contact',  label: 'Contact' },
]

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

interface Props {
  name: string
}

export function Navbar({ name: _name }: Props) {
  const [active, setActive] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const page = document.getElementById('page')
    if (!page) return
    function onScroll() {
      setScrolled(page!.scrollTop > 40)
    }
    page.addEventListener('scroll', onScroll, { passive: true })
    return () => page.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    const observers: IntersectionObserver[] = []
    NAV.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (!el) return
      const obs = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) setActive(id) },
        { rootMargin: '-40% 0px -55% 0px' }
      )
      obs.observe(el)
      observers.push(obs)
    })
    return () => observers.forEach(o => o.disconnect())
  }, [])

  return (
    <>
      <header
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 100,
          height: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          padding: '0 24px',
          background: scrolled ? 'rgba(9,9,11,0.85)' : 'transparent',
          backdropFilter: scrolled ? 'blur(16px)' : 'none',
          borderBottom: scrolled ? '1px solid rgba(255,255,255,0.06)' : '1px solid transparent',
          transition: 'background 0.3s, backdrop-filter 0.3s, border-color 0.3s',
        }}
      >
        {/* Desktop nav */}
        <nav
          style={{ display: 'flex', gap: 4 }}
          className="desktop-nav"
        >
          {NAV.map(item => (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              style={{
                background: active === item.id ? 'rgba(255,255,255,0.07)' : 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '6px 14px',
                borderRadius: 6,
                fontSize: 13,
                fontWeight: 500,
                color: active === item.id ? '#f4f4f5' : '#71717a',
                transition: 'color 0.15s, background 0.15s',
                fontFamily: 'inherit',
              }}
              onMouseEnter={e => {
                if (active !== item.id) (e.currentTarget as HTMLElement).style.color = '#d4d4d8'
              }}
              onMouseLeave={e => {
                if (active !== item.id) (e.currentTarget as HTMLElement).style.color = '#71717a'
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {/* Mobile hamburger */}
        <button
          className="hamburger"
          onClick={() => setMenuOpen(!menuOpen)}
          style={{
            display: 'none',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 8,
            color: '#a1a1aa',
          }}
          aria-label="Menu"
        >
          {menuOpen ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          )}
        </button>
      </header>

      {/* Mobile menu */}
      {menuOpen && (
        <div
          style={{
            position: 'fixed',
            top: 60,
            left: 0,
            right: 0,
            zIndex: 99,
            background: 'rgba(9,9,11,0.97)',
            backdropFilter: 'blur(16px)',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            padding: '16px 24px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
          }}
        >
          {NAV.map(item => (
            <button
              key={item.id}
              onClick={() => { scrollTo(item.id); setMenuOpen(false) }}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '10px 12px',
                borderRadius: 8,
                fontSize: 15,
                fontWeight: 500,
                color: active === item.id ? '#6366f1' : '#a1a1aa',
                textAlign: 'left',
                fontFamily: 'inherit',
                transition: 'color 0.15s',
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}

      <style>{`
        @media (max-width: 640px) {
          .desktop-nav { display: none !important; }
          .hamburger { display: flex !important; }
        }
      `}</style>
    </>
  )
}
