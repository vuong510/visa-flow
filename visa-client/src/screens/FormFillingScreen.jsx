import { useState, useRef } from 'react'
import NavHeader from '../components/NavHeader'
import ProgressBar from '../components/ProgressBar'
import BottomActionArea from '../components/BottomActionArea'
import CTAButton from '../components/CTAButton'
import OptionButton from '../components/OptionButton'
import { useApp } from '../context/AppContext'

// ─── shared inline styles ───────────────────────────────────────────────────
const inputStyle = {
  width: '100%',
  border: '1px solid var(--color-border)',
  borderRadius: 8,
  padding: '9px 12px',
  fontSize: 14,
  outline: 'none',
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
  boxSizing: 'border-box',
}

const labelStyle = {
  fontSize: 12,
  fontWeight: 600,
  color: 'var(--color-text-primary)',
  marginBottom: 4,
  display: 'block',
}

const cardStyle = {
  background: 'var(--color-surface)',
  borderRadius: 'var(--radius-card)',
  padding: 20,
  boxShadow: 'var(--shadow-card)',
  marginBottom: 16,
}

// ─── Step 1 — Personal info ──────────────────────────────────────────────────
const PERSONAL_FIELDS = [
  { key: 'family_name',          label: 'Họ (chữ in hoa Latin)',          placeholder: 'VD: NGUYEN',            required: true },
  { key: 'given_name',           label: 'Tên (chữ in hoa Latin)',          placeholder: 'VD: VAN A',             required: true },
  { key: 'middle_name',          label: 'Tên đệm',                         placeholder: '',                      required: false },
  { key: 'date_of_birth',        label: 'Ngày sinh',                       placeholder: 'DD/MM/YYYY',            required: true },
  { key: 'gender',               label: 'Giới tính',                       placeholder: '',                      required: false, isSelect: true,
    options: [{ value: '', label: '— Chọn —' }, { value: 'male', label: 'Nam' }, { value: 'female', label: 'Nữ' }] },
  { key: 'marital_status',       label: 'Tình trạng hôn nhân',             placeholder: '',                      required: false, isSelect: true,
    options: [{ value: '', label: '— Chọn —' }, { value: 'single', label: 'Độc thân' }, { value: 'married', label: 'Đã kết hôn' }, { value: 'divorced', label: 'Ly hôn' }, { value: 'widowed', label: 'Góa' }] },
  { key: 'nationality',          label: 'Quốc tịch',                       placeholder: 'VD: Vietnamese',        required: false },
  { key: 'birth_place',          label: 'Nơi sinh',                        placeholder: 'VD: Ha Noi',            required: false },
  { key: 'permanent_address',    label: 'Địa chỉ thường trú (tiếng Anh)', placeholder: 'VD: 123 Tran Hung Dao, Hanoi', required: false },
  { key: 'occupation',           label: 'Nghề nghiệp',                    placeholder: 'VD: Software Engineer', required: false },
  { key: 'company_name',         label: 'Tên công ty (tiếng Anh)',         placeholder: 'VD: ABC Company Ltd',   required: false },
  { key: 'passport_number',      label: 'Số hộ chiếu',                    placeholder: 'VD: B1234567',          required: true },
  { key: 'passport_issue_date',  label: 'Ngày cấp hộ chiếu',              placeholder: 'DD/MM/YYYY',            required: false },
  { key: 'passport_expiry_date', label: 'Ngày hết hạn hộ chiếu',         placeholder: 'DD/MM/YYYY',            required: false },
  { key: 'accommodation_name',   label: 'Tên khách sạn / nơi lưu trú',   placeholder: 'VD: APA Hotel Shinjuku', required: false },
  { key: 'accommodation_address', label: 'Địa chỉ khách sạn',             placeholder: 'VD: 1-2-3 Shinjuku, Tokyo', required: false },
  { key: 'contact_in_japan',     label: 'Liên hệ tại điểm đến',           placeholder: 'Tên + SĐT',             required: false },
]

const REQUIRED_KEYS = PERSONAL_FIELDS.filter(f => f.required).map(f => f.key)

// Convert YYYY-MM-DD → DD/MM/YYYY for display (pass-through if already in other format)
function fmtDate(v) {
  if (!v) return v
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  return m ? `${m[3]}/${m[2]}/${m[1]}` : v
}

