export type Machine = {
  machine_id: string
  name: string
  machine_type: string
  manufacturer: string
  model: string
  location: string
  status: string
  temperature_limit: number
  vibration_limit: number
  motor_current_limit: number
  notes?: string | null
}

export type TelemetrySample = {
  machine_id: string
  timestamp: string
  temperature_c: number
  vibration_mm_s: number
  motor_current_a: number
}

export type Incident = {
  incident_id: string
  machine_id: string
  status: string
  severity: string
  suspected_failure?: string | null
  confidence?: number | null
  detected_at: string
  resolved_at?: string | null
  trigger_reason: string
  agent_summary?: string | null
}

export type WorkOrder = {
  work_order_id: string
  machine_id: string
  incident_id?: string | null
  title: string
  description: string
  suspected_failure?: string | null
  priority: string
  recommended_action?: string | null
  required_parts: string[]
  status: string
  created_at: string
  completed_at?: string | null
}

export type InventoryItem = {
  part_id: string
  name: string
  part_number: string
  stock: number
  location: string
}

export type AgentAction = {
  action_id?: string
  timestamp?: string
  machine_id?: string
  incident_id?: string
  action?: string
  detail?: string
}

export type ApprovalRequest = {
  approval_id: string
  incident_id: string
  machine_id: string
  reason: string
  status: string
  created_at: string
  resolved_at?: string | null
  resolved_by?: string | null
}

export type DashboardSummary = {
  total_machines: number
  healthy_machines: number
  attention_machines: number
  open_incidents: number
  active_work_orders: number
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  dashboard: () => request<DashboardSummary>('/api/dashboard'),
  machines: () => request<{ machines: Machine[] }>('/api/machines'),
  machine: (id: string) =>
    request<{
      machine: Machine
      open_incident_id: string | null
      maintenance_history: Array<Record<string, string>>
    }>(`/api/machines/${id}`),
  telemetry: (id: string) =>
    request<{
      machine_id: string
      samples: TelemetrySample[]
      limits: {
        temperature_c: number
        vibration_mm_s: number
        motor_current_a: number
      }
    }>(`/api/machines/${id}/telemetry`),
  incidents: () => request<{ incidents: Incident[] }>('/api/incidents'),
  incident: (id: string) =>
    request<{
      incident: Incident
      work_orders: WorkOrder[]
      agent_actions: AgentAction[]
      inventory: InventoryItem[]
    }>(`/api/incidents/${id}`),
  workOrders: () => request<{ work_orders: WorkOrder[] }>('/api/work-orders'),
  inventory: () => request<{ inventory: InventoryItem[] }>('/api/inventory'),
  agentActions: () =>
    request<{ agent_actions: AgentAction[] }>('/api/agent-actions'),
  seedDemo: () =>
    request<{
      status: string
      incident_id: string
      created_incident: boolean
      created_work_order: boolean
    }>('/api/demo/seed', { method: 'POST' }),
  seedCritical: () =>
    request<{
      status: string
      incident_id: string
      approval_id: string
      approval_status: string
      machine_status: string
      shutdown_executed: boolean
    }>('/api/demo/seed-critical', { method: 'POST' }),
  listApprovals: () =>
    request<{ approvals: ApprovalRequest[]; count: number }>('/api/approvals'),
  pendingApprovals: () =>
    request<{ approvals: ApprovalRequest[]; count: number }>(
      '/api/approvals/pending',
    ),
  approve: (id: string) =>
    request<{
      status: string
      message: string
      approval: ApprovalRequest
      machine: Machine
    }>(`/api/approvals/${id}/approve`, { method: 'POST' }),
  reject: (id: string) =>
    request<{
      status: string
      message: string
      approval: ApprovalRequest
      machine: Machine | null
    }>(`/api/approvals/${id}/reject`, { method: 'POST' }),
  completeWorkOrder: (id: string) =>
    request<{
      status: string
      message: string
      already_completed: boolean
      agent_invoked: boolean
      machine_status: string | null
      work_order: WorkOrder
      incident: Incident | null
      tools_called: string[]
      agent_summary: string | null
    }>(`/api/work-orders/${id}/complete`, { method: 'POST' }),
}
