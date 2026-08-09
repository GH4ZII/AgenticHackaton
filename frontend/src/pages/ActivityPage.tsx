import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AgentAction, type Incident } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { Timeline } from '../components/Timeline'
import '../styles/pages.css'

type IncidentGroup = {
  incidentId: string | null
  machineId?: string
  incident?: Incident
  actions: AgentAction[]
}

function latestTimestamp(actions: AgentAction[]): string {
  let max = ''
  for (const a of actions) {
    if (a.timestamp && a.timestamp > max) max = a.timestamp
  }
  return max
}

export function ActivityPage() {
  const [actions, setActions] = useState<AgentAction[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.agentActions(), api.incidents()])
      .then(([actionData, incidentData]) => {
        setActions(actionData.agent_actions)
        setIncidents(incidentData.incidents)
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  const groups = useMemo(() => {
    const byIncident = new Map<string, AgentAction[]>()
    const unassigned: AgentAction[] = []

    for (const action of actions) {
      if (action.incident_id) {
        const list = byIncident.get(action.incident_id) ?? []
        list.push(action)
        byIncident.set(action.incident_id, list)
      } else {
        unassigned.push(action)
      }
    }

    const incidentMap = new Map(
      incidents.map((inc) => [inc.incident_id, inc]),
    )

    const grouped: IncidentGroup[] = [...byIncident.entries()].map(
      ([incidentId, groupActions]) => {
        const incident = incidentMap.get(incidentId)
        const sorted = [...groupActions].sort((a, b) =>
          (a.timestamp || '').localeCompare(b.timestamp || ''),
        )
        return {
          incidentId,
          machineId:
            incident?.machine_id ||
            groupActions.find((a) => a.machine_id)?.machine_id,
          incident,
          actions: sorted,
        }
      },
    )

    grouped.sort(
      (a, b) =>
        latestTimestamp(b.actions).localeCompare(latestTimestamp(a.actions)),
    )

    if (unassigned.length) {
      grouped.push({
        incidentId: null,
        actions: [...unassigned].sort((a, b) =>
          (a.timestamp || '').localeCompare(b.timestamp || ''),
        ),
      })
    }

    return grouped
  }, [actions, incidents])

  if (error) return <p className="error">{error}</p>

  return (
    <div className="page">
      <section className="hero">
        <h1>Agent activity</h1>
        <p>
          Autonomous steps the maintenance agent took — grouped by incident so
          you can follow each investigation separately.
        </p>
      </section>

      {groups.length === 0 ? (
        <section className="panel">
          <p className="empty muted">
            No agent actions recorded yet. Use &quot;Load demo state&quot; on a
            machine card.
          </p>
        </section>
      ) : (
        groups.map((group) => (
          <section
            key={group.incidentId ?? 'unassigned'}
            className="panel activity-incident-panel"
          >
            <header className="activity-incident-head">
              <div>
                {group.incidentId ? (
                  <h2>
                    <Link to={`/incidents/${group.incidentId}`}>
                      {group.incidentId}
                    </Link>
                  </h2>
                ) : (
                  <h2>Unassigned</h2>
                )}
                <p className="muted activity-incident-meta">
                  {group.machineId ? (
                    <span className="mono">{group.machineId}</span>
                  ) : null}
                  {group.machineId && group.incident ? ' · ' : null}
                  {group.incident?.suspected_failure ||
                    (group.incidentId
                      ? 'Incident activity'
                      : 'Actions without an incident')}
                </p>
              </div>
              <div className="activity-incident-badges">
                {group.incident?.severity ? (
                  <StatusBadge value={group.incident.severity} />
                ) : null}
                {group.incident?.status ? (
                  <StatusBadge value={group.incident.status} />
                ) : null}
              </div>
            </header>
            <Timeline actions={group.actions} />
          </section>
        ))
      )}
    </div>
  )
}
