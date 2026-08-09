import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  api,
  type AgentAction,
  type Incident,
  type Machine,
  type TelemetrySample,
  type WorkOrder,
} from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { InvestigationTimeline } from '../components/Timeline'
import { TelemetryCharts } from '../components/TelemetryCharts'
import { formatDateTime } from '../utils/formatDate'
import '../styles/pages.css'
import '../components/Timeline.css'

export function MachineDetailPage() {
  const { machineId = 'PUMP-04' } = useParams()
  const [machine, setMachine] = useState<Machine | null>(null)
  const [openIncidentId, setOpenIncidentId] = useState<string | null>(null)
  const [samples, setSamples] = useState<TelemetrySample[]>([])
  const [limits, setLimits] = useState({
    temperature_c: 70,
    vibration_mm_s: 4.5,
    motor_current_a: 12.5,
  })
  const [history, setHistory] = useState<Array<Record<string, string>>>([])
  const [incident, setIncident] = useState<Incident | null>(null)
  const [actions, setActions] = useState<AgentAction[]>([])
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [error, setError] = useState<string | null>(null)
  const [forceBusy, setForceBusy] = useState(false)
  const [forceMessage, setForceMessage] = useState<string | null>(null)

  const loadMachine = useCallback(
    (opts?: { silent?: boolean }) => {
      const silent = Boolean(opts?.silent)
      return Promise.all([api.machine(machineId), api.telemetry(machineId)])
        .then(([mach, tel]) => {
          setMachine(mach.machine)
          setOpenIncidentId(mach.open_incident_id)
          setHistory(mach.maintenance_history)
          setSamples(tel.samples)
          setLimits(tel.limits)
          if (!silent) setError(null)
          return mach.open_incident_id
        })
        .catch((err: Error) => {
          if (!silent) setError(err.message)
          return null
        })
    },
    [machineId],
  )

  const loadIncident = useCallback(
    (incidentId: string, opts?: { silent?: boolean }) => {
      const silent = Boolean(opts?.silent)
      return api
        .incident(incidentId)
        .then((data) => {
          setIncident(data.incident)
          setActions(data.agent_actions)
          setWorkOrders(data.work_orders)
          if (!silent) setError(null)
        })
        .catch((err: Error) => {
          if (!silent) setError(err.message)
        })
    },
    [],
  )

  useEffect(() => {
    void loadMachine().then((id) => {
      if (id) void loadIncident(id)
      else {
        setIncident(null)
        setActions([])
        setWorkOrders([])
      }
    })
  }, [loadMachine, loadIncident])

  const investigating = incident?.status === 'INVESTIGATING'
  const pollFast = investigating || Boolean(openIncidentId && !incident?.agent_summary)

  useEffect(() => {
    const intervalMs = pollFast ? 800 : 1500
    const id = window.setInterval(() => {
      void loadMachine({ silent: true }).then((openId) => {
        if (openId) void loadIncident(openId, { silent: true })
      })
    }, intervalMs)
    return () => window.clearInterval(id)
  }, [loadMachine, loadIncident, pollFast])

  const vibrationTrail = useMemo(() => {
    const recent = [...samples]
      .sort((a, b) => a.timestamp.localeCompare(b.timestamp))
      .slice(-6)
      .map((s) => s.vibration_mm_s)
    if (recent.length < 2) return null
    return recent.map((v) => v.toFixed(1)).join(' → ') + ' mm/s'
  }, [samples])

  const primaryWo = workOrders[0] ?? null
  const diagnosisReady = Boolean(
    incident?.suspected_failure ||
      incident?.agent_summary ||
      (incident && incident.status !== 'INVESTIGATING' && incident.status !== 'OPEN'),
  )

  const onForceAnomaly = async () => {
    setForceBusy(true)
    setForceMessage(null)
    try {
      const result = await api.forceAnomaly(machineId)
      setForceMessage(
        result.incident_id
          ? `Live investigation started: ${result.incident_id}`
          : 'Anomaly injected — waiting for incident…',
      )
      await loadMachine()
      if (result.incident_id) await loadIncident(result.incident_id)
    } catch (err) {
      setForceMessage(
        err instanceof Error ? err.message : 'Failed to force anomaly',
      )
    } finally {
      setForceBusy(false)
    }
  }

  if (error && !machine) return <p className="error">{error}</p>
  if (!machine) return <p className="muted">Loading machine…</p>

  return (
    <div className="page">
      <section className="hero">
        <h1>{machine.machine_id}</h1>
        <p>
          {machine.name} · {machine.manufacturer} {machine.model}
        </p>
        <StatusBadge value={machine.status} />
        {openIncidentId ? (
          <p>
            Active incident:{' '}
            <Link to={`/incidents/${openIncidentId}`}>{openIncidentId}</Link>
          </p>
        ) : (
          <p className="muted">No open incident.</p>
        )}
        <p className="demo-note">
          Telemetry is simulated · Gemini agent investigation runs live
        </p>
        {machine.machine_id === 'PUMP-04' ? (
          <div style={{ marginTop: '0.75rem' }}>
            <button
              type="button"
              className="seed-btn"
              disabled={forceBusy}
              onClick={() => void onForceAnomaly()}
            >
              {forceBusy ? 'Injecting anomaly…' : 'Run live investigation'}
            </button>
            {forceMessage ? (
              <p className="fleet-seed-msg mono">{forceMessage}</p>
            ) : null}
          </div>
        ) : null}
      </section>

      {incident ? (
        <div
          className={`investigation-banner${
            investigating ? '' : ' investigation-banner--done'
          }`}
        >
          <strong>
            {investigating ? '⚠ Anomaly detected' : 'Investigation update'}
          </strong>
          <p>
            {investigating
              ? 'Maintenance Agent investigating…'
              : incident.suspected_failure
                ? `Diagnosis: ${incident.suspected_failure}`
                : `Incident ${incident.status.replaceAll('_', ' ').toLowerCase()}`}
          </p>
          {vibrationTrail ? (
            <p className="vibration-trail">Vibration {vibrationTrail}</p>
          ) : null}
          <p className="muted mono" style={{ margin: 0 }}>
            Detected {formatDateTime(incident.detected_at)} · {incident.trigger_reason}
          </p>
        </div>
      ) : null}

      <div className="split split-top">
        <section className="panel">
          <h2>Telemetry</h2>
          <TelemetryCharts samples={samples} limits={limits} />
        </section>

        <section className="panel stack">
          <h2>Agent investigation</h2>
          {!incident ? (
            <p className="muted">
              Waiting for an anomaly. Start the simulator or run a live
              investigation on PUMP-04.
            </p>
          ) : (
            <>
              <InvestigationTimeline actions={actions} live />
              {diagnosisReady ? (
                <div className="diagnosis-result" style={{ marginTop: '1rem' }}>
                  <h3 className="result-headline">Diagnosis</h3>
                  <div className="meta-grid">
                    <div>
                      <span>Suspected problem</span>
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
                      <span>Severity / risk</span>
                      <strong>{incident.severity}</strong>
                    </div>
                    <div>
                      <span>Evidence</span>
                      <strong>{incident.trigger_reason}</strong>
                    </div>
                  </div>
                  {primaryWo ? (
                    <>
                      <div>
                        <span className="muted">Recommended action</span>
                        <p style={{ margin: '0.25rem 0 0' }}>
                          {primaryWo.recommended_action || primaryWo.title}
                        </p>
                      </div>
                      <p className="mono">
                        ✓ Work Order{' '}
                        <Link to={`/work-orders`}>{primaryWo.work_order_id}</Link>{' '}
                        created
                      </p>
                    </>
                  ) : null}
                  <Link to={`/incidents/${incident.incident_id}`}>
                    Open full incident →
                  </Link>
                </div>
              ) : null}
            </>
          )}
        </section>
      </div>

      <section className="panel">
        <h2>Maintenance history</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Summary</th>
              <th>Tech</th>
            </tr>
          </thead>
          <tbody>
            {history.map((row, idx) => (
              <tr key={`${row.date}-${idx}`}>
                <td className="mono">{row.date}</td>
                <td>{row.type}</td>
                <td>{row.summary}</td>
                <td>{row.technician}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
