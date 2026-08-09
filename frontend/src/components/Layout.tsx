import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import './Layout.css'

type Props = {
  children: ReactNode
}

export function Layout({ children }: Props) {
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
      </header>
      <main className="main">{children}</main>
    </div>
  )
}
