import { useState, type MouseEvent } from 'react'

/**
 * Full id in a monospace box. Click copies it; an optional "+" toggles it in a
 * caller-managed collection list (used to build an id list for Claude Code).
 */
export function IdChip({
  id,
  collected,
  onToggleCollect,
}: {
  id: string
  collected?: boolean
  onToggleCollect?: (id: string) => void
}) {
  const [copied, setCopied] = useState(false)

  const copy = async (e: MouseEvent) => {
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(id)
      setCopied(true)
      setTimeout(() => setCopied(false), 1200)
    } catch { /* clipboard blocked; the text is still selectable */ }
  }

  return (
    <span className="inline-flex items-stretch text-xs font-mono select-all" onClick={(e) => e.stopPropagation()}>
      <button
        type="button"
        onClick={copy}
        title="Click to copy"
        className={`px-1.5 py-0.5 rounded-l border border-gray-200 bg-gray-50 hover:bg-blue-50 text-gray-600 ${onToggleCollect ? '' : 'rounded-r'}`}
      >
        {copied ? 'copied ✓' : id}
      </button>
      {onToggleCollect && (
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onToggleCollect(id) }}
          title={collected ? 'Remove from id list' : 'Add to id list'}
          className={`px-1.5 rounded-r border border-l-0 border-gray-200 ${collected ? 'bg-blue-600 text-white' : 'bg-white text-gray-500 hover:bg-blue-50'}`}
        >
          {collected ? '✓' : '+'}
        </button>
      )}
    </span>
  )
}

/** Sticky footer listing collected ids with copy/clear controls. */
export function IdListPanel({ ids, onClear, onRemove }: { ids: string[]; onClear: () => void; onRemove: (id: string) => void }) {
  const [copied, setCopied] = useState('')
  if (ids.length === 0) return null
  const copyAs = async (label: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(label)
      setTimeout(() => setCopied(''), 1200)
    } catch { /* clipboard blocked */ }
  }
  return (
    <div className="sticky bottom-0 z-40 bg-white border border-gray-200 rounded-xl shadow-lg p-3 space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">ID list ({ids.length})</span>
        <div className="ml-auto flex gap-2">
          <button className="px-2.5 py-1 text-xs rounded-md border border-gray-200" onClick={() => copyAs('lines', ids.join('\n'))}>
            {copied === 'lines' ? 'Copied ✓' : 'Copy (one per line)'}
          </button>
          <button className="px-2.5 py-1 text-xs rounded-md border border-gray-200" onClick={() => copyAs('json', JSON.stringify(ids))}>
            {copied === 'json' ? 'Copied ✓' : 'Copy as JSON'}
          </button>
          <button className="px-2.5 py-1 text-xs rounded-md border border-gray-200 text-red-600" onClick={onClear}>Clear</button>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto">
        {ids.map((id) => (
          <span key={id} className="inline-flex items-center text-xs font-mono border border-gray-200 rounded px-1.5 py-0.5 bg-gray-50 text-gray-600">
            {id}
            <button className="ml-1.5 text-gray-400 hover:text-red-600" title="Remove" onClick={() => onRemove(id)}>×</button>
          </span>
        ))}
      </div>
    </div>
  )
}
