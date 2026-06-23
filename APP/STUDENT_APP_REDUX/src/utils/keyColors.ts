import React from 'react'

function djb2(str: string): number {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

// Primary color wheel stops — evenly spaced, maximally distinct
const PRIMARY_HUES = [0, 30, 60, 120, 180, 210, 270, 330]

export function assignKeyColor(
  id: string,
  category: 'anatomy' | 'concept'
): { color: string; lightBg: string } {
  const hash = djb2(id)
  if (category === 'concept') {
    const hue = PRIMARY_HUES[hash % PRIMARY_HUES.length]
    return {
      color:   `hsl(${hue}, 85%, 38%)`,
      lightBg: `hsl(${hue}, 60%, 92%)`,
    }
  }
  // Anatomy: full 360° wheel, high contrast
  const hue = hash % 360
  return {
    color:   `hsl(${hue}, 75%, 30%)`,
    lightBg: `hsl(${hue}, 60%, 92%)`,
  }
}

export function activeKeyStyle(color: string): React.CSSProperties {
  return { backgroundColor: color, color: '#ffffff', borderColor: color }
}

export function inactiveKeyStyle(color: string, lightBg: string): React.CSSProperties {
  return { backgroundColor: lightBg, color, borderColor: color }
}
