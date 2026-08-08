import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import './Layout.css'

type Props = {
  children: ReactNode
  onSeedDemo: () => void
  onSeedCritical: () => void
  seeding?: boolean
  seedMessage?: string | null
}

export function Layout({
  children,
  onSeedDemo,
  onSeedCritical,
  seeding,
  seedMessage,
}: Props) {
  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark">MA</span>
          <span className="brand-text">
            <strong>Maintenance Agent</strong>
            <em>Industrial ops dashboard</em>
          </span>
        </Link>
        <nav className="nav">
          <Link to="/">Fleet</Link>
          <Link to="/approvals">Approvals</Link>
          <Link to="/activity">Activity</Link>
          <Link to="/work-orders">Work orders</Link>
          <Link to="/machines/PUMP-04">PUMP-04</Link>
        </nav>
        <div className="seed-actions">
          <button
            className="seed-btn seed-btn-ghost"
            type="button"
            onClick={onSeedCritical}
            disabled={seeding}
          >
            {seeding ? 'Loading…' : 'Load critical demo'}
          </button>
          <button
            className="seed-btn"
            type="button"
            onClick={onSeedDemo}
            disabled={seeding}
          >
            {seeding ? 'Loading…' : 'Load demo state'}
          </button>
        </div>
      </header>
      {seedMessage ? <p className="seed-msg mono">{seedMessage}</p> : null}
      <main className="main">{children}</main>
    </div>
  )
}
