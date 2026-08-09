import { Link } from 'react-router-dom'
import type { Machine } from '../api/client'
import { StatusBadge } from './StatusBadge'
import './MachineCard.css'

type Props = {
  machine: Machine
  seeding?: boolean
  onSeedDemo: () => void
  onSeedCritical: () => void
}

function motionClass(status: string): string {
  if (status === 'OUT_OF_SERVICE') return 'stopped'
  if (
    status === 'WARNING' ||
    status === 'MAINTENANCE_REQUIRED' ||
    status === 'MONITORING'
  ) {
    return 'stressed'
  }
  return 'running'
}

function MachineIllustration({ machine }: { machine: Machine }) {
  const id = machine.machine_id.replace(/[^a-zA-Z0-9]/g, '')
  const body = `body-${id}`
  const metal = `metal-${id}`
  const type = machine.machine_type

  const defs = (
    <defs>
      <linearGradient id={body} x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#1a3a42" />
        <stop offset="100%" stopColor="#0f766e" />
      </linearGradient>
      <linearGradient id={metal} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#c5d4dc" />
        <stop offset="100%" stopColor="#7a8f9c" />
      </linearGradient>
    </defs>
  )

  if (type === 'cnc_mill') {
    return (
      <svg className="machine-svg" viewBox="0 0 240 180" aria-hidden="true">
        {defs}
        <rect x="40" y="148" width="160" height="12" rx="3" fill={`url(#${metal})`} />
        <rect
          className="pump-motor"
          x="48"
          y="48"
          width="144"
          height="100"
          rx="8"
          fill={`url(#${body})`}
        />
        <rect x="64" y="64" width="72" height="56" rx="4" fill="#0b4f4a" />
        <rect
          className="pump-shaft"
          x="148"
          y="72"
          width="28"
          height="40"
          rx="3"
          fill={`url(#${metal})`}
        />
        <g transform="translate(162 92)">
          <g className="pump-impeller">
            <circle r="10" fill="#5eead4" />
            <rect x="-2" y="-18" width="4" height="12" rx="1" fill="#99f6e4" />
            <rect x="-2" y="6" width="4" height="12" rx="1" fill="#99f6e4" />
          </g>
        </g>
        <rect x="72" y="36" width="48" height="14" rx="3" fill={`url(#${metal})`} />
      </svg>
    )
  }

  if (type === 'industrial_fan') {
    return (
      <svg className="machine-svg" viewBox="0 0 240 180" aria-hidden="true">
        {defs}
        <rect x="96" y="140" width="48" height="16" rx="3" fill={`url(#${metal})`} />
        <rect
          className="pump-shaft"
          x="112"
          y="108"
          width="16"
          height="36"
          rx="3"
          fill="#94a3b8"
        />
        <circle className="pump-casing" cx="120" cy="78" r="48" fill={`url(#${body})`} />
        <circle cx="120" cy="78" r="30" fill="#0b4f4a" />
        <g transform="translate(120 78)">
          <g className="pump-impeller">
            <ellipse cx="0" cy="-20" rx="10" ry="18" fill="#99f6e4" />
            <ellipse cx="0" cy="20" rx="10" ry="18" fill="#99f6e4" />
            <ellipse cx="-20" cy="0" rx="18" ry="10" fill="#5eead4" />
            <ellipse cx="20" cy="0" rx="18" ry="10" fill="#5eead4" />
            <circle r="8" fill="#99f6e4" />
          </g>
        </g>
      </svg>
    )
  }

  if (type === 'conveyor') {
    return (
      <svg className="machine-svg" viewBox="0 0 240 180" aria-hidden="true">
        {defs}
        <rect x="28" y="88" width="184" height="28" rx="10" fill={`url(#${body})`} />
        <rect x="40" y="96" width="160" height="12" rx="4" fill="#0b4f4a" />
        <g transform="translate(48 102)">
          <g className="pump-impeller">
            <circle r="14" fill={`url(#${metal})`} />
            <circle r="5" fill="#5eead4" />
          </g>
        </g>
        <g transform="translate(192 102)">
          <g className="pump-impeller">
            <circle r="14" fill={`url(#${metal})`} />
            <circle r="5" fill="#5eead4" />
          </g>
        </g>
        <rect
          className="pump-motor"
          x="100"
          y="52"
          width="40"
          height="28"
          rx="6"
          fill={`url(#${metal})`}
        />
        <rect className="pump-shaft" x="116" y="78" width="8" height="12" fill="#94a3b8" />
        <rect x="36" y="128" width="16" height="24" rx="2" fill="#5a6b78" />
        <rect x="188" y="128" width="16" height="24" rx="2" fill="#5a6b78" />
      </svg>
    )
  }

  // Default: centrifugal pump
  return (
    <svg className="machine-svg" viewBox="0 0 240 180" aria-hidden="true">
      {defs}
      <rect x="48" y="148" width="144" height="12" rx="3" fill={`url(#${metal})`} />
      <rect x="64" y="138" width="112" height="12" rx="2" fill="#5a6b78" />
      <rect
        className="pump-pipe"
        x="16"
        y="78"
        width="52"
        height="22"
        rx="6"
        fill={`url(#${metal})`}
      />
      <rect
        className="pump-pipe"
        x="172"
        y="78"
        width="52"
        height="22"
        rx="6"
        fill={`url(#${metal})`}
      />
      <rect
        className="pump-motor"
        x="88"
        y="36"
        width="64"
        height="48"
        rx="8"
        fill={`url(#${body})`}
      />
      <rect x="100" y="44" width="40" height="8" rx="2" fill="#5eead4" opacity="0.45" />
      <circle className="pump-casing" cx="120" cy="108" r="42" fill={`url(#${body})`} />
      <circle cx="120" cy="108" r="28" fill="#0b4f4a" />
      <g transform="translate(120 108)">
        <g className="pump-impeller">
          <circle r="8" fill="#5eead4" />
          <rect x="-3" y="-22" width="6" height="16" rx="2" fill="#99f6e4" />
          <rect x="-3" y="6" width="6" height="16" rx="2" fill="#99f6e4" />
          <rect x="-22" y="-3" width="16" height="6" rx="2" fill="#99f6e4" />
          <rect x="6" y="-3" width="16" height="6" rx="2" fill="#99f6e4" />
        </g>
      </g>
      <rect
        className="pump-shaft"
        x="114"
        y="84"
        width="12"
        height="24"
        rx="2"
        fill="#94a3b8"
      />
    </svg>
  )
}

