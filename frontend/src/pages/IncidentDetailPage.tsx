import { useCallback, useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import { Link, useParams } from 'react-router-dom'
import {
  api,
  type AgentAction,
  type ApprovalRequest,
  type Incident,
  type InventoryItem,
  type WorkOrder,
} from '../api/client'
import { CriticalApprovalBanner } from '../components/CriticalBanner'
import { StatusBadge } from '../components/StatusBadge'
import { InvestigationTimeline } from '../components/Timeline'
import { formatDateTime } from '../utils/formatDate'
import { extractReasoning, sanitizeAgentText } from '../utils/agentText'
import '../styles/pages.css'
import '../components/Timeline.css'

export function IncidentDetailPage() {
  const { incidentId = '' } = useParams()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [actions, setActions] = useState<AgentAction[]>([])
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = useCallback(
    (opts?: { silent?: boolean }) => {
      if (!incidentId) return Promise.resolve()
      const silent = Boolean(opts?.silent)
      return Promise.all([api.incident(incidentId), api.listApprovals()])
        .then(([data, approvalData]) => {
          setIncident(data.incident)
          setWorkOrders(data.work_orders)
          setActions(data.agent_actions)
          setInventory(data.inventory)
          setApprovals(
            approvalData.approvals.filter((a) => a.incident_id === incidentId),
          )
          if (!silent) setError(null)
        })
        .catch((err: Error) => {
          if (!silent) setError(err.message)
        })
    },
    [incidentId],
  )

  useEffect(() => {
    void load()
  }, [load])

  const investigating = incident?.status === 'INVESTIGATING'

  useEffect(() => {
    if (!investigating) return
    const id = window.setInterval(() => {
      void load({ silent: true })
    }, 800)
    return () => window.clearInterval(id)
  }, [investigating, load])

  // Brief post-investigation poll so enrichment / WO land without refresh.
  useEffect(() => {
    if (investigating || !incident) return
    if (incident.agent_summary && workOrders.length) return
    const id = window.setInterval(() => {
      void load({ silent: true })
    }, 1000)
    const stop = window.setTimeout(() => window.clearInterval(id), 15000)
    return () => {
      window.clearInterval(id)
      window.clearTimeout(stop)
    }
  }, [investigating, incident, workOrders.length, load])

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
  const reasoning = extractReasoning(incident.agent_summary)
  const summaryText = incident.agent_summary
    ? sanitizeAgentText(incident.agent_summary)
    : null
  const primaryWo = workOrders[0] ?? null

  return (
    <div className="page">
      <section className="hero">
        <h1>{incident.incident_id}</h1>
        <p>
          {incident.machine_id} · detected{' '}
          <span className="mono">{formatDateTime(incident.detected_at)}</span>
        </p>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <StatusBadge value={incident.severity} />
          <StatusBadge value={incident.status} />
        </div>
        <p className="demo-note">
          Telemetry may be simulated · agent investigation runs live via Gemini
        </p>
      </section>

      <CriticalApprovalBanner approvals={approvals} onResolved={() => void load()} />

      {message ? <p className="seed-msg mono">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}

      {investigating ? (
        <div className="investigation-banner">
          <strong>⚠ Anomaly detected</strong>
          <p>Maintenance Agent investigating…</p>
        </div>
      ) : null}

      <div className="split split-top">
        <section className="panel stack">
          <h2>Diagnosis</h2>
          <div className="diagnosis-result">
            <p className="result-headline">
              {incident.suspected_failure ||
                (investigating ? 'Diagnosis in progress…' : 'Pending diagnosis')}
            </p>
            <div className="meta-grid">
              <div>
                <span>Confidence</span>
                <strong>
                  {incident.confidence != null
                    ? `${Math.round(incident.confidence * 100)}%`
                    : '—'}
                </strong>
              </div>
              <div>
                <span>Severity / risk</span>
                <strong>{incident.severity}</strong>
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
                <span>Evidence used</span>
                <strong>{incident.trigger_reason}</strong>
              </div>
            </div>
            {primaryWo?.recommended_action ? (
              <div>
                <span className="muted">Recommended action</span>
                <p style={{ margin: '0.25rem 0 0' }}>
                  {primaryWo.recommended_action}
                </p>
              </div>
            ) : null}
            {primaryWo ? (
              <p className="mono" style={{ margin: 0 }}>
                ✓ Work Order {primaryWo.work_order_id} created
              </p>
            ) : null}
            {reasoning ? (
              <div className="reasoning-box">
                <span>Reasoning</span>
                <p>{reasoning}</p>
              </div>
            ) : null}
          </div>
        </section>

        <section className="panel stack">
          <h2>Related work orders</h2>
          {workOrders.length === 0 ? (
            <p className="muted">
              {investigating
                ? 'Work order will appear when the agent creates one…'
                : 'No work orders linked yet.'}
            </p>
          ) : (
            workOrders.map((wo) => {
              const canComplete =
                wo.status === 'OPEN' || wo.status === 'IN_PROGRESS'
              return (
                <div key={wo.work_order_id} className="wo-card">
                  <strong className="mono">{wo.work_order_id}</strong>
                  <div>{wo.title}</div>
                  <div className="wo-badges">
                    <StatusBadge
                      value={wo.priority}
                      label={`Priority ${wo.priority}`}
                    />
                    <StatusBadge value={wo.status} />
                  </div>
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
        <h2>Agent activity</h2>
        <InvestigationTimeline actions={actions} live />
      </section>

      <section className="panel">
        <h2>Agent summary</h2>
        {summaryText ? (
          <div className="summary-box markdown-body">
            <Markdown>{summaryText}</Markdown>
          </div>
        ) : (
          <p className="muted">
            {investigating
              ? 'Summary will appear when the agent finishes…'
              : 'No summary yet.'}
          </p>
        )}
      </section>
    </div>
  )
}
