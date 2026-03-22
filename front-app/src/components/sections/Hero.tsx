import type { Config } from '@/types/config'

interface Props {
  config: Config
}

function ArrowDown() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>
    </svg>
  )
}

function GithubIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.37.6.1.82-.26.82-.58v-2.03c-3.34.72-4.04-1.61-4.04-1.61-.54-1.38-1.33-1.75-1.33-1.75-1.09-.74.08-.73.08-.73 1.2.09 1.84 1.24 1.84 1.24 1.07 1.83 2.8 1.3 3.49 1 .1-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.14-.3-.54-1.52.1-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 3-.4c1.02 0 2.04.13 3 .4 2.28-1.55 3.29-1.23 3.29-1.23.65 1.66.24 2.88.12 3.18.77.84 1.23 1.91 1.23 3.22 0 4.61-2.8 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.83.58C20.56 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/>
    </svg>
  )
}

function LinkedinIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
      <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.13 1.45-2.13 2.94v5.67H9.37V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.59 0 4.26 2.36 4.26 5.43v6.31zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zm1.78 13.02H3.56V9h3.56v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.46C23.2 24 24 23.23 24 22.28V1.72C24 .77 23.2 0 22.23 0z"/>
    </svg>
  )
}

export function Hero({ config }: Props) {
  const { main_info, contact_card, about_me } = config
  const { github, linkedin } = contact_card.social_links

  return (
    <section
      id="hero"
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: '80px 24px 48px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background glow */}
      <div
        aria-hidden
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse 120% 90% at 50% 0%, rgba(99,102,241,0.45) 0%, rgba(99,102,241,0.08) 55%, transparent 75%)',
          pointerEvents: 'none',
          animation: 'glowPulse 6s ease-in-out infinite',
        }}
      />

      {/* Profile image */}
      <div
        data-reveal
        style={{
          width: 140,
          height: 140,
          borderRadius: '50%',
          overflow: 'hidden',
          background: '#1c1c22',
          border: '3px solid rgba(99,102,241,0.35)',
          animation: 'heroFloat 6s ease-in-out infinite',
          marginBottom: 28,
          flexShrink: 0,
          position: 'relative',
          zIndex: 1,
        }}
      >
        <img
          src="/data/images/profile.webp"
          alt={main_info.name}
          style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
          onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
        />
      </div>

      {/* Name */}
      <h1
        data-reveal
        data-delay="1"
        style={{
          fontSize: 'clamp(2.8rem, 9vw, 6rem)',
          fontWeight: 900,
          letterSpacing: '-0.04em',
          lineHeight: 1.05,
          color: '#f4f4f5',
          marginBottom: 16,
          position: 'relative',
          zIndex: 1,
        }}
      >
        {main_info.name}
      </h1>

      {/* Badge */}
      <div
        data-reveal
        data-delay="2"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          padding: '5px 14px',
          borderRadius: 20,
          background: 'rgba(99,102,241,0.1)',
          border: '1px solid rgba(99,102,241,0.25)',
          fontSize: 12,
          fontWeight: 600,
          color: '#818cf8',
          letterSpacing: '0.3px',
          marginBottom: 20,
          position: 'relative',
          zIndex: 1,
        }}
      >
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#6366f1', display: 'block', boxShadow: '0 0 8px #6366f1' }} />
        {main_info.job_title}
      </div>

      {/* Short bio */}
      <p
        data-reveal
        data-delay="3"
        style={{
          fontSize: 'clamp(15px, 2vw, 17px)',

          color: '#71717a',
          lineHeight: 1.65,
          maxWidth: 520,
          marginBottom: 36,
          position: 'relative',
          zIndex: 1,
        }}
      >
        {about_me.short_description}
      </p>

      {/* CTAs */}
      <div
        data-reveal
        data-delay="4"
        style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center', position: 'relative', zIndex: 1 }}
      >
        {github.enabled && (
          <a href={github.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost">
            <GithubIcon /> GitHub
          </a>
        )}
        {linkedin.enabled && (
          <a href={linkedin.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost">
            <LinkedinIcon /> LinkedIn
          </a>
        )}
      </div>

      {/* Scroll cue */}
      <button
        onClick={() => document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' })}
        style={{
          position: 'absolute',
          bottom: 32,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: '#6366f1',
          padding: 8,
          transition: 'color 0.2s',
          animation: 'bounce 2s ease-in-out infinite',
        }}
        onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = '#818cf8' }}
        onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = '#6366f1' }}
        aria-label="Scroll down"
      >
        <ArrowDown />
      </button>

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateX(-50%) translateY(0); }
          50% { transform: translateX(-50%) translateY(6px); }
        }
        @keyframes heroFloat {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        @keyframes glowPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.55; transform: scale(1.2); }
        }
      `}</style>
    </section>
  )
}
