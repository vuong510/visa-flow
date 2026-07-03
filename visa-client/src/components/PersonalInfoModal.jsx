import { useState, useRef } from 'react'
import { useApp } from '../context/AppContext'

const FIELDS = [
  { key: 'family_name',         label: 'Họ (chữ in hoa Latin)',       placeholder: 'VD: NGUYEN',        required: true },
  { key: 'given_name',          label: 'Tên (chữ in hoa Latin)',       placeholder: 'VD: VAN A',          required: true },
  { key: 'date_of_birth',       label: 'Ngày sinh',                    placeholder: 'YYYY-MM-DD',         required: true, type: 'date' },
  { key: 'place_of_birth',      label: 'Nơi sinh',                     placeholder: 'VD: Ha Noi',         required: false },
  { key: 'id_number',           label: 'Số CCCD',                      placeholder: '12 chữ số',          required: false },
  { key: 'passport_number',     label: 'Số hộ chiếu',                  placeholder: 'VD: B1234567',       required: true },
  { key: 'passport_issue_date', label: 'Ngày cấp hộ chiếu',            placeholder: 'YYYY-MM-DD',         required: false, type: 'date' },
  { key: 'home_address',        label: 'Địa chỉ thường trú (tiếng Anh)', placeholder: 'VD: 123 Tran Hung Dao, Hanoi', required: false },
  { key: 'mobile',              label: 'Số điện thoại',                placeholder: '0912345678',         required: false },
  { key: 'email',               label: 'Email',                        placeholder: 'abc@gmail.com',      required: false, type: 'email' },
  { key: 'company_name',        label: 'Tên công ty (tiếng Anh)',      placeholder: 'VD: ABC Company Ltd', required: false },
  { key: 'company_address',     label: 'Địa chỉ công ty (tiếng Anh)', placeholder: '',                   required: false },
  { key: 'accommodation',       label: 'Tên khách sạn tại Nhật',       placeholder: 'VD: APA Hotel Shinjuku', required: false },
  { key: 'accommodation_address', label: 'Địa chỉ khách sạn',         placeholder: 'VD: 1-2-3 Shinjuku, Tokyo', required: false },
  { key: 'accommodation_phone', label: 'SĐT khách sạn',               placeholder: 'VD: +81-3-1234-5678', required: false },
]

const GENDER_OPTIONS = [
  { value: 'male', label: 'Nam' },
  { value: 'female', label: 'Nữ' },
]

const MARITAL_OPTIONS = [
  { value: 'single', label: 'Độc thân' },
  { value: 'married', label: 'Đã kết hôn' },
  { value: 'divorced', label: 'Ly hôn' },
  { value: 'widowed', label: 'Góa' },
]

const inputStyle = {
  width: '100%',
  border: '1px solid #d1d5db',
  borderRadius: 8,
  padding: '9px 12px',
  fontSize: 14,
  outline: 'none',
  background: '#fff',
  boxSizing: 'border-box',
}

const labelStyle = {
  fontSize: 12,
  fontWeight: 600,
  color: '#374151',
  marginBottom: 4,
  display: 'block',
}

