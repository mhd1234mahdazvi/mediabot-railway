import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, NavLink, useNavigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import Users from './pages/Users.jsx'
import Links from './pages/Links.jsx'
import Logs from './pages/Logs.jsx'
import Settings from './pages/Settings.jsx'
import Bots from './pages/Bots.jsx'
import Login from './pages/Login.jsx'

const S = {
  layout: { display: 'flex', minHeight: '100vh' },
  sidebar: { width: 220, background: '#13182a', borderInlineEnd: '1px solid #1e2a45', display: 'flex', flexDirection: 'column', padding: '24px 0' },
  logo: { padding: '0 20px 24px', fontSize: 18, fontWeight: 700, color: '#60a5fa', borderBottom: '1px solid #1e2a45', marginBottom: 16 },
  nav: { display: 'flex', flexDirection: 'column', gap: 4, padding: '0 12px' },
  link: { padding: '10px 12px', borderRadius: 8, color: '#94a3b8', textDecoration: 'none', fontSize: 14, display: 'flex', alignItems: 'center', gap: 10, transition: 'all .15s' },
  activeLink: { background: '#1e3a5f', color: '#60a5fa' },
  main: { flex: 1, overflow: 'auto' },
  logout: { marginTop: 'auto', padding: '0 12px 12px' },
  logoutBtn: { width: '100%', padding: '10px 12px', background: 'none', border: '1px solid #2d3748', borderRadius: 8, color: '#94a3b8', cursor: 'pointer', fontSize: 14 },
}

function Sidebar({ onLogout }) {
  const links = [
    { to: '/', label: '📊 داشبورد', end: true },
    { to: '/users', label: '👥 کاربران' },
    { to: '/links', label: '🔗 تاریخچه لینک‌ها' },
    { to: '/logs', label: '📋 لاگ‌ها' },
    { to: '/bots', label: '🤖 ربات‌ها' },
    { to: '/settings', label: '⚙️ تنظیمات' },
  ]
  return (
    <div style={S.sidebar}>
      <div style={S.logo}>🤖 مدیابوت</div>
      <nav style={S.nav}>
        {links.map(l => (
          <NavLink key={l.to} to={l.to} end={l.end}
            style={({ isActive }) => ({ ...S.link, ...(isActive ? S.activeLink : {}) })}>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div style={S.logout}>
        <button style={S.logoutBtn} onClick={onLogout}>🚪 خروج</button>
      </div>
    </div>
  )
}

function Layout({ onLogout }) {
  return (
    <div style={S.layout}>
      <Sidebar onLogout={onLogout} />
      <main style={S.main}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/users" element={<Users />} />
          <Route path="/links" element={<Links />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/bots" element={<Bots />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  const [authed, setAuthed] = useState(!!localStorage.getItem('token'))

  const logout = () => { localStorage.removeItem('token'); setAuthed(false) }

  if (!authed) return <Login onLogin={() => setAuthed(true)} />

  return (
    <BrowserRouter>
      <Layout onLogout={logout} />
    </BrowserRouter>
  )
}