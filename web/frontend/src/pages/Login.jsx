import React, { useState } from 'react'
import { api } from '../api.js'

const S = {
  wrap: { display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#0f1117' },
  card: { background: '#13182a', border: '1px solid #1e2a45', borderRadius: 16, padding: 40, width: 360 },
  title: { fontSize: 24, fontWeight: 700, color: '#60a5fa', marginBottom: 8, textAlign: 'center' },
  sub: { color: '#64748b', fontSize: 14, textAlign: 'center', marginBottom: 32 },
  label: { display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 },
  input: { width: '100%', padding: '10px 14px', background: '#0f1117', border: '1px solid #1e2a45', borderRadius: 8, color: '#e2e8f0', fontSize: 14, marginBottom: 16, outline: 'none' },
  btn: { width: '100%', padding: '12px', background: '#2563eb', border: 'none', borderRadius: 8, color: '#fff', fontSize: 15, fontWeight: 600, cursor: 'pointer', marginTop: 8 },
  err: { color: '#f87171', fontSize: 13, marginTop: 12, textAlign: 'center' },
}

export default function Login({ onLogin }) {
  const [u, setU] = useState('')
  const [p, setP] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true); setErr('')
    try {
      const { token } = await api.login(u, p)
      localStorage.setItem('token', token)
      onLogin()
    } catch { setErr('نام کاربری یا رمز عبور اشتباه است') }
    setLoading(false)
  }

  return (
    <div style={S.wrap}>
      <div style={S.card}>
        <div style={S.title}>🤖 مدیابوت</div>
        <div style={S.sub}>پنل مدیریت</div>
        <form onSubmit={submit}>
          <label style={S.label}>نام کاربری</label>
          <input style={S.input} value={u} onChange={e => setU(e.target.value)} autoFocus />
          <label style={S.label}>رمز عبور</label>
          <input style={S.input} type="password" value={p} onChange={e => setP(e.target.value)} />
          <button style={S.btn} disabled={loading}>{loading ? 'در حال ورود...' : 'ورود'}</button>
        </form>
        {err && <div style={S.err}>{err}</div>}
      </div>
    </div>
  )
}