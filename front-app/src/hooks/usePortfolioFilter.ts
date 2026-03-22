import { useState, useMemo } from 'react'
import type { Project } from '@/types/config'

export function usePortfolioFilter(projects: Project[]) {
  const [activeTag, setActiveTag] = useState<string>('All')

  const allTags = useMemo(() => {
    const tags = new Set<string>()
    projects.forEach(p => p.tags?.forEach(t => tags.add(t)))
    return ['All', ...Array.from(tags)]
  }, [projects])

  const filtered = useMemo(() => {
    if (activeTag === 'All') return projects
    return projects.filter(p =>
      p.tags?.some(t => t.toLowerCase() === activeTag.toLowerCase())
    )
  }, [projects, activeTag])

  return { allTags, filtered, activeTag, setActiveTag }
}
