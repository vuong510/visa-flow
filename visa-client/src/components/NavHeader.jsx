import { useState } from 'react'
import BottomSheet from './BottomSheet'

export default function NavHeader({ title, onBack, showBack = true, rightAction }) {
  const [showAI, setShowAI] = useState(false)

  return (
    <>
      <header style={{
        height: 56,
        background: 'var(--color-primary)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        position: 'sticky',
        top: 0,
        zIndex: 10,
        flexShrink: 0,
      }}>
        <div style={{ width: 44, display: 'flex', alignItems: 'center' }}>
          {showBack && onBack && (
            <button
              onClick={onBack}
              aria-label="Quay lại"
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: '#fff', fontSize: 20, width: 44, height: 44,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              ‹
            </button>
          )}
        </div>

        <span style={{
          flex: 1, textAlign: 'center', color: '#fff',
          fontSize: 17, fontWeight: 600, lineHeight: 1.4,
        }}>
          {title || 'Visa Flow'}
        </span>

        {rightAction ? (
          <div style={{ width: 44, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {rightAction}
          </div>
        ) : (
          <button
            onClick={() => setShowAI(true)}
            aria-label="Thông tin AI"
            style={{
              background: 'var(--color-cta)', border: 'none', cursor: 'pointer',
              color: '#fff', borderRadius: 'var(--radius-chip)',
              padding: '3px 10px', fontSize: 12, fontWeight: 500,
              minWidth: 44, minHeight: 44,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            AI
          </button>
        )}
      </header>

      <BottomSheet open={showAI} onClose={() => setShowAI(false)} title="Về dịch vụ AI">
        <p style={{ fontSize: 15, lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
          Dịch vụ này sử dụng AI để đánh giá hồ sơ của bạn. Kết quả là tham khảo và không đảm bảo được cấp visa.
        </p>
      </BottomSheet>
    </>
  )
}
