import type { AgentAction } from '../api/client'
import { formatDateTime } from '../utils/formatDate'
import './Timeline.css'

type Props = {
  actions: AgentAction[]
  /** When true, show investigation-oriented chrome (status icons, running pulse). */
  live?: boolean
}

const ACTION_LABELS: Record<string, string> = {
  anomaly_detected: 'Anomaly detected',
  investigation_started: 'Starting investigation…',
  investigation_finished: 'Investigation complete',
  investigation_failed: 'Investigation failed',
  tool_started: 'Tool running',
  tool_completed: 'Tool completed',
  work_order_created: 'Work order created',
  technician_notified: 'Technician notified',
  machine_status_updated: 'Machine status updated',
  shutdown_approval_requested: 'Shutdown approval requested',
  shutdown_approved: 'Shutdown approved',
  shutdown_rejected: 'Shutdown rejected',
}

function inferStatus(action: AgentAction, all: AgentAction[]): string {
  if (action.status) {
    if (
      action.status === 'running' &&
      action.action === 'investigation_started' &&
      all.some(
        (a) =>
          a.action === 'investigation_finished' ||
          a.action === 'investigation_failed',
      )
    ) {
      return action.action === 'investigation_started' &&
        all.some((a) => a.action === 'investigation_failed')
        ? 'failed'
        : 'completed'
    }
    return action.status
  }
  if (action.action === 'investigation_failed') return 'failed'
  if (action.action === 'tool_started') return 'running'
  return 'completed'
}

function stepTitle(action: AgentAction): string {
  if (action.label) return action.label
  if (action.action && ACTION_LABELS[action.action]) {
    return ACTION_LABELS[action.action]
  }
  return (action.action || 'action').replaceAll('_', ' ')
}

function statusGlyph(status: string): string {
  if (status === 'running') return '◌'
  if (status === 'failed') return '✕'
  if (status === 'waiting') return '·'
  return '✓'
}

export function InvestigationTimeline({ actions, live = true }: Props) {
  if (!actions.length) {
    return <p className="empty">No agent actions recorded yet.</p>
  }

  const sorted = [...actions].sort((a, b) =>
    (a.timestamp || '').localeCompare(b.timestamp || ''),
  )

  return (
    <ol className={`timeline ${live ? 'timeline--live' : ''}`}>
      {sorted.map((action, index) => {
        const status = inferStatus(action, sorted)
        const running = status === 'running'
        return (
          <li
            key={`${action.action_id || action.action}-${action.timestamp || index}-${index}`}
            className={`timeline-step timeline-step--${status}${running ? ' timeline-step--active' : ''}`}
          >
            <div className={`timeline-dot timeline-dot--${status}`} aria-hidden>
              {live ? statusGlyph(status) : null}
            </div>
            <div className="timeline-body">
              <div className="timeline-meta">
                <strong>{stepTitle(action)}</strong>
                <span className="mono">
                  {action.timestamp ? formatDateTime(action.timestamp) : ''}
                </span>
              </div>
              <p>{action.detail || 'No detail'}</p>
              {running ? (
                <span className="timeline-running-tag">In progress</span>
              ) : null}
            </div>
          </li>
        )
      })}
    </ol>
  )
}

/** @deprecated Prefer InvestigationTimeline — kept for gradual migration. */
export function Timeline({ actions }: { actions: AgentAction[] }) {
  return <InvestigationTimeline actions={actions} live />
}
