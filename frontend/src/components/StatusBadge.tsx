import './StatusBadge.css'

const TONE: Record<string, string> = {
  HEALTHY: 'ok',
  MONITORING: 'warn',
  WARNING: 'warn',
  MAINTENANCE_REQUIRED: 'danger',
  OUT_OF_SERVICE: 'danger',
  OPEN: 'warn',
  INVESTIGATING: 'warn',
  RESOLVED: 'ok',
  IN_PROGRESS: 'warn',
  COMPLETED: 'ok',
  LOW: 'ok',
  MEDIUM: 'warn',
  HIGH: 'danger',
  CRITICAL: 'danger',
  URGENT: 'danger',
  PENDING: 'warn',
  APPROVED: 'ok',
  REJECTED: 'neutral',
}

type Props = {
  value: string
  label?: string
}

export function StatusBadge({ value, label }: Props) {
  const tone = TONE[value] || 'neutral'
  return (
    <span className={`badge badge-${tone}`}>
      {label || value.replaceAll('_', ' ')}
    </span>
  )
}