function emptyPersonal() {
  return Object.fromEntries(PERSONAL_FIELDS.map(f => [f.key, '']))
}

function SummaryRow({ label, value }) {
  if (!value) return null
  return (
    <div style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
      <span style={{ fontSize: 12, color: 'var(--color-text-muted)', minWidth: 120, flexShrink: 0 }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', wordBreak: 'break-word' }}>{value}</span>
    </div>
  )
}

// ─── Step 1 component ────────────────────────────────────────────────────────
function Step1({ onNext }) {
  const { applicationId, API_BASE, extractedInfo, setExtractedInfo } = useApp()
  const fileRef = useRef(null)
  const uploadingRef = useRef(false)

  // mode: 'choose' | 'uploading' | 'summary' | 'edit'
  const hasExisting = extractedInfo && Object.keys(extractedInfo).length > 0
  const [mode, setMode] = useState(hasExisting ? 'summary' : 'choose')
  const [fields, setFields] = useState(() => ({ ...emptyPersonal(), ...extractedInfo }))
  const [errors, setErrors] = useState({})
  const [uploadError, setUploadError] = useState('')
  const [uploading, setUploading] = useState(false)

  function setField(key, val) {
    setFields(f => ({ ...f, [key]: val }))
    setErrors(e => ({ ...e, [key]: undefined }))
  }

  function validate() {
    const errs = {}
    REQUIRED_KEYS.forEach(k => {
      if (!fields[k]?.trim()) errs[k] = 'Bắt buộc'
    })
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function handlePassportFile(file) {
    if (!file || uploadingRef.current) return
    uploadingRef.current = true
    setUploading(true)
    setUploadError('')

    try {
      // 1. OCR extraction (best-effort — failure does not block document upload)
      try {
        const ocrForm = new FormData()
        ocrForm.append('file', file)
        ocrForm.append('doc_type', 'passport')
        const ocrRes = await fetch(`${API_BASE}/api/extract-id`, { method: 'POST', body: ocrForm })
        if (ocrRes.ok) {
          const ocrData = await ocrRes.json()
          const merged = { ...emptyPersonal(), ...extractedInfo, ...Object.fromEntries(Object.entries(ocrData).filter(([, v]) => v)) }
          setFields(merged)
        } else {
          setUploadError('Không thể đọc hộ chiếu tự động — vui lòng kiểm tra và chỉnh sửa thông tin bên dưới.')
        }
      } catch {
        setUploadError('Không thể đọc hộ chiếu tự động — vui lòng kiểm tra và chỉnh sửa thông tin bên dưới.')
      }

      // 2. Document upload (critical path)
      const docForm = new FormData()
      docForm.append('file', file)
      docForm.append('doc_type', 'passport')
      const docRes = await fetch(`${API_BASE}/api/application/${applicationId}/documents`, { method: 'POST', body: docForm })
      if (!docRes.ok) throw new Error('Upload failed')
      const docData = await docRes.json()
      const docId = docData.document_id

      // 3. Trigger review
      const reviewRes = await fetch(`${API_BASE}/api/application/${applicationId}/documents/${docId}/review`, { method: 'POST' })
      if (!reviewRes.ok) throw new Error('Review failed')

      // 4. Fetch extracted info from server
      try {
        const infoRes = await fetch(`${API_BASE}/api/application/${applicationId}/extracted-info`)
        if (infoRes.ok) {
          const info = await infoRes.json()
          if (info && !info.error) {
            setExtractedInfo(info)
            setFields(f => ({ ...f, ...Object.fromEntries(Object.entries(info).filter(([, v]) => v)) }))
          }
        }
      } catch { /* non-critical */ }

      setMode('summary')
    } catch {
      setUploadError('Không thể tải hộ chiếu lên. Vui lòng thử lại hoặc điền tay bên dưới.')
      setMode('edit')
    } finally {
      setUploading(false)
      uploadingRef.current = false
    }
  }

  function handleContinue() {
    if (!validate()) return
    setExtractedInfo({ ...extractedInfo, ...fields })
    onNext(fields)
  }

  return (
    <div>
      <div style={cardStyle}>
        <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>Bước 1: Thông tin cá nhân</h2>
        <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 16, lineHeight: 1.5 }}>
          Tải hộ chiếu lên để tự động điền thông tin, hoặc điền tay.
        </p>

        {mode === 'choose' && (
          <>
            <button
              onClick={() => { fileRef.current.value = ''; fileRef.current.click() }}
              disabled={uploading}
              style={{ width: '100%', padding: '14px 0', background: 'var(--color-cta)', color: '#fff', border: 'none', borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: 'pointer', marginBottom: 12 }}
            >
              📷 Tải hộ chiếu lên
            </button>
            <button
              onClick={() => setMode('edit')}
              style={{ display: 'block', margin: '0 auto', background: 'none', border: 'none', fontSize: 14, color: 'var(--color-cta)', cursor: 'pointer', textDecoration: 'underline' }}
            >
              Điền tay →
            </button>
            <input ref={fileRef} type="file" accept="image/*,.pdf" style={{ display: 'none' }}
              onChange={e => handlePassportFile(e.target.files[0])} />
          </>
        )}

        {uploading && (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <div style={{ width: 36, height: 36, border: '3px solid var(--color-border)', borderTopColor: 'var(--color-cta)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px' }} />
            <p style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>Đang xử lý hộ chiếu...</p>
          </div>
        )}

        {uploadError && (
          <div style={{ background: '#fee2e2', border: '1px solid #f87171', borderRadius: 8, padding: '10px 12px', fontSize: 13, color: '#991b1b', marginBottom: 12 }}>
            {uploadError}
          </div>
        )}

        {mode === 'summary' && !uploading && (
          <>
            <div style={{ background: '#d1fae5', borderRadius: 8, padding: '10px 12px', marginBottom: 14, fontSize: 13, color: '#065f46', fontWeight: 600 }}>
              ✓ Đã đọc thông tin từ hộ chiếu
            </div>
            <SummaryRow label="Họ tên" value={[fields.family_name, fields.given_name].filter(Boolean).join(' ')} />
            <SummaryRow label="Ngày sinh" value={fmtDate(fields.date_of_birth)} />
            <SummaryRow label="Số hộ chiếu" value={fields.passport_number} />
            <SummaryRow label="Hết hạn" value={fmtDate(fields.passport_expiry_date)} />
            <SummaryRow label="Quốc tịch" value={fields.nationality} />
            <button
              onClick={() => setMode('edit')}
              style={{ background: 'none', border: 'none', fontSize: 13, color: 'var(--color-cta)', cursor: 'pointer', textDecoration: 'underline', marginTop: 8 }}
            >
              Chỉnh sửa →
            </button>
          </>
        )}

        {mode === 'edit' && !uploading && (
          <>
            {PERSONAL_FIELDS.map(f => (
              <div key={f.key} style={{ marginBottom: 14 }}>
                <label style={labelStyle}>
                  {f.label}
                  {f.required && <span style={{ color: '#ef4444' }}> *</span>}
                </label>
                {f.isSelect ? (
                  <select
                    value={fields[f.key] || ''}
                    onChange={e => setField(f.key, e.target.value)}
                    style={{ ...inputStyle, borderColor: errors[f.key] ? '#ef4444' : 'var(--color-border)' }}
                  >
                    {f.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                ) : (
                  <input
                    type={f.type || 'text'}
                    value={fields[f.key] || ''}
                    onChange={e => setField(f.key, e.target.value)}
                    placeholder={f.placeholder}
                    style={{ ...inputStyle, borderColor: errors[f.key] ? '#ef4444' : 'var(--color-border)' }}
                  />
                )}
                {errors[f.key] && <p style={{ fontSize: 11, color: '#ef4444', marginTop: 3 }}>{errors[f.key]}</p>}
              </div>
            ))}
          </>
        )}
      </div>

      {!uploading && mode !== 'choose' && (
        <CTAButton label="Tiếp tục →" onClick={handleContinue} />
      )}
    </div>
  )
}

// ─── Step 2 — Trip details ───────────────────────────────────────────────────
const PURPOSE_OPTIONS = [
  { value: 'tourism',       label: 'Du lịch' },
  { value: 'business',      label: 'Công tác / Kinh doanh' },
  { value: 'visit_family',  label: 'Thăm thân' },
]

function Step2({ onNext }) {
  const { tripFormData, setTripFormData } = useApp()
  const [form, setForm] = useState({
    accommodation_address: '',
    contact_person: '',
    contact_phone: '',
    visit_purpose: 'tourism',
    ...tripFormData,
  })

  function handleContinue() {
    setTripFormData(form)
    onNext(form)
  }

  function set(key, val) {
    setForm(f => ({ ...f, [key]: val }))
  }

  return (
    <div>
      <div style={cardStyle}>
        <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>Bước 2: Chi tiết chuyến đi</h2>
        <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 16, lineHeight: 1.5 }}>
          Thông tin này dùng để điền vào đơn xin visa. Tất cả đều không bắt buộc.
        </p>

        <div style={{ marginBottom: 14 }}>
          <label style={labelStyle}>Địa chỉ nơi lưu trú tại điểm đến</label>
          <input
            type="text"
            value={form.accommodation_address}
            onChange={e => set('accommodation_address', e.target.value)}
            placeholder="VD: 1-2-3 Shinjuku, Tokyo"
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: 14 }}>
          <label style={labelStyle}>Tên người liên hệ tại điểm đến</label>
          <input
            type="text"
            value={form.contact_person}
            onChange={e => set('contact_person', e.target.value)}
            placeholder="Họ tên"
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: 14 }}>
          <label style={labelStyle}>Số điện thoại người liên hệ</label>
          <input
            type="tel"
            value={form.contact_phone}
            onChange={e => set('contact_phone', e.target.value)}
            placeholder="+81-90-xxxx-xxxx"
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: 4 }}>
          <label style={labelStyle}>Mục đích chuyến đi</label>
          <select
            value={form.visit_purpose}
            onChange={e => set('visit_purpose', e.target.value)}
            style={inputStyle}
          >
            {PURPOSE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>

      <CTAButton label="Tiếp tục →" onClick={handleContinue} />
    </div>
  )
}