export function MachineCard({
  machine,
  seeding,
  onSeedDemo,
  onSeedCritical,
}: Props) {
  const running = machine.status !== 'OUT_OF_SERVICE'
  const motion = motionClass(machine.status)
  const showDemo = machine.machine_id === 'PUMP-04'

  return (
    <article className={`machine-card machine-card--${motion}`}>
      <Link
        to={`/machines/${machine.machine_id}`}
        className="machine-card-main"
      >
        <header className="machine-card-header">
          <div>
            <h3 className="mono">{machine.machine_id}</h3>
            <p className="machine-card-name">{machine.name}</p>
            <p className="muted machine-card-loc">{machine.location}</p>
          </div>
          <StatusBadge value={machine.status} />
        </header>

        <div className="machine-visual">
          <span
            className={`live-chip ${running ? 'live-chip--on' : 'live-chip--off'}`}
          >
            <span className="live-dot" />
            {running ? 'Running' : 'Stopped'}
          </span>
          <MachineIllustration machine={machine} />
        </div>
      </Link>

      {showDemo ? (
        <div className="machine-card-actions">
          <button
            type="button"
            className="seed-btn seed-btn-ghost"
            onClick={onSeedCritical}
            disabled={seeding}
          >
            {seeding ? 'Loading…' : 'Load critical demo'}
          </button>
          <button
            type="button"
            className="seed-btn"
            onClick={onSeedDemo}
            disabled={seeding}
          >
            {seeding ? 'Loading…' : 'Load demo state'}
          </button>
        </div>
      ) : null}
    </article>
  )
}
