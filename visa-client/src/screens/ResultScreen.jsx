import NavHeader from '../components/NavHeader'
import { useApp } from '../context/AppContext'

const COPY = {
  approved: {
    icon: '🎉',
    headline: 'Visa đã được cấp!',
    sub: 'Chúc mừng! Hồ sơ của bạn đã được Đại sứ quán chấp thuận.',
    color: '#065f46',
    bg: '#d1fae5',
    border: '#34d399',
    details: 'Visa của bạn đã sẵn sàng. Chúng tôi sẽ liên hệ để hướng dẫn bước tiếp theo.',
  },
  rejected: {
    icon: '❌',
    headline: 'Hồ sơ chưa được chấp thuận',
    sub: 'Đại sứ quán đã từ chối đơn xin visa lần này.',
    color: '#991b1b',
    bg: '#fee2e2',
    border: '#f87171',
    details: 'Chúng tôi sẽ phân tích lý do từ chối và tư vấn cho bạn hướng cải thiện. Đội tư vấn sẽ liên hệ trong 24 giờ.',
  },
  quota_rejected: {
    icon: '📋',
    headline: 'Hết quota xét duyệt kỳ này',
    sub: 'Đại sứ quán đã xử lý đủ số lượng hồ sơ trong kỳ xét duyệt này.',
    color: '#92400e',
    bg: '#fef3c7',
    border: '#fbbf24',
    details: 'Đây không phải lỗi hồ sơ của bạn. Hồ sơ sẽ được tự động chuyển sang kỳ xét duyệt tiếp theo mà không cần nộp lại.',
  },
}

export default function ResultScreen() {
  const { resultStatus, navigate, setResultStatus } = useApp()
  const status = resultStatus || 'approved'
  const copy = COPY[status] || COPY.approved

  function restart() {
    localStorage.removeItem('visa_application_id')
    localStorage.removeItem('visa_session_id')
    setResultStatus(null)
    navigate('landing')
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--color-background)' }}>
      <NavHeader title="Kết quả" showBack={false} />

      <div style={{ flex: 1, padding: '32px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{
          background: copy.bg,
          border: `2px solid ${copy.border}`,
          borderRadius: 'var(--radius-card)',
          padding: '32px 24px',
          textAlign: 'center',
          width: '100%',
          maxWidth: 380,
        }}>
          <div style={{ fontSize: 56, marginBottom: 16 }}>{copy.icon}</div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: copy.color, marginBottom: 10, lineHeight: 1.3 }}>
            {copy.headline}
          </h1>
          <p style={{ fontSize: 14, color: copy.color, opacity: 0.85, marginBottom: 16, lineHeight: 1.6 }}>
            {copy.sub}
          </p>
          <div style={{ borderTop: `1px solid ${copy.border}`, paddingTop: 16 }}>
            <p style={{ fontSize: 13, color: copy.color, opacity: 0.75, lineHeight: 1.6 }}>
              {copy.details}
            </p>
          </div>
        </div>

        <div style={{ marginTop: 24, background: 'var(--color-surface)', borderRadius: 12, padding: 16, width: '100%', maxWidth: 380, textAlign: 'center' }}>
          <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 10 }}>
            Cần hỗ trợ thêm?
          </p>
          <a
            href="mailto:support@visaflow.vn"
            style={{ fontSize: 14, color: 'var(--color-cta)', fontWeight: 600, textDecoration: 'none' }}
          >
            Liên hệ đội tư vấn →
          </a>
        </div>

        <button
          onClick={restart}
          style={{ marginTop: 16, background: 'none', border: 'none', fontSize: 13, color: 'var(--color-text-muted)', cursor: 'pointer', textDecoration: 'underline', padding: 8 }}
        >
          Bắt đầu hồ sơ mới
        </button>
      </div>
    </div>
  )
}
