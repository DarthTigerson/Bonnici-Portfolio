import type { Config } from '@/types/config'

interface Props {
  config: Config
}

export function About({ config }: Props) {
  const { about_me, skills } = config

  const paragraphs = about_me.long_description.split('\n\n').filter(Boolean)
  const skillSections = Object.values(skills.sections)

  return (
    <section id="about" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
      <div className="section">
        <div data-reveal className="section-label">About me</div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 60,
            alignItems: 'start',
          }}
          className="about-grid"
        >
          {/* Left: Bio */}
          <div data-reveal data-delay="1">
            <h2 className="section-heading" style={{ marginBottom: 20 }}>
              My Story
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {paragraphs.map((p, i) => (
                <p key={i} style={{ color: '#a1a1aa', fontSize: 15, lineHeight: 1.75 }}>{p}</p>
              ))}
            </div>
          </div>

          {/* Right: Skills */}
          <div data-reveal data-delay="2">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
              {skillSections.map((section, si) => (
                <div key={si}>
                  <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '1.5px', textTransform: 'uppercase', color: '#52525b', marginBottom: 12 }}>
                    {section.title}
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {section.skills.map((skill, ki) => (
                      <div
                        key={ki}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                          padding: '5px 10px',
                          borderRadius: 6,
                          background: 'rgba(255,255,255,0.03)',
                          border: '1px solid rgba(255,255,255,0.07)',
                          fontSize: 12,
                          fontWeight: 500,
                          color: '#a1a1aa',
                          position: 'relative',
                          transition: 'border-color 0.15s, color 0.15s',
                          cursor: 'default',
                        }}
                        onMouseEnter={e => {
                          const el = e.currentTarget as HTMLElement
                          el.style.borderColor = skill.border_color || 'rgba(99,102,241,0.4)'
                          el.style.color = '#f4f4f5'
                        }}
                        onMouseLeave={e => {
                          const el = e.currentTarget as HTMLElement
                          el.style.borderColor = 'rgba(255,255,255,0.07)'
                          el.style.color = '#a1a1aa'
                        }}
                      >
                        <img
                          src={`/data/images/skills/${skill.image}`}
                          alt=""
                          style={{ width: 14, height: 14, objectFit: 'contain', display: 'block' }}
                          onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                        />
                        {skill.title}
                        {skill.is_new && (
                          <span style={{ fontSize: 9, fontWeight: 700, padding: '1px 4px', borderRadius: 4, background: '#6366f1', color: '#fff', letterSpacing: '0.5px' }}>
                            NEW
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .about-grid { grid-template-columns: 1fr !important; gap: 40px !important; }
        }
      `}</style>
    </section>
  )
}
