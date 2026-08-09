function parseDate(value?: string | null): Date | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date
}

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

/** Local datetime as DD.MM.YYYY HH:mm */
export function formatDateTime(value?: string | null): string {
  const date = parseDate(value)
  if (!date) return '—'
  return `${pad(date.getDate())}.${pad(date.getMonth() + 1)}.${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** Local time as HH:mm (for chart axes) */
export function formatTime(value?: string | null): string {
  const date = parseDate(value)
  if (!date) return '—'
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}
