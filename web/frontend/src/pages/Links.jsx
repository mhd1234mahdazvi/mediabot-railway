import React, { useState, useEffect } from 'react'
import { api } from '../api.js'

const S = {
  page: { padding: 32 },
  title: { fontSize: 22, fontWeight: 700, color: '#e2e8f0', marginBottom: 24 },
  filters: { display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' },
  input: { padding: '8px 12px', background: '#13182a', border: '1px solid #1e2a45', borderRadius: 8, color: '#e2e8f0', fontSize: 14, minWidth: 180 },
  select: { padding: '8px 12px', background: '#13182a', border: '1px solid #1e2a45', borderRadius: 8, color: '#e2e8f0', fontSize: 14 },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { padding: '12px 16px', textAlign: 'right', fontSize: 12, color: '#64748b', fontWeight: 600, borderBottom: '1px solid #1e2a45' },
  td: { padding: '12px 16px', fontSize: 13, color: '#e2e8f0', borderBottom: '1px solid #1a2035', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  badge: (s) => ({
    padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600,
    background: s === 'success' ? '#14532d' : '#7f1d1d',
    color: s === 'success' ? '#86efac' : '#fca5a5',
  }),
  link: { color: '#60a5fa', textDecoration: 'none', fontSize: 12 },
}

export default function Links() {
  const [links, setLinks] = useState([])
  const [search, setSearch] = useState('')
  const [platform, setPlatform] = useState('')
  const [status, setStatus] = useState('')

  const load = () => {
    const p = {}
    if (search) p.search = search
    if (platform) p.platform = platform
    if (status) p.status = status
    api.links(p).then(setLinks).catch(() => {})
  }

  useEffect(() => { load() }, [search, platform, status])

  return (
    <div style={S.page}>
      <div style={S.title}>🔗 تاریخچه لینک‌ها ({links.length})</div>
      <div style={S.filters}>
        <input style={S.input} placeholder="جستجوی لینک، عنوان، کاربر..." value={search} onChange={e => setSearch(e.target.value)} />
        <select style={S.select} value={platform} onChange={e => setPlatform(e.target.value)}>
          <option value="">همه پلتفرم‌ها</option>
          {['youtube','instagram','twitter','tiktok','direct_url'].map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <select style={S.select} value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">همه وضعیت‌ها</option>
          <option value="success">موفق</option>
          <option value="failed">ناموفق</option>
        </select>
      </div>
      <table style={S.table}>
        <thead>
          <tr>{['زمان','کاربر','پلتفرم','عنوان','کیفیت','حجم','وضعیت'].map(h => <th key={h} style={S.th}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {links.map(l => (
            <tr key={l.id}>
              <td style={S.td}><span style={{ color: '#64748b', fontSize: 11 }}>{new Date(l.time).toLocaleString('fa-IR')}</span></td>
              <td style={S.td}>
                <div>{l.display_name || '—'}</div>
                <div style={{ color: '#64748b', fontSize: 11 }}>@{l.username || 'N/A'}</div>
              </td>
              <td style={S.td}><span style={{ color: '#94a3b8' }}>{l.platform}</span></td>
              <td style={{ ...S.td, maxWidth: 200 }} title={l.title}>
                <a href={l.url} target="_blank" rel="noreferrer" style={S.link}>{l.title || l.url}</a>
              </td>
              <td style={S.td}>{l.quality || '—'}</td>
              <td style={S.td}>{l.file_size_mb ? `${l.file_size_mb.toFixed(1)} MB` : '—'}</td>
              <td style={S.td}><span style={S.badge(l.status)}>{l.status === 'success' ? 'موفق' : 'ناموفق'}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}