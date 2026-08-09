import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type WorkOrder } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { formatDateTime } from '../utils/formatDate'
import '../styles/pages.css'

export function WorkOrdersPage() {
  const [orders, setOrders] = useState<WorkOrder[]>([])
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = () =>
    api
      .workOrders()
      .then((data) => setOrders(data.work_orders))
      .catch((err: Error) => setError(err.message))

  useEffect(() => {
    load()
  }, [])

  const onComplete = async (workOrderId: string) => {
    setBusyId(workOrderId)
    setMessage(null)
    setError(null)
    try {
      const result = await api.completeWorkOrder(workOrderId)
      setMessage(
        `${result.message} Machine: ${result.machine_status || 'n/a'}; ` +
          `incident: ${result.incident?.status || 'n/a'}.`,
      )
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Complete failed')
    } finally {
      setBusyId(null)
    }
  }

  if (error && orders.length === 0) return <p className="error">{error}</p>

  return (
    <div className="page">
      <section className="hero">
        <h1>Work orders</h1>
        <p>
          Maintenance jobs created by the agent. Mark completed to inject healthy
          telemetry and let the agent verify the repair.
        </p>
      </section>
      {message ? <p className="seed-msg mono">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Machine</th>
              <th>Title</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr>
                <td colSpan={7} className="muted">
                  No work orders yet. Load demo state first.
                </td>
              </tr>
            ) : (
              orders.map((wo) => {
                const canComplete =
                  wo.status === 'OPEN' || wo.status === 'IN_PROGRESS'
                return (
                  <tr key={wo.work_order_id}>
                    <td className="mono">{wo.work_order_id}</td>
                    <td>
                      <Link to={`/machines/${wo.machine_id}`}>{wo.machine_id}</Link>
                    </td>
                    <td>
                      {wo.title}
                      {wo.incident_id ? (
                        <div>
                          <Link to={`/incidents/${wo.incident_id}`}>
                            {wo.incident_id}
                          </Link>
                        </div>
                      ) : null}
                    </td>
                    <td>
                      <StatusBadge value={wo.priority} />
                    </td>
                    <td>
                      <StatusBadge value={wo.status} />
                    </td>
                    <td className="mono">{formatDateTime(wo.created_at)}</td>
                    <td>
                      {canComplete ? (
                        <button
                          className="seed-btn"
                          type="button"
                          disabled={busyId === wo.work_order_id}
                          onClick={() => onComplete(wo.work_order_id)}
                        >
                          {busyId === wo.work_order_id
                            ? 'Verifying…'
                            : 'Mark as completed'}
                        </button>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