// ─── Step 3 — Itinerary ──────────────────────────────────────────────────────
function Step3({ onNext }) {
  const { itineraryJson } = useApp()
  const [skipped, setSkipped] = useState(false)

  if (itineraryJson) {
    return (
      <div>
        <div style={cardStyle}>
          <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>Bước 3: Lịch trình</h2>
          <div style={{ background: '#d1fae5', borderRadius: 8, padding: '10px 12px', marginBottom: 12, fontSize: 13, color: '#065f46', fontWeight: 600 }}>
            ✓ Lịch trình đã được tạo
          </div>
          <button
            onClick={() => window.__openChatWithMessage?.('Gợi ý lịch trình cho chuyến đi của tôi')}
            style={{ background: 'none', border: 'none', fontSize: 13, color: 'var(--color-cta)', cursor: 'pointer', textDecoration: 'underline' }}
          >
            Chỉnh sửa lịch trình →
          </button>
        </div>
        <CTAButton label="Tiếp tục →" onClick={onNext} />
      </div>
    )
  }

  return (
    <div>
      <div style={cardStyle}>
        <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>Bước 3: Lịch trình</h2>
        <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 16, lineHeight: 1.5 }}>
          Lịch trình giúp đại sứ quán xem xét đơn. AI có thể gợi ý theo điểm đến và thời gian của bạn.
        </p>

        <button
          onClick={() => window.__openChatWithMessage?.('Gợi ý lịch trình cho chuyến đi của tôi')}
          style={{ width: '100%', padding: '14px 0', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 10, fontSize: 15, fontWeight: 600, color: '#1d4ed8', cursor: 'pointer', marginBottom: 12 }}
        >
          Để AI tạo lịch trình
        </button>

        {skipped ? (
          <div style={{ background: '#fef3c7', border: '1px solid #fbbf24', borderRadius: 8, padding: '10px 12px', fontSize: 13, color: '#92400e', marginTop: 4 }}>
            ⚠️ Chưa có lịch trình — bạn vẫn có thể tiếp tục, nhưng hồ sơ có thể thiếu tài liệu này.
          </div>
        ) : (
          <button
            onClick={() => setSkipped(true)}
            style={{ display: 'block', margin: '0 auto', background: 'none', border: 'none', fontSize: 13, color: 'var(--color-text-muted)', cursor: 'pointer', textDecoration: 'underline' }}
          >
            Bỏ qua
          </button>
        )}
      </div>

      {skipped && (
        <CTAButton label="Tiếp tục →" onClick={onNext} />
      )}
    </div>
  )
}

