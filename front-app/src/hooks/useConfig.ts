import { useQuery } from '@tanstack/react-query'
import type { Config } from '@/types/config'

export function useConfig() {
  return useQuery<Config>({
    queryKey: ['config'],
    queryFn: async () => {
      const res = await fetch('/api/config')
      if (!res.ok) throw new Error('Failed to load config')
      return res.json()
    },
    staleTime: Infinity,
  })
}
