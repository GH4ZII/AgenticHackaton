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

export function DashboardPage() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [machines, setMachines] = useState<Machine[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [error, setError] = useState<string | null>(null)
  const [seeding, setSeeding] = useState(false)
  const [seedMessage, setSeedMessage] = useState<string | null>(null)

  const load = useCallback(() => {
    Promise.all([
      api.dashboard(),
      api.machines(),
      api.incidents(),
      api.pendingApprovals(),
    ])
      .then(([dash, mach, inc, pending]) => {
        setSummary(dash)
        setMachines(mach.machines)
        setIncidents(inc.incidents)
        setApprovals(pending.approvals)
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    load()
  }, [load])

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
          <h2>Machines</h2>
          {seedMessage ? (
            <p className="seed-msg mono fleet-seed-msg">{seedMessage}</p>
          ) : null}
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
                  No incidents yet. Use &quot;Load demo state&quot; on a machine
                  card.
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
