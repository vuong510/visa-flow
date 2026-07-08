import { useState, useEffect } from 'react'
import NavHeader from '../components/NavHeader'
import CTAButton from '../components/CTAButton'
import BottomActionArea from '../components/BottomActionArea'
import { useApp } from '../context/AppContext'

export default function LandingScreen() {
  const { startApplication, navigate, API_BASE } = useApp()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_BASE}/api/health`).catch(() => {})
  }, [])

  async function handleStart() {
    setLoading(true)
    setError('')
    try {
      await startApplication()
      navigate('destination')
    } catch {
      setError('Không thể kết nối. Vui lòng thử lại.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--color-background)' }}>
      <NavHeader title="Visa Flow" showBack={false} />

      <div style={{ flex: 1, padding: '24px 20px 120px' }}>
        {/* Hero */}
        <div style={{
          background: 'linear-gradient(180deg, #1A2E4A 0%, #223A5E 100%)',
          borderRadius: 'var(--radius-card)',
          padding: '32px 24px',
          marginBottom: 'var(--section-gap)',
          color: '#fff',
        }}>
          <p style={{ fontSize: 13, fontWeight: 500, opacity: 0.7, marginBottom: 8, letterSpacing: 0.5 }}>
            DỊCH VỤ XIN VISA AI
          </p>
          <h1 style={{ fontSize: 24, fontWeight: 700, lineHeight: 1.3, marginBottom: 12 }}>
            Biết kết quả trước khi thanh toán
          </h1>
          <p style={{ fontSize: 15, lineHeight: 1.6, opacity: 0.85 }}>
            AI đánh giá hồ sơ của bạn miễn phí trước khi thanh toán. Nếu hồ sơ không đủ điều kiện, bạn không mất đồng nào.
          </p>
        </div>

        {/* Value props */}
        <div style={{
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-card)',
          padding: 'var(--card-inner)',
          boxShadow: 'var(--shadow-card)',
          display: 'flex', flexDirection: 'column', gap: 16,
        }}>
          <ValueRow icon="💰" title="Rẻ hơn đại lý" desc="Không có chi phí nhân sự, bạn giữ lại phần chênh lệch đó" />
          <div style={{ height: 1, background: 'var(--color-border)' }} />
          <ValueRow icon="🕐" title="Sẵn sàng 24/7" desc="Không chờ giờ hành chính. Nộp hồ sơ lúc nửa đêm cũng được" />
          <div style={{ height: 1, background: 'var(--color-border)' }} />
          <ValueRow icon="🤖" title="AI minh bạch" desc="Mọi quyết định đều được giải thích rõ ràng, không hộp đen" />
        </div>

        {/* AI disclosure */}
        <p style={{
          marginTop: 16, fontSize: 13, color: 'var(--color-text-muted)',
          lineHeight: 1.5, textAlign: 'center',
        }}>
          Dịch vụ sử dụng AI. Kết quả là tham khảo, không đảm bảo được cấp visa.
        </p>
      </div>

      <BottomActionArea>
        {error && (
          <p style={{ textAlign: 'center', fontSize: 13, color: '#b91c1c', marginBottom: 10 }}>{error}</p>
        )}
        <CTAButton label="Bắt đầu →" onClick={handleStart} loading={loading} />
      </BottomActionArea>
    </div>
  )
}

function ValueRow({ icon, title, desc }) {
  return (
    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
      <span style={{ fontSize: 22, lineHeight: 1 }}>{icon}</span>
      <div>
        <p style={{ fontWeight: 600, fontSize: 15, marginBottom: 2 }}>{title}</p>
        <p style={{ fontSize: 14, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>{desc}</p>
      </div>
    </div>
  )
}
