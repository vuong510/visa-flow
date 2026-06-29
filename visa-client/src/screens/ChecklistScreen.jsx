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
          {allPass ? '✅ Hồ sơ sẵn sàng nộp!' : `Đã tải lên ${uploaded}/${total} tài liệu`}
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
  const { applicationId, API_BASE, navigate, destination, checklist: ctxChecklist, setChecklist: setCtxChecklist } = useApp()
  const [downloading, setDownloading] = useState(false)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [docs, setDocs] = useState({})
  const [detailItem, setDetailItem] = useState(null)
  const [activeUploadId, setActiveUploadId] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [confidenceNote, setConfidenceNote] = useState(null)
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
      setDocs(d => ({ ...d, [docId]: { ...d[docId], reviewing: false, status: 'needs_clarification', notes: 'Không thể tự động kiểm tra. Nhân viên sẽ xem xét tài liệu này.' } }))
    }
  }

  const uploadedItems = items.filter(item => docs[item.id]?.id && !docs[item.id]?.uploading)
  const uploadedCount = uploadedItems.length
  const allPass = uploadedCount === items.length && items.length > 0 && items.every(item => docs[item.id]?.status === 'pass')

  async function handleDownloadForms() {
    setDownloading(true)
    try {
      const res = await fetch(`${API_BASE}/api/application/${applicationId}/forms/download`)
      if (!res.ok) throw new Error()
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'visa-forms.zip'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('Không thể tải form. Vui lòng thử lại.')
    } finally {
      setDownloading(false)
    }
  }

  async function handleSubmit() {
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
      <NavHeader title="Tài liệu cần chuẩn bị" showBack={false} />
      <ProgressBar current={9} total={10} />

      {!loading && items.length > 0 && (
        <ReadinessBanner uploaded={uploadedCount} total={items.length} allPass={allPass} />
      )}

      <div style={{ flex: 1, paddingBottom: allPass ? 100 : 24 }}>
        {loading && <SkeletonList />}

        {error && (
          <div style={{ padding: '24px 20px', textAlign: 'center' }}>
            <p style={{ color: '#991b1b', marginBottom: 16 }}>{error}</p>
            <CTAButton label="Thử lại" onClick={() => { setError(''); setLoading(true); loadChecklist() }} />
          </div>
        )}

        {!loading && !error && destination === 'japan' && (
          <div style={{ padding: '16px 20px 0' }}>
            <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 12, padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <div>
                <p style={{ fontWeight: 600, fontSize: 14, color: '#1e40af', marginBottom: 2 }}>Đơn xin visa + Lịch trình</p>
                <p style={{ fontSize: 12, color: '#3b82f6' }}>Tải form MOFA đã điền sẵn thông tin</p>
              </div>
              <button
                onClick={handleDownloadForms}
                disabled={downloading}
                style={{ background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 600, cursor: downloading ? 'not-allowed' : 'pointer', opacity: downloading ? 0.6 : 1, whiteSpace: 'nowrap' }}
              >
                {downloading ? 'Đang tải...' : '⬇ Tải xuống'}
              </button>
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
            {items.map(item => (
              <DocumentItem
                key={item.id}
                item={item}
                docState={docs[item.id]}
                onUpload={triggerUpload}
                onDetail={setDetailItem}
              />
            ))}
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,.pdf,.doc,.docx"
        style={{ display: 'none' }}
        onChange={handleFileSelected}
      />

      {allPass && (
        <BottomActionArea>
          <CTAButton
            label={submitting ? 'Đang nộp...' : 'Nộp hồ sơ'}
            onClick={handleSubmit}
            disabled={submitting}
          />
        </BottomActionArea>
      )}

      {detailItem && (
        <BottomSheet open={true} title={detailItem.name} onClose={() => setDetailItem(null)}>
          <div style={{ padding: '0 0 8px' }}>
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
