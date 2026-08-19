import React, { useState, useEffect } from 'react'
import { api } from '../api.js'

const S = {
  page: { padding: 32 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 22, fontWeight: 700, color: '#e2e8f0' },
  card: { background: '#13182a', border: '1px solid #1e2a45', borderRadius: 12, padding: 20, marginBottom: 16 },
  label: { display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 },
  input: { width: '100%', padding: '10px 14px', background: '#0f1117', border: '1px solid #1e2a45', borderRadius: 8, color: '#e2e8f0', fontSize: 13, outline: 'none', marginBottom: 12 },
  btn: { padding: '9px 18px', background: '#2563eb', border: 'none', borderRadius: 8, color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  ghost: { padding: '8px 16px', background: '#1e293b', border: 'none', borderRadius: 8, color: '#94a3b8', fontSize: 13, cursor: 'pointer', margin: '0 8px' },
  row: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 4px', borderBottom: '1px solid #1e2a45' },
  name: { fontSize: 15, fontWeight: 600, color: '#e2e8f0' },
  meta: { fontSize: 12, color: '#64748b', marginTop: 4 },
  badge: (on) => ({ display: 'inline-block', fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 999, background: on ? '#14532d' : '#3f1d1d', color: on ? '#86efac' : '#fca5a5', marginInlineEnd: 8 }),
  msg: { color: '#60a5fa', fontSize: 13, marginTop: 10 },
  err: { color: '#f87171', fontSize: 13, marginTop: 10 },
}

export default function Bots() {
  const [bots, setBots] = useState([])
  const [token, setToken] = useState('')
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  const load = () => api.bots().then(setBots).catch(() => {})
  useEffect(() => { load() }, [])

  const add = async (e) => {
    e.preventDefault()
    setMsg(''); setErr('')
    try {
      await api.addBot({ token })
      setToken('')
      setMsg('توکن ثبت شد. برای فعال‌شدن ربات، سرویس را دوباره deploy کنید.')
      load()
    } catch (ex) { setErr(String(ex.message || ex)) }
  }

  const remove = async (b) => {
    if (!confirm(`ربات ${b.bot_name || b.token_preview} حذف شود؟`)) return
    await api.removeBot(b.id)
    load()
  }

  const toggle = async (b) => {
    await api.toggleBot(b.id)
    load()
  }

  return (
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.title}>🤖 ربات‌ها</div>
      </div>

      <div style={S.card}>
        <label style={S.label}>توکن جدید ربات (از @BotFather — بعد از افزودن، سرویس را دوباره deploy کنید)</label>
        <form onSubmit={add}>
          <input style={S.input} dir="ltr" placeholder="1234567890:AAH..." value={token} onChange={e => setToken(e.target.value)} />
          <button style={S.btn} type="submit">➕ افزودن ربات</button>
        </form>
        {msg && <div style={S.msg}>{msg}</div>}
        {err && <div style={S.err}>{err}</div>}
      </div>

      <div style={S.card}>
        {bots.length === 0 && <div style={{ color: '#64748b', fontSize: 13 }}>هنوز رباتی اضافه نشده است.</div>}
        {bots.map(b => (
          <div key={b.id} style={S.row}>
            <div>
              <div style={S.name}>
                <span style={S.badge(b.is_active)}>{b.is_active ? 'فعال' : 'غیرفعال'}</span>
                {b.bot_name || '—'}{b.bot_username ? ` (@${b.bot_username})` : ''}
              </div>
              <div style={S.meta} className="ltr">{b.token_preview} · اضافه‌شده: {b.added_at ? new Date(b.added_at).toLocaleString('fa-IR') : '—'}</div>
            </div>
            <div>
              <button style={S.ghost} onClick={() => toggle(b)}>{b.is_active ? '⏸ غیرفعال کن' : '▶ فعال کن'}</button>
              <button style={{ ...S.ghost, color: '#fca5a5' }} onClick={() => remove(b)}>🗑 حذف</button>
            </div>
          </div>
        ))}
      </div>
      <div style={{ color: '#64748b', fontSize: 12 }}>
        تغییرات توکن/فعال‌سازی، بعد از هر deploy جدید اعمال می‌شود.
      </div>
    </div>
  )
}