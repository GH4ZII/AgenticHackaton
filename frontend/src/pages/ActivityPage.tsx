import { useEffect, useState } from 'react'
import { api, type AgentAction } from '../api/client'
import { Timeline } from '../components/Timeline'
import '../styles/pages.css'

export function ActivityPage() {
  const [actions, setActions] = useState<AgentAction[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .agentActions()
      .then((data) => setActions([...data.agent_actions].reverse()))
      .catch((err: Error) => setError(err.message))
  }, [])

  if (error) return <p className="error">{error}</p>

  return (
    <div className="page">
      <section className="hero">
        <h1>Agent activity</h1>
        <p>
          Autonomous steps the maintenance agent took — detection, tools, work
          orders, and notifications.
        </p>
      </section>
      <section className="panel">
        <Timeline actions={actions} />
      </section>
    </div>
  )
}
