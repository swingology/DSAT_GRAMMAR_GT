import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Question } from '../components/QuestionCard'

const BUCKETS: Array<{ difficulty: 'low' | 'medium' | 'high'; limit: number }> = [
  { difficulty: 'low', limit: 3 },
  { difficulty: 'medium', limit: 4 },
  { difficulty: 'high', limit: 3 },
]
const TARGET_TOTAL = 10

function focusKeyParam(domain: string, focusKey: string): Record<string, string> {
  return domain === 'reading' ? { reading_focus_key: focusKey } : { grammar_focus_key: focusKey }
}

export function useQuickPickQuestions(domain: string, focusKey: string) {
  const [questions, setQuestions] = useState<Question[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [shortfallNote, setShortfallNote] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function run() {
      setIsLoading(true)
      setIsError(false)
      setShortfallNote(null)

      try {
        const focusParam = focusKeyParam(domain, focusKey)
        const results = await Promise.all(
          BUCKETS.map((bucket) =>
            api.getQuestions({ domain, ...focusParam, difficulty: bucket.difficulty, limit: bucket.limit })
          )
        )

        const seenIds = new Set<string>()
        // One slot array per bucket, in bucket order (low, medium, high). Backfill items
        // for a given bucket's shortfall are appended into that same slot, so the final
        // list stays grouped low -> medium -> high with backfill landing next to the
        // block it's compensating for, rather than all dumped at the very end.
        const slots: Question[][] = BUCKETS.map(() => [])
        const shortfallByBucket: number[] = []

        results.forEach((resp, i) => {
          const items: Question[] = resp?.items ?? []
          const taken = items.slice(0, BUCKETS[i].limit)
          taken.forEach((item) => {
            if (!seenIds.has(item.id)) {
              seenIds.add(item.id)
              slots[i].push(item)
            }
          })
          shortfallByBucket[i] = BUCKETS[i].limit - taken.length
        })

        const totalShortfall = shortfallByBucket.reduce((a, b) => a + b, 0)

        if (totalShortfall > 0 && !cancelled) {
          const alreadyHave = slots.reduce((n, slot) => n + slot.length, 0)
          const backfillResp = await api.getQuestions({ domain, ...focusParam, limit: totalShortfall + alreadyHave })
          const backfillItems: Question[] = backfillResp?.items ?? []
          let backfillIndex = 0

          for (let i = 0; i < BUCKETS.length; i++) {
            let need = shortfallByBucket[i]
            while (need > 0 && backfillIndex < backfillItems.length) {
              const candidate = backfillItems[backfillIndex]
              backfillIndex++
              if (seenIds.has(candidate.id)) continue
              seenIds.add(candidate.id)
              slots[i].push(candidate)
              need--
            }
          }
        }

        if (cancelled) return

        const merged = slots.flat()
        setQuestions(merged)
        setShortfallNote(
          merged.length < TARGET_TOTAL
            ? `Only ${merged.length} question${merged.length === 1 ? '' : 's'} available for this concept.`
            : null
        )
      } catch {
        if (!cancelled) setIsError(true)
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [domain, focusKey])

  return { questions, isLoading, isError, shortfallNote }
}
