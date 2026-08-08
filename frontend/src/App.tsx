import { useCallback, useState } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { api } from './api/client'
import { Layout } from './components/Layout'
import { ActivityPage } from './pages/ActivityPage'
import { DashboardPage } from './pages/DashboardPage'
import { IncidentDetailPage } from './pages/IncidentDetailPage'
import { MachineDetailPage } from './pages/MachineDetailPage'
import { WorkOrdersPage } from './pages/WorkOrdersPage'
import './styles/tokens.css'

export default function App() {
  const navigate = useNavigate()
  const [seeding, setSeeding] = useState(false)
  const [seedMessage, setSeedMessage] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

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
      setRefreshKey((k) => k + 1)
      navigate(`/incidents/${result.incident_id}`)
    } catch (err) {
      setSeedMessage(
        err instanceof Error ? err.message : 'Failed to load demo state',
      )
    } finally {
      setSeeding(false)
    }
  }, [navigate])

  return (
    <Layout onSeedDemo={onSeedDemo} seeding={seeding} seedMessage={seedMessage}>
      <Routes key={refreshKey}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/incidents/:incidentId" element={<IncidentDetailPage />} />
        <Route path="/machines/:machineId" element={<MachineDetailPage />} />
        <Route path="/work-orders" element={<WorkOrdersPage />} />
        <Route path="/activity" element={<ActivityPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
