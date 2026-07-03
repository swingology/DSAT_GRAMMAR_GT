export function Skeleton({ className = 'h-4' }: { className?: string }) {
  return <div className={`rounded bg-gray-100 animate-pulse ${className}`} />
}
