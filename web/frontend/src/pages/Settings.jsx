import React, { useState, useEffect } from 'react'
import { api } from '../api.js'

const S = {
  page: { padding: 32 },
  title: { fontSize: 22, fontWeight: 700, color: '#e2e8f0', marginBottom: 32 },
  section: { marginBottom: 32 },
  sectionTitle: { fontSize: 16, fontWeight: 600, color: '#94a3b8', marginBottom: 16 },
  card: { background: '#13182a', border: '1px solid #1e2a45', borderRadius: 12, padding: 20 },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid #1a2035' },
  rowLast: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0' },
  platformName: { fontSize: 14, color: '#e2e8f0', textTransform: 'capitalize' },
  toggle: (on) => ({
    width: 44, height: 24, borderRadius: 12, background: on ? '#2563eb' : '#374151',
    position: 'relative', cursor: 'pointer', border: 'none', transition: 'background .2s',
  }),
  toggleDot: (on) => ({
    position: 'absolute', top: 3, left: on ? 23 : 3, width: 18, height: 18,
    borderRadius: '50%', background: '#fff', transition: 'left .2s',
  }),
  label: { fontSize: 13, color: '#94a3b8', marginBottom: 6, marginTop: 14, display: 'block' },
  input: { width: '100%', padding: '9px 12px', background: '#0f1117', border: '1px solid #1e2a45', borderRadius: 8, color: '#e2e8f0', fontSize: 14 },
  saveBtn: { marginTop: 20, padding: '10px 24px', background: '#2563eb', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontWeight: 600, fontSize: 14 },
  saved: { color: '#86efac', fontSize: 13, marginRight: 12 },
}

function Toggle({ on, onClick }) {
  return (
    <button style={S.toggle(on)} onClick={onClick}>
      <div style={S.toggleDot(on)} />
    </button>
  )
}

export default function Settings() {
  const [platforms, setPlatforms] = useState({})
  const [defaults, setDefaults] = useState({})
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.platforms().then(setPlatforms).catch(() => {})
    api.getDefaults().then(setDefaults).catch(() => {})
  }, [])

  const togglePlatform = async (name) => {
    const res = await api.togglePlatform(name)
    setPlatforms(p => ({ ...p, [name]: res.enabled }))
  }

  const saveDefaults = async () => {
    await api.setDefaults({
      default_max_file_mb: parseInt(defaults.default_max_file_mb),
      default_daily_limit_mb: parseInt(defaults.default_daily_limit_mb),
      default_queue_limit: parseInt(defaults.default_queue_limit),
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const entries = Object.entries(platforms)

  return (
    <div style={S.page}>
      <div style={S.title}>⚙️ تنظیمات</div>

      <div style={S.section}>
        <div style={S.sectionTitle}>فعال/غیرفعال‌سازی پلتفرم‌ها</div>
        <div style={S.card}>
          {entries.map(([name, enabled], i) => (
            <div key={name} style={i === entries.length - 1 ? S.rowLast : S.row}>
              <span style={S.platformName}>{name.replace('_', ' ')}</span>
              <Toggle on={enabled} onClick={() => togglePlatform(name)} />
            </div>
          ))}
        </div>
      </div>

      <div style={S.section}>
        <div style={S.sectionTitle}>محدودیت‌های پیش‌فرض (برای همه کاربران بدون محدودیت اختصاصی)</div>
        <div style={S.card}>
          <label style={S.label}>حداکثر حجم فایل (MB)</label>
          <input style={S.input} type="number" value={defaults.default_max_file_mb || ''}
            onChange={e => setDefaults(p => ({ ...p, default_max_file_mb: e.target.value }))} />
          <label style={S.label}>سقف دانلود روزانه (MB)</label>
          <input style={S.input} type="number" value={defaults.default_daily_limit_mb || ''}
            onChange={e => setDefaults(p => ({ ...p, default_daily_limit_mb: e.target.value }))} />
          <label style={S.label}>سقف صف (برای هر کاربر)</label>
          <input style={S.input} type="number" value={defaults.default_queue_limit || ''}
            onChange={e => setDefaults(p => ({ ...p, default_queue_limit: e.target.value }))} />
          <div>
            <button style={S.saveBtn} onClick={saveDefaults}>ذخیره پیش‌فرض‌ها</button>
            {saved && <span style={S.saved}>✓ ذخیره شد</span>}
          </div>
        </div>
      </div>
    </div>
  )
}