// ─── Step 4 — Criminal-history declaration ───────────────────────────────────
// 6 câu Yes/No dịch từ text thật của form MOFA (static/visa_form_blank.pdf, trang 2),
// giữ nguyên thứ tự trên form. Key trùng tên field backend (PersonalInfo / RB5[0-5]).
const DECLARATION_QUESTIONS = [
  { key: 'conviction_any_crime', label: 'Bạn đã từng bị kết án về một tội nào ở bất kỳ quốc gia nào chưa?' },
  { key: 'sentenced_1yr_plus', label: 'Bạn đã từng bị kết án tù từ 1 năm trở lên ở bất kỳ quốc gia nào chưa?' },
  { key: 'deported_or_removed', label: 'Bạn đã từng bị trục xuất khỏi Nhật Bản hoặc bất kỳ quốc gia nào vì ở quá hạn visa hoặc vi phạm pháp luật chưa?' },
  { key: 'drug_offense', label: 'Bạn đã từng bị kết án về tội liên quan đến ma túy (chất gây nghiện, cần sa, thuốc phiện, chất kích thích hoặc chất hướng thần) ở bất kỳ quốc gia nào chưa?' },
  { key: 'prostitution_related', label: 'Bạn đã từng tham gia mại dâm, môi giới hoặc dụ dỗ mại dâm cho người khác, cung cấp địa điểm cho mại dâm, hoặc bất kỳ hoạt động nào liên quan trực tiếp đến mại dâm chưa?' },
  { key: 'human_trafficking', label: 'Bạn đã từng phạm tội buôn người, hoặc xúi giục, giúp sức người khác phạm tội buôn người chưa?' },
]

