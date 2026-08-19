import React, { useState, useEffect, useRef } from 'react'
import { api } from '../api.js'

const COLORS = { ERROR: '#f87171', WARNING: '#fbbf24', INFO: '#60a5fa', DEBUG: '#94a3b8' }

const S = {
  page: { padding: 32 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 22, fontWeight: 700, color: '#e2e8f0' },
  controls: { display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' },
  select: { padding: '7px 12px', background: '#13182a', border: '1px solid #1e2a45', borderRadius: 8, color: '#e2e8f0', fontSize: 13 },
  input: { padding: '7px 12px', background: '#13182a', border: '1px solid #1e2a45', borderRadius: 8, color: '#e2e8f0', fontSize: 13, width: 200 },
  clearBtn: { padding: '7px 16px', background: '#7f1d1d', border: 'none', borderRadius: 8, color: '#fca5a5', cursor: 'pointer', fontSize: 13 },
  liveBtn: (on) => ({ padding: '7px 16px', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 13, fontWeight: 600, background: on ? '#14532d' : '#1e293b', color: on ? '#86efac' : '#94a3b8' }),
  terminal: { background: '#0a0d14', border: '1px solid #1e2a45', borderRadius: 12, padding: 20, height: 'calc(100vh - 200px)', overflowY: 'auto', fontFamily: 'monospace', fontSize: 12 },
  line: { padding: '3px 0', lineHeight: 1.6, borderBottom: '1px solid #0f1420', whiteSpace: 'pre-wrap', wordBreak: 'break-all' },
  ts: { color: '#334155', marginRight: 8 },
  level: (l) => ({ color: COLORS[l] || '#94a3b8', marginRight: 8, fontWeight: 700, minWidth: 50, display: 'inline-block' }),
  dot: (on) => ({ width: 8, height: 8, borderRadius: '50%', background: on ? '#22c55e' : '#64748b', display: 'inline-block', marginRight: 6 }),
  tb: { background: '#120d18', color: '#f0abfc', padding: '10px 12px', borderRadius: 8, marginTop: 6, fontSize: 11, whiteSpace: 'pre-wrap', direction: 'ltr', textAlign: 'left' },
  expandBtn: { background: 'none', border: 'none', color: '#818cf8', cursor: 'pointer', fontSize: 11, padding: 0 },
}

export default function Logs() {
  const [logs, setLogs] = useState([])
  const [level, setLevel] = useState('')
  const [search, setSearch] = useState('')
  const [live, setLive] = useState(true)
  const [wsOk, setWsOk] = useState(false)
  const [expanded, setExpanded] = useState({})
  const endRef = useRef(null)
  const wsRef = useRef(null)

  const load = () => {
    const p = {}
    if (level) p.level = level
    if (search) p.search = search
    api.logs(p).then(r => setLogs(r.reverse())).catch(() => {})
  }

  useEffect(() => { load() }, [level, search])

  useEffect(() => {
    if (!live) { wsRef.current?.close(); setWsOk(false); return }
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${location.host}/api/logs/ws`)
    wsRef.current = ws
    ws.onopen = () => { ws.send(localStorage.getItem('token') || ''); setWsOk(true) }
    ws.onmessage = (e) => {
      try {
        const entry = JSON.parse(e.data)
        setLogs(prev => [...prev.slice(-999), entry])
      } catch {}
    }
    ws.onclose = () => setWsOk(false)
    return () => ws.close()
  }, [live])

  useEffect(() => { if (live) endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [logs, live])

  const clearLogs = async () => { if (confirm('همه لاگ‌ها پاک شوند؟')) { await api.clearLogs(); setLogs([]) } }

  const toggleTb = (i) => setExpanded(p => ({ ...p, [i]: !p[i] }))

  const fmt = (entry) => {
    const ts = entry.time ? new Date(entry.time * 1000).toLocaleTimeString() : ''
    return { ts, level: entry.level || 'INFO', msg: entry.message || '' }
  }

  return (
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.title}>
          📋 لاگ‌ها
          {live && <span style={{ marginLeft: 12, fontSize: 13, fontWeight: 400 }}><span style={S.dot(wsOk)} />{wsOk ? 'زنده' : 'در حال اتصال...'}</span>}
        </div>
        <div style={S.controls}>
          <input style={S.input} placeholder="جستجو..." value={search} onChange={e => setSearch(e.target.value)} />
          <select style={S.select} value={level} onChange={e => setLevel(e.target.value)}>
            <option value="">همه سطوح</option>
            {['INFO','WARNING','ERROR','DEBUG'].map(l => <option key={l} value={l}>{l}</option>)}
          </select>
          <button style={S.liveBtn(live)} onClick={() => setLive(p => !p)}>{live ? '🔴 زنده' : '⚫ آفلاین'}</button>
          <button style={S.clearBtn} onClick={clearLogs}>پاک کردن</button>
        </div>
      </div>
      <div style={S.terminal}>
        {logs.map((entry, i) => {
          const { ts, level: lv, msg } = fmt(entry)
          const hasTb = !!entry.traceback
          return (
            <div key={i} style={S.line}>
              <span style={S.ts}>{ts}</span>
              <span style={S.level(lv)}>{lv}</span>
              <span style={{ color: '#cbd5e1' }}>{msg}</span>
              {hasTb && (
                <div>
                  {expanded[i]
                    ? <pre style={S.tb}>{entry.traceback}</pre>
                    : <button style={S.expandBtn} onClick={() => toggleTb(i)}>نمایش خطای کامل (traceback)</button>}
                </div>
              )}
            </div>
          )
        })}
        <div ref={endRef} />
      </div>
    </div>
  )
}