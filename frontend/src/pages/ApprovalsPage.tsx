import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type ApprovalRequest } from '../api/client'
import { CriticalApprovalBanner } from '../components/CriticalBanner'
import { StatusBadge } from '../components/StatusBadge'
import '../styles/pages.css'

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    return api
      .listApprovals()
      .then((data) => setApprovals(data.approvals))
      .catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  if (error) {
    return <p className="error">{error}</p>
  }

  return (
    <div className="page">
      <section className="hero">
        <h1>Shutdown approvals</h1>
        <p>
          CRITICAL recommendations wait here. Approve sets the machine{' '}
          <span className="mono">OUT_OF_SERVICE</span>; Reject leaves it in
          maintenance.
        </p>
      </section>

      <CriticalApprovalBanner approvals={approvals} onResolved={() => void load()} />

      <section className="panel">
        <h2>All requests</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Approval</th>
              <th>Machine</th>
              <th>Incident</th>
              <th>Status</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {approvals.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted">
                  No approvals yet. Click &quot;Load critical demo&quot;.
                </td>
              </tr>
            ) : (
              approvals.map((a) => (
                <tr key={a.approval_id}>
                  <td className="mono">{a.approval_id}</td>
                  <td className="mono">{a.machine_id}</td>
                  <td>
                    <Link to={`/incidents/${a.incident_id}`}>{a.incident_id}</Link>
                  </td>
                  <td>
                    <StatusBadge value={a.status} />
                  </td>
                  <td>{a.reason}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
