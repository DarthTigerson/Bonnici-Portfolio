import { useEffect } from 'react'
import { useConfig } from '@/hooks/useConfig'
import { Hero } from '@/components/sections/Hero'
import { About } from '@/components/sections/About'
import { Doing } from '@/components/sections/Doing'
import { Projects } from '@/components/sections/Projects'
import { Contact } from '@/components/sections/Contact'
import { SectionDots } from '@/components/SectionDots'

function Loader() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{
        width: 28, height: 28,
        border: '2px solid rgba(99,102,241,0.2)',
        borderTopColor: '#6366f1',
        borderRadius: '50%',
        animation: 'spin 0.65s linear infinite',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

function Setup() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 24px' }}>
      <div style={{ textAlign: 'center', maxWidth: 420 }}>
        <div style={{ fontSize: 40, marginBottom: 16 }}>👋</div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#f4f4f5', marginBottom: 10, letterSpacing: '-0.03em' }}>
          Portfolio not configured
        </h1>
        <p style={{ color: '#71717a', fontSize: 14, lineHeight: 1.65, marginBottom: 28 }}>
          Head over to the admin panel to set up your profile, projects and skills.
        </p>
        <a
          href="http://localhost:85"
          className="btn btn-primary"
          style={{ display: 'inline-flex', justifyContent: 'center' }}
        >
          Open admin panel
        </a>
      </div>
    </div>
  )
}

export default function App() {
  const { data: config, isLoading, isError } = useConfig()

  // Post device info for visitor analytics
  useEffect(() => {
    fetch('/api/device-info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        screen_width: screen.width,
        screen_height: screen.height,
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight,
        pixel_ratio: window.devicePixelRatio,
        platform: navigator.platform,
        user_agent: navigator.userAgent,
        language: navigator.language,
      }),
    }).catch(() => {})
  }, [])

  // Scroll reveal via IntersectionObserver
  useEffect(() => {
    const els = document.querySelectorAll('[data-reveal]')
    if (!els.length) return
    const obs = new IntersectionObserver(
      entries => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            e.target.classList.add('revealed')
            obs.unobserve(e.target)
          }
        })
      },
      { rootMargin: '0px 0px -60px 0px', threshold: 0.1 }
    )
    els.forEach(el => obs.observe(el))
    return () => obs.disconnect()
  })

  if (isLoading) return <Loader />
  if (isError || !config) return <Setup />
  if (!config.main_info?.name || config.main_info.name === 'Your Name') return <Setup />

  document.title = `${config.main_info.name} | Portfolio`

  return (
    <>
      <SectionDots portfolioEnabled={config.portfolio?.enabled !== false} />
      <div id="page">
        <main>
          <Hero config={config} />
          <About config={config} />
          <Doing config={config} />
          <Projects config={config} />
          <Contact />
        </main>
        <footer style={{
          borderTop: '1px solid rgba(255,255,255,0.05)',
          padding: '24px',
          textAlign: 'center',
          color: '#3f3f46',
          fontSize: 12,
          letterSpacing: '0.3px',
        }}>
          Made by{' '}
          <a
            href="https://bonnici.xyz"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: '#6366f1', textDecoration: 'none', fontWeight: 600 }}
          >
            {config.main_info.name}
          </a>
        </footer>
      </div>
    </>
  )
}
