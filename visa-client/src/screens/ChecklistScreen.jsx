import { useEffect, useState, useRef } from 'react'
import NavHeader from '../components/NavHeader'
import ProgressBar from '../components/ProgressBar'
import BottomActionArea from '../components/BottomActionArea'
import CTAButton from '../components/CTAButton'
import BottomSheet from '../components/BottomSheet'
import DocumentItem from '../components/DocumentItem'
import { useApp } from '../context/AppContext'

function SkeletonList() {
  return (
    <div style={{ padding: '0 20px' }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} style={{ paddingTop: 14, paddingBottom: 14, borderBottom: '1px solid var(--color-border)' }}>
          <div className="skeleton" style={{ width: '60%', height: 14, marginBottom: 6 }} />
          <div className="skeleton" style={{ width: '80%', height: 12 }} />
        </div>
      ))}
    </div>
  )
}

function ReadinessBanner({ uploaded, total, allPass }) {
  const pct = total > 0 ? Math.round((uploaded / total) * 100) : 0
  const color = allPass ? '#065f46' : pct > 0 ? '#1d4ed8' : 'var(--color-text-muted)'
  const bg = allPass ? '#d1fae5' : pct > 0 ? '#eff6ff' : '#f9fafb'

  return (
    <div style={{ background: bg, padding: '12px 20px', borderBottom: '1px solid var(--color-border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color }}>
          {allPass ? '✅ Đủ tài liệu — sẵn sàng gửi' : `AI đã kiểm tra ${uploaded}/${total} tài liệu`}
        </span>
        <span style={{ fontSize: 12, color, fontWeight: 600 }}>{pct}%</span>
      </div>
      <div style={{ height: 4, background: allPass ? '#34d399' : '#e5e7eb', borderRadius: 2 }}>
        <div style={{ height: '100%', width: `${pct}%`, background: allPass ? '#10b981' : 'var(--color-cta)', borderRadius: 2, transition: 'width 0.3s ease' }} />
      </div>
    </div>
  )
}

export default function ChecklistScreen() {
  const { applicationId, API_BASE, navigate, checklist: ctxChecklist, setChecklist: setCtxChecklist, itineraryJson } = useApp()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [docs, setDocs] = useState({})
  const [detailItem, setDetailItem] = useState(null)
  const [activeUploadId, setActiveUploadId] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [confidenceNote, setConfidenceNote] = useState(null)
  const [skipped, setSkipped] = useState({})
  const fileInputRef = useRef(null)

  useEffect(() => {
    loadChecklist()
    loadExistingDocs()
  }, [])

  async function loadChecklist() {
    if (ctxChecklist && ctxChecklist.length > 0) {
      setItems(ctxChecklist)
      setLoading(false)
      return
    }
    try {
      const res = await fetch(`${API_BASE}/api/application/${applicationId}/checklist`, { method: 'POST' })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setItems(data.items || [])
      setConfidenceNote(data.confidence_note || null)
      setCtxChecklist(data.items || [])
    } catch {
      setError('Không thể tạo danh sách tài liệu. Vui lòng thử lại.')
    } finally {
      setLoading(false)
    }
  }

  async function loadExistingDocs() {
    try {
      const res = await fetch(`${API_BASE}/api/application/${applicationId}/documents`)
      if (!res.ok) return
      const data = await res.json()
      const docsMap = {}
      for (const d of data) {
        docsMap[d.doc_type] = { id: d.id, status: d.review_status, notes: d.review_notes }
      }
      setDocs(docsMap)
    } catch (_) {}
  }

  function triggerUpload(docId) {
    setActiveUploadId(docId)
    fileInputRef.current.value = ''
    fileInputRef.current.click()
  }

  async function handleFileSelected(e) {
    const file = e.target.files[0]
    if (!file || !activeUploadId) return

    const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'application/pdf']
    if (!allowed.includes(file.type)) {
      setDocs(d => ({ ...d, [activeUploadId]: { error: true, status: 'fail', notes: 'Chỉ chấp nhận ảnh (JPG, PNG) hoặc PDF. Vui lòng chọn lại tệp.' } }))
      setActiveUploadId(null)
      return
    }

    const docId = activeUploadId
    setActiveUploadId(null)

    setDocs(d => ({ ...d, [docId]: { uploading: true } }))

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('doc_type', docId)
      const res = await fetch(`${API_BASE}/api/application/${applicationId}/documents`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error('Upload failed')
      const data = await res.json()
      setDocs(d => ({ ...d, [docId]: { id: data.document_id, status: 'pending', reviewing: true } }))
      reviewDoc(docId, data.document_id)
    } catch {
      setDocs(d => ({ ...d, [docId]: { error: true, status: 'fail', notes: 'Tải lên thất bại. Vui lòng thử lại.' } }))
    }
  }

  async function reviewDoc(docId, documentId) {
    try {
      const res = await fetch(
        `${API_BASE}/api/application/${applicationId}/documents/${documentId}/review`,
        { method: 'POST' }
      )
      if (!res.ok) throw new Error()
      const data = await res.json()
      setDocs(d => ({ ...d, [docId]: { id: documentId, status: data.status, notes: data.reason, reviewing: false } }))
    } catch {
      setDocs(d => ({ ...d, [docId]: { ...d[docId], reviewing: false, status: 'needs_clarification', notes: 'Không thể tự động kiểm tra. Đội tư vấn sẽ xem xét tài liệu này.' } }))
    }
  }

  const nonItineraryItems = items.filter(item => item.id !== 'itinerary')
  const uploadedItems = nonItineraryItems.filter(item => docs[item.id]?.id && !docs[item.id]?.uploading)
  const uploadedCount = uploadedItems.length
  const skippedCount = nonItineraryItems.filter(item => skipped[item.id] && !docs[item.id]?.id).length
  const totalCount = nonItineraryItems.length
  const allPass = uploadedCount === totalCount && totalCount > 0 &&
    nonItineraryItems.every(item => docs[item.id]?.status === 'pass')
  const hasClarification = nonItineraryItems.some(item => docs[item.id]?.status === 'needs_clarification')
  const canSubmit = (uploadedCount + skippedCount) === totalCount && totalCount > 0 &&
    nonItineraryItems.every(item =>
      skipped[item.id] && !docs[item.id]?.id ||
      docs[item.id]?.status === 'pass' ||
      docs[item.id]?.status === 'needs_clarification'
    )

  async function handleSubmit() {
    const skippedRequired = nonItineraryItems.some(item => !item.optional && skipped[item.id] && !docs[item.id]?.id)
    if (skippedRequired) {
      const ok = window.confirm('Bạn chưa tải lên một số tài liệu bắt buộc. Vẫn gửi hồ sơ?')
      if (!ok) return
    }
    setSubmitting(true)
    try {
      await fetch(`${API_BASE}/api/application/${applicationId}/submit`, { method: 'POST' })
      navigate('status-timeline')
    } catch {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--color-background)' }}>
      <NavHeader title="Chuẩn bị hồ sơ" showBack={false} />
      <ProgressBar current={10} total={11} />

      {!loading && items.length > 0 && (
        <ReadinessBanner uploaded={uploadedCount + skippedCount} total={totalCount} allPass={allPass} />
      )}

      <div style={{ flex: 1, paddingBottom: canSubmit ? 'calc(100px + env(safe-area-inset-bottom))' : 24 }}>
        {loading && <SkeletonList />}

        {error && (
          <div style={{ padding: '24px 20px', textAlign: 'center' }}>
            <p style={{ color: '#991b1b', marginBottom: 16 }}>{error}</p>
            <CTAButton label="Thử lại" onClick={() => { setError(''); setLoading(true); loadChecklist() }} />
          </div>
        )}

        {!loading && !error && items.length > 0 && (
          <div style={{ padding: '12px 20px 0' }}>
            <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 10, padding: '10px 14px', fontSize: 13, color: '#0c4a6e', lineHeight: 1.55 }}>
              AI sẽ kiểm tra từng tài liệu và cảnh báo nếu có vấn đề — giúp bạn hoàn thiện hồ sơ giấy đúng chuẩn trước khi nộp đại sứ quán.
            </div>
          </div>
        )}

        {!loading && !error && items.length > 0 && (
          <div style={{ padding: '0 20px' }}>
            {confidenceNote && (
              <div style={{ background: '#fef3c7', border: '1px solid #fbbf24', borderRadius: 10, padding: '10px 14px', margin: '16px 0', fontSize: 13, color: '#92400e', lineHeight: 1.5 }}>
                ⚠️ {confidenceNote}
              </div>
            )}
            {hasClarification && (
              <div style={{ background: '#f0f9ff', border: '1px solid #7dd3fc', borderRadius: 10, padding: '10px 14px', margin: '8px 0 0', fontSize: 13, color: '#0c4a6e', lineHeight: 1.5 }}>
                Một số tài liệu cần xem xét thêm. Bạn có thể nộp hồ sơ — đội tư vấn sẽ hỗ trợ kiểm tra trực tiếp.
              </div>
            )}
            {items.map(item => {
              if (item.id === 'itinerary') {
                return (
                  <div key="itinerary" style={{ borderBottom: '1px solid var(--color-border)', padding: '14px 0', display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 14, fontWeight: 600, marginBottom: 2 }}>Lịch trình chuyến đi</p>
                      <p style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
                        {itineraryJson
                          ? 'Đã tạo — sẽ tự điền vào form tải xuống'
                          : 'AI sẽ tự tạo khi bạn tải form visa. Hoặc hỏi AI chat để tùy chỉnh trước.'}
                      </p>
                    </div>
                    {itineraryJson
                      ? <span style={{ fontSize: 18, flexShrink: 0 }}>✓</span>
                      : <span style={{ fontSize: 12, color: '#6b7280', background: '#f3f4f6', padding: '4px 8px', borderRadius: 6, flexShrink: 0, whiteSpace: 'nowrap' }}>Tự động tạo</span>
                    }
                  </div>
                )
              }

              const docState = docs[item.id]
              const isUploaded = !!(docState?.id && !docState?.uploading)
              const isSkipped = !!skipped[item.id] && !isUploaded

              if (isSkipped) {
                return (
                  <div key={item.id} style={{ borderBottom: '1px solid var(--color-border)', padding: '12px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 14, fontWeight: 600, color: '#9ca3af', marginBottom: 1 }}>{item.name}</p>
                      {item.optional && <span style={{ fontSize: 11, color: '#d1d5db' }}>Không bắt buộc</span>}
                    </div>
                    <span style={{ fontSize: 12, color: '#9ca3af', flexShrink: 0 }}>Bỏ qua</span>
                    <button
                      onClick={() => triggerUpload(item.id)}
                      style={{ flexShrink: 0, padding: '5px 10px', border: '1.5px solid var(--color-cta)', borderRadius: 6, background: 'transparent', color: 'var(--color-cta)', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}
                    >
                      Tải lên
                    </button>
                    <button
                      onClick={() => setSkipped(s => ({ ...s, [item.id]: false }))}
                      style={{ flexShrink: 0, padding: '5px 8px', border: '1px solid #d1d5db', borderRadius: 6, background: 'transparent', fontSize: 12, color: '#6b7280', cursor: 'pointer' }}
                    >
                      Hoàn tác
                    </button>
                  </div>
                )
              }

              return (
                <div key={item.id}>
                  {item.optional && (
                    <div style={{ paddingTop: 10, paddingBottom: 2 }}>
                      <span style={{ fontSize: 11, color: '#6b7280', fontWeight: 500, background: '#f3f4f6', padding: '2px 7px', borderRadius: 4 }}>Không bắt buộc</span>
                    </div>
                  )}
                  <DocumentItem
                    item={item}
                    docState={docState}
                    onUpload={triggerUpload}
                    onDetail={setDetailItem}
                  />
                  {!isUploaded && item.id !== 'passport' && (
                    <button
                      onClick={() => setSkipped(s => ({ ...s, [item.id]: true }))}
                      style={{ display: 'block', width: '100%', textAlign: 'center', padding: '5px', background: 'none', border: 'none', fontSize: 12, color: '#9ca3af', cursor: 'pointer', marginBottom: 2 }}
                    >
                      Tôi chưa có tài liệu này
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,application/pdf"
        style={{ display: 'none' }}
        onChange={handleFileSelected}
      />

      {canSubmit && (
        <BottomActionArea>
          <CTAButton
            label={submitting ? 'Đang gửi...' : 'Gửi hồ sơ cho tư vấn viên'}
            onClick={handleSubmit}
            disabled={submitting}
          />
        </BottomActionArea>
      )}

      {detailItem && (
        <BottomSheet open={true} title={detailItem.name} onClose={() => setDetailItem(null)}>
          <div style={{ padding: '0 0 8px' }}>
            {detailItem.how_to_get && (
              <div style={{ marginBottom: 16, background: '#f0f9ff', borderRadius: 10, padding: '12px 14px' }}>
                <p style={{ fontSize: 12, fontWeight: 600, color: '#0369a1', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>Cách lấy</p>
                <p style={{ fontSize: 14, lineHeight: 1.65, color: '#0c4a6e' }}>{detailItem.how_to_get}</p>
              </div>
            )}
            <div style={{ marginBottom: 14 }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>Yêu cầu</p>
              <p style={{ fontSize: 14, lineHeight: 1.6 }}>{detailItem.description}</p>
            </div>
            <div style={{ marginBottom: 14 }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>Định dạng</p>
              <p style={{ fontSize: 14, lineHeight: 1.6 }}>{detailItem.format}</p>
            </div>
            <div style={{ marginBottom: 20 }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>Tại sao cần?</p>
              <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>{detailItem.why}</p>
            </div>
            <CTAButton
              label="Tải lên tài liệu này"
              onClick={() => { setDetailItem(null); triggerUpload(detailItem.id) }}
            />
          </div>
        </BottomSheet>
      )}
    </div>
  )
}
