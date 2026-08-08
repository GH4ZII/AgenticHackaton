import type { AgentAction } from '../api/client'
import './Timeline.css'

type Props = {
  actions: AgentAction[]
}

export function Timeline({ actions }: Props) {
  if (!actions.length) {
    return <p className="empty">No agent actions recorded yet.</p>
  }

  return (
    <ol className="timeline">
      {actions.map((action, index) => (
        <li key={`${action.action_id || action.action}-${index}`}>
          <div className="timeline-dot" />
          <div className="timeline-body">
            <div className="timeline-meta">
              <strong>{(action.action || 'action').replaceAll('_', ' ')}</strong>
              <span className="mono">{action.timestamp || '—'}</span>
            </div>
            <p>{action.detail || 'No detail'}</p>
          </div>
        </li>
      ))}
    </ol>
  )
}
