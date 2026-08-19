import React, { useState, useEffect } from 'react'
import { api } from '../api.js'

const S = {
  page: { padding: 32 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 },
  title: { fontSize: 22, fontWeight: 700, color: '#e2e8f0' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16, marginBottom: 32 },
  card: { background: '#13182a', border: '1px solid #1e2a45', borderRadius: 12, padding: 20 },
  cardLabel: { fontSize: 13, color: '#64748b', marginBottom: 8 },
  cardValue: { fontSize: 28, fontWeight: 700, color: '#60a5fa' },
  platformsTitle: { fontSize: 16, fontWeight: 600, color: '#94a3b8', marginBottom: 16 },
  platformRow: { display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #1e2a45', fontSize: 14, color: '#e2e8f0' },
  pauseBtn: (paused) => ({
    padding: '10px 24px', borderRadius: 8, border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 14,
    background: paused ? '#16a34a' : '#dc2626', color: '#fff',
  }),
  statusDot: (paused) => ({
    display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
    background: paused ? '#ef4444' : '#22c55e', marginRight: 8,
  }),
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [paused, setPaused] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.stats().then(setStats).catch(() => {})
    api.botStatus().then(r => setPaused(r.paused)).catch(() => {})
  }, [])

  const togglePause = async () => {
    setLoading(true)
    try {
      if (paused) { await api.resume(); setPaused(false) }
      else { await api.pause(); setPaused(true) }
    } catch {}
    setLoading(false)
  }

  const cards = stats ? [
    { label: 'کاربران فعال', value: stats.total_users },
    { label: 'کل دانلودها', value: stats.total_downloads },
    { label: 'دانلودهای امروز', value: stats.today_downloads },
    { label: 'ناموفق', value: stats.failed },
    { label: 'حجم کل', value: `${stats.total_volume_gb} GB` },
  ] : []

  return (
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.title}>
          <span style={S.statusDot(paused)} />
          {paused ? 'ربات متوقف شده' : 'ربات در حال اجرا'}
        </div>
        <button style={S.pauseBtn(paused)} onClick={togglePause} disabled={loading}>
          {loading ? '...' : paused ? '▶ ادامه ربات' : '⏸ توقف ربات'}
        </button>
      </div>

      <div style={S.grid}>
        {cards.map(c => (
          <div key={c.label} style={S.card}>
            <div style={S.cardLabel}>{c.label}</div>
            <div style={S.cardValue}>{c.value ?? '—'}</div>
          </div>
        ))}
      </div>

      {stats?.platforms && Object.keys(stats.platforms).length > 0 && (
        <div style={S.card}>
          <div style={S.platformsTitle}>دانلودها بر اساس پلتفرم</div>
          {Object.entries(stats.platforms).map(([p, c]) => (
            <div key={p} style={S.platformRow}>
              <span>{p.charAt(0).toUpperCase() + p.slice(1)}</span>
              <span style={{ color: '#60a5fa', fontWeight: 600 }}>{c}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}