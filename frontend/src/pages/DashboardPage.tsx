import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  api,
  type ApprovalRequest,
  type DashboardSummary,
  type Incident,
  type Machine,
} from '../api/client'
import { CriticalApprovalBanner } from '../components/CriticalBanner'
import { MachineCard } from '../components/MachineCard'
import { StatusBadge } from '../components/StatusBadge'
import '../styles/pages.css'

type SimStatus = {
  running: boolean
  phase: string
  ticks: number
  started_at: string | null
  active_failures: Array<{
    machine_id: string
    mode: string
    progress: number
  }>
  last_error: string | null
}

function formatSimStatus(status: SimStatus | null): string {
  if (!status?.running) {
    if (status?.phase === 'stopped') return 'Simulator stopped'
    if (status?.phase === 'idle') return 'Simulator idle'
    return 'Simulator off'
  }
  if (!status.active_failures.length) {
    return `Running · all healthy (tick ${status.ticks})`
  }
  const failing = status.active_failures
    .map((f) => `${f.machine_id} (${f.mode.replaceAll('_', ' ')})`)
    .join(', ')
  return `Running · failing ${failing}`
}

export function DashboardPage() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [machines, setMachines] = useState<Machine[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [error, setError] = useState<string | null>(null)
  const [seeding, setSeeding] = useState(false)
  const [seedMessage, setSeedMessage] = useState<string | null>(null)
  const [simStatus, setSimStatus] = useState<SimStatus | null>(null)
  const [simBusy, setSimBusy] = useState(false)
  const [simMessage, setSimMessage] = useState<string | null>(null)

  const load = useCallback((opts?: { silent?: boolean }) => {
    const silent = Boolean(opts?.silent)
    return Promise.all([
      api.dashboard(),
      api.machines(),
      api.incidents(),
      api.pendingApprovals(),
      api.simulatorStatus(),
    ])
      .then(([dash, mach, inc, pending, sim]) => {
        setSummary(dash)
        setMachines(mach.machines)
        setIncidents(inc.incidents)
        setApprovals(pending.approvals)
        setSimStatus(sim)
        if (!silent) setError(null)
      })
      .catch((err: Error) => {
        // Keep the last good snapshot during background polls so a blip
        // does not wipe the dashboard while the agent is busy.
        if (!silent) setError(err.message)
      })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // Always poll while the dashboard is open so new incidents / WARNING
  // status appear without a manual refresh (agent may still be running).
  useEffect(() => {
    const intervalMs = simStatus?.running ? 1500 : 3000
    const id = window.setInterval(() => {
      load({ silent: true })
    }, intervalMs)
    return () => window.clearInterval(id)
  }, [simStatus?.running, load])

  const onSeedDemo = useCallback(async () => {
    setSeeding(true)
    setSeedMessage(null)
    try {
      const result = await api.seedDemo()
      setSeedMessage(
        `Demo ready: ${result.incident_id} (incident ${
          result.created_incident ? 'created' : 'exists'
        })`,
      )
      await load()
      navigate(`/incidents/${result.incident_id}`)
    } catch (err) {
      setSeedMessage(
        err instanceof Error ? err.message : 'Failed to load demo state',
      )
    } finally {
      setSeeding(false)
    }
  }, [load, navigate])

  const onSeedCritical = useCallback(async () => {
    setSeeding(true)
    setSeedMessage(null)
    try {
      const result = await api.seedCritical()
      setSeedMessage(
        `CRITICAL demo: ${result.approval_id} PENDING — machine not shut down`,
      )
      await load()
      navigate('/approvals')
    } catch (err) {
      setSeedMessage(
        err instanceof Error ? err.message : 'Failed to load critical demo',
      )
    } finally {
      setSeeding(false)
    }
  }, [load, navigate])

  const onStartSim = useCallback(async () => {
    setSimBusy(true)
    setSimMessage(null)
    try {
      const result = await api.simulatorStart()
      setSimMessage('Simulator started — fleet telemetry is live')
      setSimStatus({
        running: result.running,
        phase: result.phase,
        ticks: result.ticks,
        started_at: result.started_at,
        active_failures: result.active_failures,
        last_error: null,
      })
      await load()
    } catch (err) {
      setSimMessage(
        err instanceof Error ? err.message : 'Failed to start simulator',
      )
    } finally {
      setSimBusy(false)
    }
  }, [load])

  const onStopSim = useCallback(async () => {
    setSimBusy(true)
    setSimMessage(null)
    try {
      await api.simulatorStop()
      setSimMessage('Simulator stopped')
      await load()
    } catch (err) {
      setSimMessage(
        err instanceof Error ? err.message : 'Failed to stop simulator',
      )
    } finally {
      setSimBusy(false)
    }
  }, [load])

  const onResetSim = useCallback(async () => {
    setSimBusy(true)
    setSimMessage(null)
    try {
      await api.simulatorReset()
      setSimMessage('Fleet reset to healthy')
      await load()
    } catch (err) {
      setSimMessage(
        err instanceof Error ? err.message : 'Failed to reset simulator',
      )
    } finally {
      setSimBusy(false)
    }
  }, [load])

  if (error) {
    return (
      <div className="page">
        <p className="error">
          Could not load dashboard. Is the API running on port 8081?
        </p>
        <p className="muted mono">{error}</p>
      </div>
    )
  }

  const running = Boolean(simStatus?.running)

  return (
    <div className="page">
      <section className="hero">
        <h1>Maintenance Agent</h1>
        <p>
          Fleet health, open incidents, and autonomous maintenance actions — so
          you can see what the agent decided and why.
        </p>
      </section>

      <CriticalApprovalBanner approvals={approvals} onResolved={load} />

      <section className="stats">
        <div className="stat">
          <span>Machines</span>
          <strong>{summary?.total_machines ?? '—'}</strong>
        </div>
        <div className="stat">
          <span>Healthy</span>
          <strong>{summary?.healthy_machines ?? '—'}</strong>
        </div>
        <div className="stat">
          <span>Open incidents</span>
          <strong>{summary?.open_incidents ?? '—'}</strong>
        </div>
        <div className="stat">
          <span>Active work orders</span>
          <strong>{summary?.active_work_orders ?? '—'}</strong>
        </div>
      </section>

      <section className="fleet-section">
        <div className="fleet-section-head">
          <div>
            <h2>Machines</h2>
            <p className="muted mono fleet-sim-status">
              {formatSimStatus(simStatus)}
            </p>
            {simMessage ? (
              <p className="fleet-seed-msg mono">{simMessage}</p>
            ) : null}
            {seedMessage ? (
              <p className="fleet-seed-msg mono">{seedMessage}</p>
            ) : null}
          </div>
          <div className="fleet-sim-actions">
            {running ? (
              <button
                type="button"
                className="seed-btn seed-btn-ghost"
                onClick={onStopSim}
                disabled={simBusy}
              >
                {simBusy ? 'Working…' : 'Stop simulator'}
              </button>
            ) : (
              <button
                type="button"
                className="seed-btn"
                onClick={onStartSim}
                disabled={simBusy}
              >
                {simBusy ? 'Working…' : 'Start simulator'}
              </button>
            )}
            <button
              type="button"
              className="seed-btn seed-btn-ghost"
              onClick={onResetSim}
              disabled={simBusy}
            >
              Reset
            </button>
          </div>
        </div>
        <div className="machine-grid">
          {machines.map((m) => (
            <MachineCard
              key={m.machine_id}
              machine={m}
              seeding={seeding}
              onSeedDemo={onSeedDemo}
              onSeedCritical={onSeedCritical}
            />
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Incidents</h2>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Machine</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Failure</th>
            </tr>
          </thead>
          <tbody>
            {incidents.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted">
                  No incidents yet. Start the simulator or use demo buttons on
                  PUMP-04.
                </td>
              </tr>
            ) : (
              incidents.map((incident) => (
                <tr key={incident.incident_id}>
                  <td>
                    <Link to={`/incidents/${incident.incident_id}`}>
                      {incident.incident_id}
                    </Link>
                  </td>
                  <td className="mono">{incident.machine_id}</td>
                  <td>
                    <StatusBadge value={incident.severity} />
                  </td>
                  <td>
                    <StatusBadge value={incident.status} />
                  </td>
                  <td>{incident.suspected_failure || 'Pending diagnosis'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
