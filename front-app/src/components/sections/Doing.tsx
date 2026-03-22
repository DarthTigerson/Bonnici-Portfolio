import type { Config } from '@/types/config'
import { NeuralNetwork } from '@/components/NeuralNetwork'

interface Props {
  config: Config
}

export function Doing({ config }: Props) {
  const panels = Object.values(config.what_im_doing).filter(p => p.enabled)
  if (panels.length === 0) return null

  return (
    <section id="doing" style={{ borderTop: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.015)', position: 'relative', overflow: 'hidden' }}>
      <NeuralNetwork />
      <div className="section" style={{ position: 'relative', zIndex: 1 }}>
        <div data-reveal className="section-label">Currently</div>
        <h2 data-reveal data-delay="1" className="section-heading">What I'm working on</h2>

        <div className="doing-grid">
          {panels.map((panel, i) => (
            <div
              key={i}
              data-reveal
              data-delay={String(i + 1) as '1' | '2' | '3' | '4'}
              className="card doing-card"
            >
              {/* Icon */}
              {panel.image && (
                <div
                  style={{
                    width: 56,
                    height: 56,
                    flexShrink: 0,
                    borderRadius: 14,
                    background: 'rgba(99,102,241,0.1)',
                    border: '1px solid rgba(99,102,241,0.2)',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: 20,
                  }}
                >
                  <div
                    style={{ width: '100%', height: '100%', lineHeight: 0 }}
                    ref={el => {
                      if (!el) return
                      const svg = el.querySelector('svg')
                      if (svg) {
                        svg.setAttribute('width', '100%')
                        svg.setAttribute('height', '100%')
                        svg.style.width = '100%'
                        svg.style.height = '100%'
                        svg.style.display = 'block'
                      }
                    }}
                    dangerouslySetInnerHTML={{ __html: panel.image }}
                  />
                </div>
              )}

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 16, fontWeight: 700, color: '#f4f4f5' }}>{panel.title}</span>
                  {panel.flag?.enabled && panel.flag.text && (
                    <span
                      style={{
                        fontSize: 10,
                        fontWeight: 700,
                        letterSpacing: '0.6px',
                        textTransform: 'uppercase',
                        padding: '2px 8px',
                        borderRadius: 20,
                        background: 'rgba(99,102,241,0.15)',
                        color: '#818cf8',
                        border: '1px solid rgba(99,102,241,0.25)',
                      }}
                    >
                      {panel.flag.text}
                    </span>
                  )}
                </div>
                <p style={{ fontSize: 14, color: '#71717a', lineHeight: 1.7 }}>{panel.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        .doing-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 20px;
        }
        .doing-card {
          padding: 28px;
          display: flex;
          flex-direction: column;
        }
        @media (max-width: 640px) {
          .doing-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </section>
  )
}