function Step4({ declarations, setDeclarations, onNext }) {
  const answeredAll = DECLARATION_QUESTIONS.every(q => typeof declarations[q.key] === 'boolean')

  function answer(key, value) {
    setDeclarations(d => ({ ...d, [key]: value }))
  }

  return (
    <div>
      <div style={cardStyle}>
        <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>Bước 4: Khai báo</h2>
        <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 16, lineHeight: 1.5 }}>
          Đơn xin visa yêu cầu bạn trả lời 6 câu hỏi dưới đây. Câu trả lời sẽ được điền
          đúng như bạn khai vào đơn. Vui lòng trả lời trung thực — khai sai có thể dẫn đến
          từ chối visa.
        </p>

        {DECLARATION_QUESTIONS.map((q, i) => (
          <div key={q.key} style={{ marginBottom: 18 }}>
            <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 8, lineHeight: 1.5 }}>
              {i + 1}. {q.label}
            </p>
            <div style={{ display: 'flex', gap: 8 }}>
              <div style={{ flex: 1 }}>
                <OptionButton
                  label="Có"
                  selected={declarations[q.key] === true}
                  onClick={() => answer(q.key, true)}
                />
              </div>
              <div style={{ flex: 1 }}>
                <OptionButton
                  label="Không"
                  selected={declarations[q.key] === false}
                  onClick={() => answer(q.key, false)}
                />
              </div>
            </div>
          </div>
        ))}

        <p style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
          Lưu ý: chọn "Có" nếu bạn từng nhận bản án, kể cả án đã được hưởng án treo.
        </p>
      </div>

      {!answeredAll && (
        <p style={{ fontSize: 12, color: 'var(--color-text-muted)', textAlign: 'center', marginBottom: 8 }}>
          Vui lòng trả lời đủ 6 câu hỏi để tiếp tục
        </p>
      )}
      <CTAButton label="Tiếp tục →" onClick={onNext} disabled={!answeredAll} />
    </div>
  )
}

