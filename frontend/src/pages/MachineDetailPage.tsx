import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type Machine, type TelemetrySample } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { TelemetryCharts } from '../components/TelemetryCharts'
import '../styles/pages.css'

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
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.machine(machineId), api.telemetry(machineId)])
      .then(([mach, tel]) => {
        setMachine(mach.machine)
        setOpenIncidentId(mach.open_incident_id)
        setHistory(mach.maintenance_history)
        setSamples(tel.samples)
        setLimits(tel.limits)
      })
      .catch((err: Error) => setError(err.message))
  }, [machineId])

  if (error) return <p className="error">{error}</p>
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
      </section>

      <section className="panel">
        <h2>Telemetry</h2>
        <TelemetryCharts samples={samples} limits={limits} />
      </section>

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
