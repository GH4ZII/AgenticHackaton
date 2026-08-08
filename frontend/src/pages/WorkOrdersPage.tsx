import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type WorkOrder } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import '../styles/pages.css'

export function WorkOrdersPage() {
  const [orders, setOrders] = useState<WorkOrder[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .workOrders()
      .then((data) => setOrders(data.work_orders))
      .catch((err: Error) => setError(err.message))
  }, [])

  if (error) return <p className="error">{error}</p>

  return (
    <div className="page">
      <section className="hero">
        <h1>Work orders</h1>
        <p>Maintenance jobs created by the agent after diagnosis.</p>
      </section>
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
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted">
                  No work orders yet. Load demo state first.
                </td>
              </tr>
            ) : (
              orders.map((wo) => (
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
                  <td className="mono">{wo.created_at}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
