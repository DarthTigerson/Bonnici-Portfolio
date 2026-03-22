import { useState } from 'react'
import type { Config } from '@/types/config'
import { usePortfolioFilter } from '@/hooks/usePortfolioFilter'

interface Props {
  config: Config
}

function ExternalIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
      <polyline points="15 3 21 3 21 9"/>
      <line x1="10" y1="14" x2="21" y2="3"/>
    </svg>
  )
}

export function Projects({ config }: Props) {
  const { portfolio } = config
  const { allTags, filtered, activeTag, setActiveTag } = usePortfolioFilter(portfolio.projects ?? [])
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null)

  if (!portfolio.enabled) return null

  return (
    <section id="projects" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
      <div className="section">
        <div data-reveal className="section-label">Work</div>
        <h2 data-reveal data-delay="1" className="section-heading">Portfolio</h2>

        {/* Tag filters */}
        {allTags.length > 1 && (
          <div data-reveal data-delay="2" style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 40 }}>
            {allTags.map(tag => (
              <button
                key={tag}
                onClick={() => setActiveTag(tag)}
                style={{
                  padding: '6px 16px',
                  borderRadius: 20,
                  border: '1px solid',
                  borderColor: activeTag === tag ? '#6366f1' : 'rgba(255,255,255,0.08)',
                  background: activeTag === tag ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: activeTag === tag ? '#818cf8' : '#71717a',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  fontFamily: 'inherit',
                }}
                onMouseEnter={e => {
                  if (activeTag !== tag) {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(99,102,241,0.3)'
                    ;(e.currentTarget as HTMLElement).style.color = '#a1a1aa'
                  }
                }}
                onMouseLeave={e => {
                  if (activeTag !== tag) {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.08)'
                    ;(e.currentTarget as HTMLElement).style.color = '#71717a'
                  }
                }}
              >
                {tag}
              </button>
            ))}
          </div>
        )}

        {/* Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: 20,
          }}
        >
          {filtered.map((project, i) => {
            const imgSrc = project.image_url || (project.image ? `/data/images/portfolio/${project.image}` : '')
            const isHovered = hoveredIdx === i

            return (
              <a
                key={i}
                data-reveal
                href={project.git_url || undefined}
                target={project.git_url ? '_blank' : undefined}
                rel="noopener noreferrer"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  background: '#111115',
                  border: '1px solid rgba(255,255,255,0.07)',
                  borderRadius: 16,
                  overflow: 'hidden',
                  textDecoration: 'none',
                  cursor: project.git_url ? 'pointer' : 'default',
                  transition: 'border-color 0.2s, box-shadow 0.2s, transform 0.2s',
                  transform: isHovered ? 'translateY(-4px)' : 'none',
                  boxShadow: isHovered ? '0 16px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(99,102,241,0.2)' : 'none',
                  borderColor: isHovered ? 'rgba(99,102,241,0.35)' : 'rgba(255,255,255,0.07)',
                }}
                onMouseEnter={() => setHoveredIdx(i)}
                onMouseLeave={() => setHoveredIdx(null)}
              >
                {/* Image */}
                {imgSrc && (
                  <div style={{ aspectRatio: '16/9', overflow: 'hidden', background: '#0d0d10', flexShrink: 0 }}>
                    <img
                      src={imgSrc}
                      alt={project.title}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        display: 'block',
                        transition: 'transform 0.4s',
                        transform: isHovered ? 'scale(1.04)' : 'scale(1)',
                      }}
                      onError={e => { (e.target as HTMLImageElement).closest('div')!.remove() }}
                    />
                  </div>
                )}

                {/* Content */}
                <div style={{ padding: '18px 20px 20px', flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                    <h3 style={{ fontSize: 16, fontWeight: 700, color: '#f4f4f5', lineHeight: 1.3, flex: 1 }}>
                      {project.title}
                    </h3>
                    {project.git_url && (
                      <span style={{ color: isHovered ? '#818cf8' : '#3f3f46', transition: 'color 0.2s', marginTop: 2, flexShrink: 0 }}>
                        <ExternalIcon />
                      </span>
                    )}
                  </div>

                  {portfolio.mode === 'description' && project.description && (
                    <p style={{
                      fontSize: 13,
                      color: '#71717a',
                      lineHeight: 1.6,
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}>
                      {project.description}
                    </p>
                  )}

                  {portfolio.mode === 'tags' && project.tags?.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 'auto' }}>
                      {project.tags.map((tag, ti) => (
                        <span key={ti} className="tag">{tag}</span>
                      ))}
                    </div>
                  )}

                  {portfolio.mode === 'description' && project.tags?.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 'auto' }}>
                      {project.tags.map((tag, ti) => (
                        <span key={ti} className="tag">{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              </a>
            )
          })}
        </div>

        {filtered.length === 0 && (
          <p style={{ textAlign: 'center', color: '#52525b', padding: '48px 0' }}>
            No projects match the selected filter.
          </p>
        )}
      </div>
    </section>
  )
}
