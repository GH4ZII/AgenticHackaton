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

export function MachineCard({
  machine,
  seeding,
  onSeedDemo,
  onSeedCritical,
}: Props) {
  const running = machine.status !== 'OUT_OF_SERVICE'
  const motion = motionClass(machine.status)

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

        <div className="machine-visual" aria-hidden="true">
          <span
            className={`live-chip ${running ? 'live-chip--on' : 'live-chip--off'}`}
          >
            <span className="live-dot" />
            {running ? 'Running' : 'Stopped'}
          </span>

          <svg
            className="pump-svg"
            viewBox="0 0 240 180"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <linearGradient id="pumpBody" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#1a3a42" />
                <stop offset="100%" stopColor="#0f766e" />
              </linearGradient>
              <linearGradient id="pumpMetal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#c5d4dc" />
                <stop offset="100%" stopColor="#7a8f9c" />
              </linearGradient>
            </defs>

            {/* Base */}
            <rect
              x="48"
              y="148"
              width="144"
              height="12"
              rx="3"
              fill="url(#pumpMetal)"
            />
            <rect x="64" y="138" width="112" height="12" rx="2" fill="#5a6b78" />

            {/* Inlet / outlet pipes */}
            <rect
              className="pump-pipe"
              x="16"
              y="78"
              width="52"
              height="22"
              rx="6"
              fill="url(#pumpMetal)"
            />
            <rect
              className="pump-pipe"
              x="172"
              y="78"
              width="52"
              height="22"
              rx="6"
              fill="url(#pumpMetal)"
            />

            {/* Motor housing */}
            <rect
              className="pump-motor"
              x="88"
              y="36"
              width="64"
              height="48"
              rx="8"
              fill="url(#pumpBody)"
            />
            <rect x="100" y="44" width="40" height="8" rx="2" fill="#5eead4" opacity="0.45" />

            {/* Volute / pump casing */}
            <circle
              className="pump-casing"
              cx="120"
              cy="108"
              r="42"
              fill="url(#pumpBody)"
            />
            <circle cx="120" cy="108" r="28" fill="#0b4f4a" />

            {/* Impeller — outer translate, inner spin (CSS transform must not clobber position) */}
            <g transform="translate(120 108)">
              <g className="pump-impeller">
                <circle r="8" fill="#5eead4" />
                <rect x="-3" y="-22" width="6" height="16" rx="2" fill="#99f6e4" />
                <rect x="-3" y="6" width="6" height="16" rx="2" fill="#99f6e4" />
                <rect x="-22" y="-3" width="16" height="6" rx="2" fill="#99f6e4" />
                <rect x="6" y="-3" width="16" height="6" rx="2" fill="#99f6e4" />
              </g>
            </g>

            {/* Shaft from motor to casing */}
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
        </div>
      </Link>

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
    </article>
  )
}