// ─── Step 5 — Preview & Download ─────────────────────────────────────────────
function Step5({ personalFields, declarations, onFinish }) {
  const { applicationId, API_BASE, extractedInfo, tripFormData, itineraryJson } = useApp()
  const [downloading, setDownloading] = useState(false)

  async function handleDownload() {
    setDownloading(true)
    try {
      const res = await fetch(`${API_BASE}/api/application/${applicationId}/forms/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          personal_info: { ...extractedInfo, ...personalFields, ...declarations },
          trip_details: tripFormData,
          itinerary: itineraryJson,
        }),
      })
      if (!res.ok) throw new Error()
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'visa-forms.zip'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 100)
    } catch {
      alert('Không thể tạo đơn. Vui lòng thử lại.')
    } finally {
      setDownloading(false)
    }
  }

  const purposeLabel = PURPOSE_OPTIONS.find(o => o.value === tripFormData?.visit_purpose)?.label || tripFormData?.visit_purpose

  return (
    <div>
      <div style={cardStyle}>
        <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: 12 }}>Bước 5: Xem lại & Tải xuống</h2>

        {/* Personal info summary */}
        <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid var(--color-border)' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>Thông tin cá nhân</p>
          <SummaryRow label="Họ tên" value={[personalFields.family_name, personalFields.given_name].filter(Boolean).join(' ')} />
          <SummaryRow label="Ngày sinh" value={personalFields.date_of_birth} />
          <SummaryRow label="Số hộ chiếu" value={personalFields.passport_number} />
          <SummaryRow label="Hết hạn" value={personalFields.passport_expiry_date} />
          <SummaryRow label="Quốc tịch" value={personalFields.nationality} />
        </div>

        {/* Trip details summary */}
        <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid var(--color-border)' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>Chi tiết chuyến đi</p>
          <SummaryRow label="Mục đích" value={purposeLabel} />
          <SummaryRow label="Nơi lưu trú" value={tripFormData?.accommodation_address} />
          <SummaryRow label="Liên hệ" value={[tripFormData?.contact_person, tripFormData?.contact_phone].filter(Boolean).join(' — ')} />
        </div>

        {/* Itinerary */}
        <div>
          <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>Lịch trình</p>
          {itineraryJson
            ? <p style={{ fontSize: 13, color: '#065f46', fontWeight: 600 }}>✓ Đã tạo lịch trình</p>
            : <p style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>Chưa có lịch trình</p>
          }
        </div>
      </div>

      <button
        onClick={handleDownload}
        disabled={downloading}
        style={{
          width: '100%', padding: '14px 0',
          background: downloading ? 'var(--color-border)' : '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: 10, fontSize: 15, fontWeight: 600,
          color: downloading ? 'var(--color-text-muted)' : '#1d4ed8',
          cursor: downloading ? 'not-allowed' : 'pointer',
          marginBottom: 12,
        }}
      >
        {downloading ? 'Đang tạo đơn...' : '⬇ Tải đơn xin visa (ZIP)'}
      </button>

      <CTAButton label="Tiếp tục →" onClick={onFinish} />
    </div>
  )
}

// ─── Main FormFillingScreen ───────────────────────────────────────────────────
export default function FormFillingScreen() {
  const { navigate } = useApp()
  const [step, setStep] = useState(1)
  const [personalFields, setPersonalFields] = useState({})
  const [declarations, setDeclarations] = useState({})

  const STEP_LABELS = ['Cá nhân', 'Chuyến đi', 'Lịch trình', 'Khai báo', 'Tải xuống']

  function handleBack() {
    if (step === 1) navigate('price')
    else setStep(s => s - 1)
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--color-background)' }}>
      <NavHeader title="Điền đơn visa" showBack onBack={handleBack} />
      <ProgressBar current={9} total={11} />

      {/* Step indicator */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: '12px 20px 0' }}>
        {STEP_LABELS.map((label, i) => {
          const n = i + 1
          const active = n === step
          const done = n < step
          return (
            <div key={n} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
              <div style={{
                width: 28, height: 28,
                borderRadius: '50%',
                background: done ? '#10b981' : active ? 'var(--color-cta)' : 'var(--color-border)',
                color: done || active ? '#fff' : 'var(--color-text-muted)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, fontWeight: 700,
                marginBottom: 4,
              }}>
                {done ? '✓' : n}
              </div>
              <span style={{ fontSize: 10, color: active ? 'var(--color-cta)' : 'var(--color-text-muted)', fontWeight: active ? 700 : 400, textAlign: 'center' }}>
                {label}
              </span>
            </div>
          )
        })}
      </div>

      <div style={{ flex: 1, padding: '16px 20px', paddingBottom: 32 }}>
        {step === 1 && (
          <Step1 onNext={(fields) => { setPersonalFields(fields); setStep(2) }} />
        )}
        {step === 2 && (
          <Step2 onNext={() => setStep(3)} />
        )}
        {step === 3 && (
          <Step3 onNext={() => setStep(4)} />
        )}
        {step === 4 && (
          <Step4 declarations={declarations} setDeclarations={setDeclarations} onNext={() => setStep(5)} />
        )}
        {step === 5 && (
          <Step5 personalFields={personalFields} declarations={declarations} onFinish={() => navigate('checklist')} />
        )}
      </div>
    </div>
  )
}
