import React from 'react'

function djb2(str: string): number {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

export function assignKeyColor(
  id: string,
  category: 'anatomy' | 'concept'
): { color: string; lightBg: string } {
  const hash = djb2(id)
  const hue = category === 'anatomy'
    ? 10 + (hash % 20) * 8
    : 182 + (hash % 60) * 2.88
  const [sat, light, bgSat, bgLight] =
    category === 'anatomy'
      ? [50, 32, 40, 93]
      : [70, 26, 65, 89]
  return {
    color:   `hsl(${Math.round(hue)}, ${sat}%, ${light}%)`,
    lightBg: `hsl(${Math.round(hue)}, ${bgSat}%, ${bgLight}%)`,
  }
}

export function activeKeyStyle(color: string): React.CSSProperties {
  return { backgroundColor: color, color: '#ffffff', borderColor: color }
}

export function inactiveKeyStyle(color: string, lightBg: string): React.CSSProperties {
  return { backgroundColor: lightBg, color, borderColor: color }
}
