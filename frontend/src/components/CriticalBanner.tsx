import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type ApprovalRequest } from '../api/client'
import './CriticalBanner.css'

type Props = {
  approvals: ApprovalRequest[]
  onResolved?: () => void
}

export function CriticalApprovalBanner({ approvals, onResolved }: Props) {
  const pending = approvals.filter((a) => a.status === 'PENDING')
  const [busyId, setBusyId] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (pending.length === 0) return null

  const act = async (id: string, decision: 'approve' | 'reject') => {
    setBusyId(id)
    setMessage(null)
    setError(null)
    try {
      const result =
        decision === 'approve' ? await api.approve(id) : await api.reject(id)
      setMessage(result.message)
      onResolved?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <section className="critical-banner" role="alert">
      <div className="critical-banner-head">
        <strong>CRITICAL — shutdown recommended</strong>
        <span className="muted">
          Agent requested approval. Machine was not shut down.
        </span>
      </div>
      {message ? <p className="critical-msg mono">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}
      <ul className="critical-list">
        {pending.map((a) => (
          <li key={a.approval_id}>
            <div>
              <Link className="mono" to={`/incidents/${a.incident_id}`}>
                {a.approval_id}
              </Link>
              <span className="mono muted"> · {a.machine_id}</span>
              <p>{a.reason}</p>
            </div>
            <div className="critical-actions">
              <button
                type="button"
                className="approve-btn"
                disabled={busyId === a.approval_id}
                onClick={() => void act(a.approval_id, 'approve')}
              >
                {busyId === a.approval_id ? '…' : 'Approve'}
              </button>
              <button
                type="button"
                className="reject-btn"
                disabled={busyId === a.approval_id}
                onClick={() => void act(a.approval_id, 'reject')}
              >
                Reject
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
