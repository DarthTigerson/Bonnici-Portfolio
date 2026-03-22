import { useState, useEffect } from 'react'

const ALL_SECTIONS = [
  { id: 'hero',     label: 'Home' },
  { id: 'about',    label: 'About' },
  { id: 'doing',    label: 'Work' },
  { id: 'projects', label: 'Portfolio' },
  { id: 'contact',  label: 'Contact' },
]

interface Props {
  portfolioEnabled?: boolean
}

export function SectionDots({ portfolioEnabled = true }: Props) {
  const [active, setActive] = useState('hero')
  const SECTIONS = portfolioEnabled ? ALL_SECTIONS : ALL_SECTIONS.filter(s => s.id !== 'projects')

  useEffect(() => {
    const page = document.getElementById('page')
    if (!page) return

    function onScroll() {
      const scrollTop = page!.scrollTop
      let current = SECTIONS[0].id
      for (const { id } of SECTIONS) {
        const el = document.getElementById(id)
        if (el && el.offsetTop <= scrollTop + page!.clientHeight * 0.5) current = id
      }
      setActive(current)
    }

    page.addEventListener('scroll', onScroll, { passive: true })
    return () => page.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <>
      <div
        className="section-dots"
        style={{
          position: 'fixed',
          right: 20,
          top: '50%',
          transform: 'translateY(-50%)',
          zIndex: 90,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          gap: 10,
        }}
      >
        {SECTIONS.map(({ id, label }) => {
          const isActive = active === id
          return (
            <div
              key={id}
              onClick={() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                cursor: 'pointer',
              }}
            >
              {/* Label */}
              <span style={{
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: '0.5px',
                color: isActive ? '#f4f4f5' : '#3f3f46',
                transition: 'color 0.2s ease',
                whiteSpace: 'nowrap',
                userSelect: 'none',
              }}>
                {label}
              </span>

              {/* Dot container */}
              <div style={{ width: 16, height: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {isActive && (
                    <>
                      <div style={{ position: 'absolute', width: 10, height: 10, borderRadius: '50%', border: '1.5px solid #6366f1', animation: 'ripple 1.6s ease-out infinite' }} />
                      <div style={{ position: 'absolute', width: 10, height: 10, borderRadius: '50%', border: '1.5px solid #6366f1', animation: 'ripple 1.6s ease-out infinite 0.5s' }} />
                    </>
                  )}
                  <div
                    style={{
                      width: isActive ? 10 : 6,
                      height: isActive ? 10 : 6,
                      borderRadius: '50%',
                      background: isActive ? '#6366f1' : 'rgba(255,255,255,0.2)',
                      transition: 'all 0.3s cubic-bezier(0.34,1.56,0.64,1)',
                      boxShadow: isActive ? '0 0 6px rgba(99,102,241,0.8)' : 'none',
                    }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <style>{`
        @keyframes ripple {
          0%   { transform: scale(1);   opacity: 0.8; }
          100% { transform: scale(2.8); opacity: 0; }
        }
        @media (max-width: 768px) {
          .section-dots { display: none !important; }
        }
      `}</style>
    </>
  )
}
