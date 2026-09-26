import type { Question } from '../types'

const pad2 = (v: string | number) => String(v).padStart(2, '0')

/** Canonical provenance label: `2025 · PT04 · Sec01 · Mod01 · Q14`. Parts that are unknown are left out. */
export function questionSourceLabel(q: Pick<Question,
  'source_release_year' | 'source_pt_number' | 'source_section_code' | 'source_module_code' | 'source_question_number'
>): string {
  return [
    q.source_release_year,
    q.source_pt_number != null && `PT${pad2(q.source_pt_number)}`,
    q.source_section_code && `Sec${q.source_section_code}`,
    q.source_module_code && `Mod${q.source_module_code}`,
    q.source_question_number != null && `Q${q.source_question_number}`,
  ].filter(Boolean).join(' · ')
}

export const ptLabel = (pt: number) => `PT${pad2(pt)}`
