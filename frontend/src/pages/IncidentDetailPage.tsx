import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  api,
  type AgentAction,
  type Incident,
  type InventoryItem,
  type WorkOrder,
} from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { Timeline } from '../components/Timeline'
import '../styles/pages.css'

export function IncidentDetailPage() {
  const { incidentId = '' } = useParams()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [actions, setActions] = useState<AgentAction[]>([])
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = () => {
    if (!incidentId) return Promise.resolve()
    return api
      .incident(incidentId)
      .then((data) => {
        setIncident(data.incident)
        setWorkOrders(data.work_orders)
        setActions(data.agent_actions)
        setInventory(data.inventory)
      })
      .catch((err: Error) => setError(err.message))
  }

  useEffect(() => {
    void load()
  }, [incidentId])

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

  if (error && !incident) {
    return <p className="error">{error}</p>
  }
  if (!incident) {
    return <p className="muted">Loading incident…</p>
  }

  const needed = new Set(
    workOrders.flatMap((wo) => wo.required_parts.map((p) => p.toLowerCase())),
  )
  const parts = inventory.filter(
    (item) =>
      needed.has(item.part_number.toLowerCase()) ||
      needed.has(item.part_id.toLowerCase()) ||
      [...needed].some((n) => item.name.toLowerCase().includes(n)),
  )

  return (
    <div className="page">
      <section className="hero">
        <h1>{incident.incident_id}</h1>
        <p>
          {incident.machine_id} · detected{' '}
          <span className="mono">{incident.detected_at}</span>
        </p>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <StatusBadge value={incident.severity} />
          <StatusBadge value={incident.status} />
        </div>
      </section>

      {message ? <p className="seed-msg mono">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}

      <div className="split">
        <section className="panel stack">
          <h2>Diagnosis</h2>
          <div className="meta-grid">
            <div>
              <span>Suspected failure</span>
              <strong>{incident.suspected_failure || '—'}</strong>
            </div>
            <div>
              <span>Confidence</span>
              <strong>
                {incident.confidence != null
                  ? `${Math.round(incident.confidence * 100)}%`
                  : '—'}
              </strong>
            </div>
            <div>
              <span>Machine</span>
              <strong>
                <Link to={`/machines/${incident.machine_id}`}>
                  {incident.machine_id}
                </Link>
              </strong>
            </div>
            <div>
              <span>Trigger</span>
              <strong>{incident.trigger_reason}</strong>
            </div>
          </div>
          <div>
            <h2>Agent summary</h2>
            <div className="summary-box">
              {incident.agent_summary || 'No summary yet.'}
            </div>
          </div>
        </section>

        <section className="panel stack">
          <h2>Related work orders</h2>
          {workOrders.length === 0 ? (
            <p className="muted">No work orders linked yet.</p>
          ) : (
            workOrders.map((wo) => {
              const canComplete =
                wo.status === 'OPEN' || wo.status === 'IN_PROGRESS'
              return (
                <div key={wo.work_order_id} className="stack">
                  <strong className="mono">{wo.work_order_id}</strong>
                  <div>{wo.title}</div>
                  <StatusBadge value={wo.priority} label={`Priority ${wo.priority}`} />
                  <StatusBadge value={wo.status} />
                  <p className="muted">{wo.recommended_action}</p>
                  {canComplete ? (
                    <button
                      className="seed-btn"
                      type="button"
                      disabled={busyId === wo.work_order_id}
                      onClick={() => void onComplete(wo.work_order_id)}
                    >
                      {busyId === wo.work_order_id
                        ? 'Verifying…'
                        : 'Mark as completed'}
                    </button>
                  ) : null}
                </div>
              )
            })
          )}

          <h2>Spare parts</h2>
          {parts.length === 0 ? (
            <p className="muted">No matched inventory rows.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Part</th>
                  <th>Stock</th>
                  <th>Location</th>
                </tr>
              </thead>
              <tbody>
                {parts.map((part) => (
                  <tr key={part.part_id}>
                    <td>
                      {part.name}
                      <div className="mono muted">{part.part_number}</div>
                    </td>
                    <td className="mono">{part.stock}</td>
                    <td>{part.location}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>

      <section className="panel">
        <h2>Agent activity timeline</h2>
        <Timeline actions={actions} />
      </section>
    </div>
  )
}
