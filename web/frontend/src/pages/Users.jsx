import React, { useState, useEffect } from 'react'
import { api } from '../api.js'

const S = {
  page: { padding: 32 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  title: { fontSize: 22, fontWeight: 700, color: '#e2e8f0' },
  addBtn: { padding: '9px 20px', background: '#2563eb', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontWeight: 600, fontSize: 14 },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { padding: '12px 16px', textAlign: 'right', fontSize: 12, color: '#64748b', fontWeight: 600, borderBottom: '1px solid #1e2a45' },
  td: { padding: '14px 16px', fontSize: 14, color: '#e2e8f0', borderBottom: '1px solid #1a2035' },
  badge: (active, banned) => ({
    padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600,
    background: banned ? '#7f1d1d' : active ? '#14532d' : '#1e293b',
    color: banned ? '#fca5a5' : active ? '#86efac' : '#64748b',
  }),
  actionBtn: (color) => ({ padding: '5px 12px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600, background: color, color: '#fff', marginLeft: 4 }),
  modal: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  modalCard: { background: '#13182a', border: '1px solid #1e2a45', borderRadius: 16, padding: 32, width: 420, maxWidth: '90vw' },
  modalTitle: { fontSize: 18, fontWeight: 700, color: '#e2e8f0', marginBottom: 20 },
  label: { display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6, marginTop: 14 },
  input: { width: '100%', padding: '9px 12px', background: '#0f1117', border: '1px solid #1e2a45', borderRadius: 8, color: '#e2e8f0', fontSize: 14 },
  row: { display: 'flex', gap: 8, marginTop: 20 },
  confirmBtn: { flex: 1, padding: 10, background: '#2563eb', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontWeight: 600 },
  cancelBtn: { flex: 1, padding: 10, background: '#1e293b', border: '1px solid #2d3748', borderRadius: 8, color: '#94a3b8', cursor: 'pointer' },
}

export default function Users() {
  const [users, setUsers] = useState([])
  const [modal, setModal] = useState(null) // 'add' | 'ban' | 'limits'
  const [target, setTarget] = useState(null)
  const [form, setForm] = useState({})

  const load = () => api.users().then(setUsers).catch(() => {})
  useEffect(() => { load() }, [])

  const openModal = (type, user = null) => { setModal(type); setTarget(user); setForm({}) }
  const closeModal = () => { setModal(null); setTarget(null); setForm({}) }
  const f = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }))

  const addUser = async () => {
    await api.addUser({ telegram_id: parseInt(form.id), username: form.username, display_name: form.name })
    load(); closeModal()
  }
  const removeUser = async (u) => { if (confirm(`حذف ${u.display_name}؟`)) { await api.removeUser(u.telegram_id); load() } }
  const banUser = async () => { await api.banUser(target.telegram_id, form.msg || 'دسترسی شما معلق شده است.'); load(); closeModal() }
  const unbanUser = async (u) => { await api.unbanUser(u.telegram_id); load() }
  const setLimits = async () => {
    await api.setLimits(target.telegram_id, {
      max_file_mb: form.file ? parseInt(form.file) : null,
      daily_limit_mb: form.daily ? parseInt(form.daily) : null,
      queue_limit: form.queue ? parseInt(form.queue) : null,
    }); load(); closeModal()
  }

  return (
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.title}>👥 کاربران ({users.length})</div>
        <button style={S.addBtn} onClick={() => openModal('add')}>+ افزودن کاربر</button>
      </div>

      <table style={S.table}>
        <thead>
          <tr>{['کاربر', 'شناسه', 'وضعیت', 'آخرین بازدید', 'عملیات'].map(h => <th key={h} style={S.th}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {users.map(u => (
            <tr key={u.telegram_id}>
              <td style={S.td}>
                <div style={{ fontWeight: 600 }}>{u.display_name || '—'}</div>
                <div style={{ color: '#64748b', fontSize: 12 }}>@{u.username || 'بدون نام کاربری'}</div>
              </td>
              <td style={S.td}><code style={{ color: '#94a3b8', fontSize: 12 }}>{u.telegram_id}</code></td>
              <td style={S.td}><span style={S.badge(u.is_active, u.is_banned)}>{u.is_banned ? 'بن شده' : u.is_active ? 'فعال' : 'غیرفعال'}</span></td>
              <td style={S.td}><span style={{ color: '#64748b', fontSize: 12 }}>{u.last_seen ? new Date(u.last_seen).toLocaleDateString('fa-IR') : 'هرگز'}</span></td>
              <td style={S.td}>
                <button style={S.actionBtn('#1d4ed8')} onClick={() => openModal('limits', u)}>محدودیت‌ها</button>
                {u.is_banned
                  ? <button style={S.actionBtn('#15803d')} onClick={() => unbanUser(u)}>رفع بن</button>
                  : <button style={S.actionBtn('#b45309')} onClick={() => openModal('ban', u)}>بن</button>
                }
                <button style={S.actionBtn('#7f1d1d')} onClick={() => removeUser(u)}>حذف</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {modal === 'add' && (
        <div style={S.modal}>
          <div style={S.modalCard}>
            <div style={S.modalTitle}>افزودن کاربر</div>
            <label style={S.label}>شناسه تلگرام</label>
            <input style={S.input} dir="ltr" placeholder="123456789" onChange={f('id')} />
            <label style={S.label}>نام کاربری (اختیاری)</label>
            <input style={S.input} dir="ltr" placeholder="@username" onChange={f('username')} />
            <label style={S.label}>نام نمایشی (اختیاری)</label>
            <input style={S.input} onChange={f('name')} />
            <div style={S.row}>
              <button style={S.confirmBtn} onClick={addUser}>افزودن</button>
              <button style={S.cancelBtn} onClick={closeModal}>انصراف</button>
            </div>
          </div>
        </div>
      )}

      {modal === 'ban' && (
        <div style={S.modal}>
          <div style={S.modalCard}>
            <div style={S.modalTitle}>بن {target?.display_name}</div>
            <label style={S.label}>پیام به کاربر</label>
            <input style={S.input} placeholder="دسترسی شما معلق شده است." onChange={f('msg')} />
            <div style={S.row}>
              <button style={{ ...S.confirmBtn, background: '#dc2626' }} onClick={banUser}>بن</button>
              <button style={S.cancelBtn} onClick={closeModal}>انصراف</button>
            </div>
          </div>
        </div>
      )}

      {modal === 'limits' && (
        <div style={S.modal}>
          <div style={S.modalCard}>
            <div style={S.modalTitle}>محدودیت‌های {target?.display_name}</div>
            <label style={S.label}>حداکثر حجم فایل (MB) — برای پیش‌فرض خالی بگذارید</label>
            <input style={S.input} type="number" defaultValue={target?.max_file_mb || ''} onChange={f('file')} />
            <label style={S.label}>سقف روزانه (MB) — برای پیش‌فرض خالی بگذارید</label>
            <input style={S.input} type="number" defaultValue={target?.daily_limit_mb || ''} onChange={f('daily')} />
            <label style={S.label}>سقف صف — برای پیش‌فرض خالی بگذارید</label>
            <input style={S.input} type="number" defaultValue={target?.queue_limit || ''} onChange={f('queue')} />
            <div style={S.row}>
              <button style={S.confirmBtn} onClick={setLimits}>ذخیره</button>
              <button style={S.cancelBtn} onClick={closeModal}>انصراف</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}