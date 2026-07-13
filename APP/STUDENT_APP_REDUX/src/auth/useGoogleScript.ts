import { useEffect, useState } from 'react'

const GIS_SRC = 'https://accounts.google.com/gsi/client'

export const GOOGLE_CLIENT_ID: string =
  (import.meta as any).env.VITE_GOOGLE_CLIENT_ID || ''

type ScriptStatus = 'loading' | 'ready' | 'error'

let loader: Promise<void> | null = null

/** Load the Google Identity Services script once, shared across callers. */
function loadGoogleScript(): Promise<void> {
  if (loader) return loader

  loader = new Promise<void>((resolve, reject) => {
    if ((window as any).google?.accounts?.id) {
      resolve()
      return
    }

    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GIS_SRC}"]`)
    const script = existing ?? document.createElement('script')

    script.addEventListener('load', () => resolve())
    script.addEventListener('error', () => {
      loader = null
      reject(new Error('Failed to load Google Identity Services'))
    })

    if (!existing) {
      script.src = GIS_SRC
      script.async = true
      script.defer = true
      document.head.appendChild(script)
    }
  })

  return loader
}

export function useGoogleScript(): ScriptStatus {
  const [status, setStatus] = useState<ScriptStatus>('loading')

  useEffect(() => {
    let cancelled = false
    loadGoogleScript().then(
      () => !cancelled && setStatus('ready'),
      () => !cancelled && setStatus('error'),
    )
    return () => {
      cancelled = true
    }
  }, [])

  return status
}
