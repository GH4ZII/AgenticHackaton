import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ActivityPage } from './pages/ActivityPage'
import { ApprovalsPage } from './pages/ApprovalsPage'
import { DashboardPage } from './pages/DashboardPage'
import { IncidentDetailPage } from './pages/IncidentDetailPage'
import { MachineDetailPage } from './pages/MachineDetailPage'
import { WorkOrdersPage } from './pages/WorkOrdersPage'
import './styles/tokens.css'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/approvals" element={<ApprovalsPage />} />
        <Route path="/incidents/:incidentId" element={<IncidentDetailPage />} />
        <Route path="/machines/:machineId" element={<MachineDetailPage />} />
        <Route path="/work-orders" element={<WorkOrdersPage />} />
        <Route path="/activity" element={<ActivityPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
