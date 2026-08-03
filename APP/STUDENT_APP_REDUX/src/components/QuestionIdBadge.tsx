interface QuestionIdBadgeProps {
  id: string
  className?: string
}

export function QuestionIdBadge({ id, className = '' }: QuestionIdBadgeProps) {
  return (
    <div
      className={`inline-flex max-w-full items-start gap-1 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800 ${className}`}
      title={`Question ID: ${id}`}
      aria-label={`Question ID: ${id}`}
    >
      <span className="shrink-0 text-amber-600">Question ID:</span>
      <span className="font-mono break-all">{id}</span>
    </div>
  )
}