export default function PersonalInfoModal({ onSubmit, onClose, loading, initialValues = {} }) {
  const { API_BASE } = useApp()
  const cccdRef = useRef(null)
  const passportRef = useRef(null)
  const [extracting, setExtracting] = useState(null) // 'cccd' | 'passport' | null
  const [extractMsg, setExtractMsg] = useState(
    Object.keys(initialValues).length > 0 ? 'Đã điền sẵn từ hộ chiếu đã tải lên. Kiểm tra lại trước khi tải.' : ''
  )

  const [form, setForm] = useState({
    family_name: '', given_name: '', date_of_birth: '', place_of_birth: '',
    id_number: '', passport_number: '', passport_issue_date: '',
    gender: 'male', marital_status: 'single',
    home_address: '', mobile: '', email: '',
    company_name: '', company_address: '',
    accommodation: '', accommodation_address: '', accommodation_phone: '',
    ...initialValues,
  })
  const [errors, setErrors] = useState({})

  async function handleExtract(docType, file) {
    if (!file) return
    setExtracting(docType)
    setExtractMsg('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('doc_type', docType)
      const res = await fetch(`${API_BASE}/api/extract-id`, { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setExtractMsg(err.detail || 'Không thể đọc ảnh. Thử lại.')
        return
      }
      const data = await res.json()
      // Merge extracted fields into form, skip empty values
      setForm(f => ({ ...f, ...Object.fromEntries(Object.entries(data).filter(([, v]) => v)) }))
      setExtractMsg(`Đã đọc được thông tin từ ${docType === 'cccd' ? 'CCCD' : 'hộ chiếu'}. Kiểm tra lại trước khi tải.`)
    } catch {
      setExtractMsg('Lỗi kết nối. Vui lòng thử lại.')
    } finally {
      setExtracting(null)
    }
  }

  function set(key, val) {
    setForm(f => ({ ...f, [key]: val }))
    setErrors(e => ({ ...e, [key]: undefined }))
  }

  function validate() {
    const errs = {}
    FIELDS.filter(f => f.required).forEach(f => {
      if (!form[f.key]?.trim()) errs[f.key] = 'Bắt buộc'
    })
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  function handleSubmit() {
    if (!validate()) return
    onSubmit(form)
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 50,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'flex-end',
      justifyContent: 'center',
    }}>
      <div style={{
        background: '#fff',
        borderRadius: '20px 20px 0 0',
        width: '100%',
        maxWidth: 480,
        maxHeight: '92dvh',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Header */}
        <div style={{ padding: '16px 20px 12px', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <p style={{ fontWeight: 700, fontSize: 16 }}>Thông tin cá nhân</p>
            <p style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>Điền để điền sẵn vào form MOFA</p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#6b7280', padding: 4 }}>✕</button>
        </div>

        {/* Body */}
        <div style={{ overflowY: 'auto', padding: '16px 20px', flex: 1 }}>
          {/* Auto-fill from ID scan */}
        <div style={{ marginBottom: 18 }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 8 }}>
            Tự động điền từ ảnh giấy tờ
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            {[
              { type: 'cccd', label: 'CCCD', ref: cccdRef },
              { type: 'passport', label: 'Hộ chiếu', ref: passportRef },
            ].map(({ type, label, ref }) => (
              <button
                key={type}
                onClick={() => ref.current.click()}
                disabled={!!extracting}
                style={{
                  flex: 1, padding: '10px 0',
                  border: '1.5px dashed #93c5fd',
                  borderRadius: 10, background: '#eff6ff',
                  color: '#1d4ed8', fontSize: 13, fontWeight: 600,
                  cursor: extracting ? 'not-allowed' : 'pointer',
                  opacity: extracting && extracting !== type ? 0.5 : 1,
                }}
              >
                {extracting === type ? 'Đang đọc...' : `📷 ${label}`}
              </button>
            ))}
          </div>
          {extractMsg && (
            <p style={{ fontSize: 12, marginTop: 8, color: extractMsg.startsWith('Đã') ? '#065f46' : '#b91c1c', lineHeight: 1.4, background: extractMsg.startsWith('Đã') ? '#d1fae5' : '#fee2e2', borderRadius: 8, padding: '8px 10px' }}>
              {extractMsg}
            </p>
          )}
          <input ref={cccdRef} type="file" accept="image/*" style={{ display: 'none' }}
            onChange={e => handleExtract('cccd', e.target.files[0])} />
          <input ref={passportRef} type="file" accept="image/*" style={{ display: 'none' }}
            onChange={e => handleExtract('passport', e.target.files[0])} />
        </div>

        {/* Gender & Marital in one row */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>Giới tính</label>
              <select value={form.gender} onChange={e => set('gender', e.target.value)} style={{ ...inputStyle }}>
                {GENDER_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>Tình trạng hôn nhân</label>
              <select value={form.marital_status} onChange={e => set('marital_status', e.target.value)} style={{ ...inputStyle }}>
                {MARITAL_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>

          {FIELDS.map(f => (
            <div key={f.key} style={{ marginBottom: 14 }}>
              <label style={labelStyle}>
                {f.label}
                {f.required && <span style={{ color: '#ef4444' }}> *</span>}
              </label>
              <input
                type={f.type || 'text'}
                value={form[f.key]}
                onChange={e => set(f.key, e.target.value)}
                placeholder={f.placeholder}
                style={{ ...inputStyle, borderColor: errors[f.key] ? '#ef4444' : '#d1d5db' }}
              />
              {errors[f.key] && <p style={{ fontSize: 11, color: '#ef4444', marginTop: 3 }}>{errors[f.key]}</p>}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{ padding: '12px 20px 20px', borderTop: '1px solid #f3f4f6' }}>
          <button
            onClick={handleSubmit}
            disabled={loading}
            style={{
              width: '100%', height: 52,
              background: loading ? '#93c5fd' : '#2563eb',
              color: '#fff', border: 'none',
              borderRadius: 12, fontSize: 16, fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Đang tạo PDF...' : 'Tạo và tải xuống'}
          </button>
        </div>
      </div>
    </div>
  )
}
