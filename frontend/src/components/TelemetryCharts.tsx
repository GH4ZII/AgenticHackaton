import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TelemetrySample } from '../api/client'
import './TelemetryCharts.css'

type Props = {
  samples: TelemetrySample[]
  limits: {
    temperature_c: number
    vibration_mm_s: number
    motor_current_a: number
  }
}

function shortTime(value: string) {
  try {
    return new Date(value).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return value
  }
}

export function TelemetryCharts({ samples, limits }: Props) {
  const data = samples.map((s) => ({
    ...s,
    label: shortTime(s.timestamp),
  }))

  if (!data.length) {
    return <p className="empty">No telemetry samples yet.</p>
  }

  return (
    <div className="charts">
      <ChartBlock
        title="Temperature (°C)"
        data={data}
        dataKey="temperature_c"
        limit={limits.temperature_c}
        color="#0f766e"
      />
      <ChartBlock
        title="Vibration (mm/s)"
        data={data}
        dataKey="vibration_mm_s"
        limit={limits.vibration_mm_s}
        color="#b45309"
      />
      <ChartBlock
        title="Motor current (A)"
        data={data}
        dataKey="motor_current_a"
        limit={limits.motor_current_a}
        color="#1d4ed8"
      />
    </div>
  )
}

function ChartBlock({
  title,
  data,
  dataKey,
  limit,
  color,
}: {
  title: string
  data: Array<Record<string, string | number>>
  dataKey: string
  limit: number
  color: string
}) {
  return (
    <section className="chart-panel">
      <header>
        <h3>{title}</h3>
        <span className="mono">limit {limit}</span>
      </header>
      <div className="chart-frame">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(20,33,43,0.08)" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} width={36} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey={dataKey}
              name="value"
              stroke={color}
              strokeWidth={2.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
