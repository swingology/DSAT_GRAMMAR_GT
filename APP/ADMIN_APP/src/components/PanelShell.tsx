import type { ReactNode } from 'react'

export function PanelShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl h-full flex flex-col overflow-hidden">
      <div className="panel-drag-handle cursor-move px-4 py-2.5 md:py-3.5 border-b border-gray-100 bg-gray-50 flex items-center justify-between flex-shrink-0 touch-none">
        <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">{title}</span>
        <span className="text-gray-300 text-xs select-none">::::</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4">{children}</div>
    </div>
  )
}
