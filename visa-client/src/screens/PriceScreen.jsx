import { useState } from 'react'
import NavHeader from '../components/NavHeader'
import ProgressBar from '../components/ProgressBar'
import BottomActionArea from '../components/BottomActionArea'
import CTAButton from '../components/CTAButton'
import { useApp } from '../context/AppContext'

const PRICE_ITEMS = [
  { label: 'Phí dịch vụ tư vấn', amount: '990.000 ₫' },
  { label: 'Phí nộp hồ sơ (Đại sứ quán)', amount: '550.000 ₫' },
]
const TOTAL = '1.540.000 ₫'

export default function PriceScreen() {
  const { applicationId, API_BASE, navigate } = useApp()
  const [paying, setPaying] = useState(false)
  const [overlay, setOverlay] = useState(null) // null | 'loading' | 'success' | 'error'

  async function handlePay() {
    setOverlay('loading')
    setPaying(true)
    try {
      const res = await fetch(`${API_BASE}/api/application/${applicationId}/payment/demo`, { method: 'POST' })
      if (!res.ok) throw new Error()
    } catch {
      setOverlay('error')
      setPaying(false)
      return
    }
    setTimeout(() => {
      setOverlay('success')
      setTimeout(() => navigate('form-filling'), 1000)
    }, 1500)
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--color-background)', position: 'relative' }}>
      <NavHeader title="Chi phí dịch vụ" showBack={!paying} onBack={() => navigate('eligibility-loading')} />
      <ProgressBar current={8} total={11} />

      <div style={{ flex: 1, padding: '24px 20px', paddingBottom: 100 }}>
        <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-card)', padding: 20, boxShadow: 'var(--shadow-card)', marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Tóm tắt chi phí</h2>
          {PRICE_ITEMS.map((item) => (
            <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 12, marginBottom: 12, borderBottom: '1px solid var(--color-border)' }}>
              <span style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>{item.label}</span>
              <span style={{ fontSize: 14, fontWeight: 600 }}>{item.amount}</span>
            </div>
          ))}
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: 4 }}>
            <span style={{ fontSize: 15, fontWeight: 700 }}>Tổng cộng</span>
            <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-cta)' }}>{TOTAL}</span>
          </div>
        </div>

        <div style={{ background: 'var(--color-surface)', borderRadius: 12, padding: 16, fontSize: 13, color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
          <p style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 6 }}>Bao gồm trong gói dịch vụ:</p>
          <ul style={{ paddingLeft: 16, margin: 0 }}>
            <li>Tư vấn hồ sơ từ chuyên viên visa</li>
            <li>AI kiểm tra tài liệu và cảnh báo sớm trước khi nộp đại sứ quán</li>
            <li>Theo dõi tiến trình hồ sơ trực tiếp</li>
            <li>Hỗ trợ 1-1 qua chat/gọi điện</li>
          </ul>
        </div>

        <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 12, lineHeight: 1.5, textAlign: 'center' }}>
          * Đây là bản demo. Không có giao dịch thực nào được thực hiện.
        </p>
      </div>

      <BottomActionArea>
        <CTAButton label="Thanh toán (Demo)" onClick={handlePay} disabled={paying} />
      </BottomActionArea>

      {overlay && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(255,255,255,0.92)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
        }}>
          {overlay === 'loading' && (
            <>
              <div style={{
                width: 48,
                height: 48,
                border: '4px solid var(--color-border)',
                borderTopColor: 'var(--color-cta)',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
                marginBottom: 16,
              }} />
              <p style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>Đang xử lý thanh toán...</p>
            </>
          )}
          {overlay === 'success' && (
            <>
              <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
              <p style={{ fontSize: 16, fontWeight: 700, color: '#065f46' }}>Thanh toán thành công!</p>
            </>
          )}
          {overlay === 'error' && (
            <>
              <div style={{ fontSize: 48, marginBottom: 12 }}>⚠️</div>
              <p style={{ fontSize: 15, fontWeight: 600, color: '#92400e', marginBottom: 16 }}>Lỗi xử lý thanh toán</p>
              <button
                onClick={() => setOverlay(null)}
                style={{ background: '#2563eb', color: '#fff', border: 'none', borderRadius: 10, padding: '10px 24px', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}
              >
                Thử lại
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
